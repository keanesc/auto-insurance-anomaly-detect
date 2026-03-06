"""
predictor.py
-----------
FraudPredictor singleton — loads all pre-trained model artefacts once at
application startup and exposes a predict() method for new claims.

Inference pipeline (per new claim / batch)
------------------------------------------
1.  Convert ClaimInput(s)  → raw pd.DataFrame  (via data_loader helpers)
2.  build_features()       → 48-col numeric feature vectors
3.  StandardScaler.transform()
4.  Isolation Forest:  score_samples()  + rank-normalise vs reference raw scores
5.  Autoencoder:       per-row MSE      + rank-normalise vs reference raw errors
6.  LOF:               refit LocalOutlierFactor on (X_full_ref ‖ X_new),
                       take last-n rows' inverted scores,
                       rank-normalise vs reference LOF raw scores
7.  Ensemble  = mean(iso_norm, lof_norm, ae_norm)
8.  CalibratedRandomForest.predict_proba(class=1)  → fraud_risk_score
9.  Apply risk-tier thresholds
"""

from __future__ import annotations

import pathlib
import sys
from typing import Optional

import joblib
import numpy as np
import pandas as pd
import torch
from scipy.stats import percentileofscore
from sklearn.neighbors import LocalOutlierFactor

# ---------------------------------------------------------------------------
# Ensure src/ is importable regardless of working directory
# ---------------------------------------------------------------------------
_SRC_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from anomaly_detection import AE_HIDDEN_DIMS, _Autoencoder  # noqa: E402
from data_loader import _clean_main, _parse_dates, load_all  # noqa: E402
from feature_engineering import build_features  # noqa: E402

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MODELS_DIR = _ROOT / "outputs" / "models"
OUTPUTS_DIR = _ROOT / "outputs"
SCORES_CACHE_PATH = OUTPUTS_DIR / "fraud_risk_scores.csv"

# Risk-tier thresholds (must match score_all.py)
_TIER_HIGH = 0.88
_TIER_MEDIUM = 0.70
_TIER_LOW = 0.50


def _assign_tier(score: float) -> str:
    if score >= _TIER_HIGH:
        return "HIGH"
    if score >= _TIER_MEDIUM:
        return "MEDIUM"
    if score >= _TIER_LOW:
        return "LOW"
    return "VERY_LOW"


class FraudPredictor:
    """
    Loads model artefacts once and provides fast inference on new policy claims.
    Instantiate once at application lifespan startup.
    """

    def __init__(self, verbose: bool = True) -> None:
        self._verbose = verbose
        self._log("Loading model artefacts …")

        # ------------------------------------------------------------------
        # 1. Load sklearn / torch artefacts
        # ------------------------------------------------------------------
        self.scaler = joblib.load(MODELS_DIR / "scaler.pkl")
        self.iso_model = joblib.load(MODELS_DIR / "isolation_forest.pkl")
        self.calibrated_rf = joblib.load(MODELS_DIR / "random_forest.pkl")

        n_feats = self.scaler.n_features_in_
        self.ae_model = _Autoencoder(n_feats, AE_HIDDEN_DIMS)
        state = torch.load(
            MODELS_DIR / "autoencoder.pt", map_location="cpu", weights_only=True
        )
        self.ae_model.load_state_dict(state)
        self.ae_model.eval()
        self._log(f"Models loaded (input dim = {n_feats}).")

        # ------------------------------------------------------------------
        # 2. Build / load reference feature matrix
        #    (needed for LOF refitting and for rank-normalisation CDFs)
        # ------------------------------------------------------------------
        self._log("Building reference feature matrix (may take ~30 s) …")
        main_df, claim_df = load_all(verbose=False)

        # Pre-compute column medians from the full dataset so single-row
        # predictions don't collapse median-imputed features to NaN.
        _median_cols = [
            "Power",
            "Cylinder_capacity",
            "Value_vehicle",
            "Weight",
            "Length",
        ]
        self._col_medians: dict[str, float] = {
            col: float(main_df[col].median(skipna=True))
            for col in _median_cols
            if col in main_df.columns
        }

        X_full, self._ids_full = build_features(main_df, claim_df, verbose=False)
        self._feature_columns: list[str] = X_full.columns.tolist()
        self._X_full_scaled: np.ndarray = self.scaler.transform(
            X_full.values.astype(np.float32)
        )
        self._log(
            f"Reference matrix ready: "
            f"{self._X_full_scaled.shape[0]:,} × {self._X_full_scaled.shape[1]}"
        )

        # ------------------------------------------------------------------
        # 3. Compute reference raw-score CDFs for rank-normalisation
        # ------------------------------------------------------------------
        self._log("Computing reference score distributions …")

        # Isolation Forest: score_samples → negate (lower raw = more anomalous)
        self._ref_iso_raw: np.ndarray = -(
            self.iso_model.score_samples(self._X_full_scaled)
        )  # higher = more anomalous

        # Autoencoder: per-row MSE (higher = more anomalous)
        self._ref_ae_raw: np.ndarray = self._ae_recon_errors(self._X_full_scaled)

        # LOF: fit on reference data once; negate (lower raw = more anomalous)
        self._log("Fitting reference LOF …")
        lof_ref = LocalOutlierFactor(n_neighbors=20, contamination=0.05, n_jobs=-1)
        lof_ref.fit(self._X_full_scaled)
        self._ref_lof_raw: np.ndarray = -(
            lof_ref.negative_outlier_factor_
        )  # higher = more anomalous

        self._log("Reference distributions ready.")

        # ------------------------------------------------------------------
        # 4. Load existing score cache from CSV
        # ------------------------------------------------------------------
        self._score_cache: dict[int, list[dict]] = {}
        if SCORES_CACHE_PATH.exists():
            cache_df = pd.read_csv(SCORES_CACHE_PATH)
            for row in cache_df.itertuples(index=False):
                key = int(row.ID)
                self._score_cache.setdefault(key, []).append(
                    {
                        "ID": key,
                        "iso_score": float(row.iso_score),
                        "lof_score": float(row.lof_score),
                        "ae_score": float(row.ae_score),
                        "ensemble_anomaly_score": float(row.ensemble_anomaly_score),
                        "fraud_risk_score": float(row.fraud_risk_score),
                        "risk_tier": str(row.risk_tier),
                    }
                )
            self._log(
                f"Score cache loaded: {len(self._score_cache):,} unique IDs "
                f"({len(cache_df):,} records)"
            )
        else:
            self._log(
                "No score cache found; GET /claim/{id} will only serve live predictions."
            )

        self._log("FraudPredictor ready ✓")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, msg: str) -> None:
        if self._verbose:
            print(f"[predictor] {msg}", flush=True)

    def _ae_recon_errors(self, X_scaled: np.ndarray) -> np.ndarray:
        """Per-row MSE reconstruction error from the autoencoder."""
        X_t = torch.tensor(X_scaled.astype(np.float32))
        with torch.no_grad():
            recon = self.ae_model(X_t).numpy()
        return np.mean((X_scaled - recon) ** 2, axis=1)

    def _rank_vs_ref(self, values: np.ndarray, reference: np.ndarray) -> np.ndarray:
        """
        Rank-normalise `values` against `reference` CDF.
        Returns array in [0, 1]; higher = more extreme / anomalous.
        """
        return np.clip(
            np.array(
                [
                    percentileofscore(reference, v, kind="rank") / 100.0
                    for v in values
                ]
            ),
            0.0,
            1.0,
        )

    def _claims_to_raw_df(
        self, claims: list
    ) -> tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        Convert a list of ClaimInput objects into (main_df, claim_df) that
        build_features() can consume.
        """
        rows: list[dict] = []
        claim_rows: list[dict] = []

        for claim in claims:
            row = claim.model_dump(exclude={"claim_records"})
            rows.append(row)
            if claim.claim_records:
                for cr in claim.claim_records:
                    claim_rows.append(
                        {
                            "ID": claim.ID,
                            "Cost_claims_year": cr.Cost_claims_year,
                            "Claims_type": cr.Claims_type,
                            "Cost_claims_by_type": cr.Cost_claims_by_type,
                        }
                    )

        main_df = pd.DataFrame(rows)

        # Apply global-median fallbacks BEFORE data_loader helpers so that
        # single-row median imputation in build_features doesn't collapse to NaN.
        for col, med in self._col_medians.items():
            if col in main_df.columns:
                main_df[col] = main_df[col].fillna(med)

        # Apply the same cleaning pipeline used by load_main_dataset()
        main_df = _parse_dates(main_df)
        main_df = _clean_main(main_df)

        claim_df = pd.DataFrame(claim_rows) if claim_rows else None
        return main_df, claim_df

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def n_reference_policies(self) -> int:
        return int(self._X_full_scaled.shape[0])

    def predict(self, claims: list) -> list[dict]:
        """
        Score one or more ClaimInput objects.

        Parameters
        ----------
        claims : list[ClaimInput]

        Returns
        -------
        list of dicts matching the PredictionResponse schema.
        """
        main_df, claim_df = self._claims_to_raw_df(claims)
        X_new, ids_new = build_features(main_df, claim_df, verbose=False)

        # Reorder columns to match training order
        X_new = X_new[self._feature_columns]
        X_new_scaled = self.scaler.transform(X_new.values.astype(np.float32))
        n = len(X_new_scaled)

        # ---- Stage 1a: Isolation Forest ----------------------------------
        # score_samples() returns negative scores; negate → higher = anomalous
        iso_raw_new = -(self.iso_model.score_samples(X_new_scaled))
        iso_norm = self._rank_vs_ref(iso_raw_new, self._ref_iso_raw)

        # ---- Stage 1b: Autoencoder ----------------------------------------
        ae_raw_new = self._ae_recon_errors(X_new_scaled)
        ae_norm = self._rank_vs_ref(ae_raw_new, self._ref_ae_raw)

        # ---- Stage 1c: LOF  -----------------------------------------------
        # Refit LOF on reference + new claims together; take scores for the
        # last n rows (the new ones).  Negate → higher = anomalous.
        X_combined = np.vstack([self._X_full_scaled, X_new_scaled])
        lof = LocalOutlierFactor(n_neighbors=20, contamination=0.05, n_jobs=-1)
        lof.fit(X_combined)
        lof_raw_new = -(lof.negative_outlier_factor_[-n:])
        lof_norm = self._rank_vs_ref(lof_raw_new, self._ref_lof_raw)

        # ---- Ensemble & Stage 2 ------------------------------------------
        ensemble = (iso_norm + lof_norm + ae_norm) / 3.0
        fraud_proba = self.calibrated_rf.predict_proba(
            X_new_scaled.astype(np.float32)
        )[:, 1]

        # ---- Assemble & cache -------------------------------------------
        results: list[dict] = []
        for i in range(n):
            pid = int(ids_new.iloc[i])
            entry = {
                "ID": pid,
                "iso_score": float(iso_norm[i]),
                "lof_score": float(lof_norm[i]),
                "ae_score": float(ae_norm[i]),
                "ensemble_anomaly_score": float(ensemble[i]),
                "fraud_risk_score": float(fraud_proba[i]),
                "risk_tier": _assign_tier(float(ensemble[i])),
            }
            self._score_cache.setdefault(pid, []).append(entry)
            results.append(entry)

        return results

    def get_cached(self, policy_id: int) -> list[dict] | None:
        """Return all cached score records for a given policy ID, or None."""
        return self._score_cache.get(policy_id)
