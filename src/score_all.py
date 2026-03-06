"""
score_all.py
------------
End-to-end fraud detection pipeline.

Stages:
  1. Load & clean data          (data_loader)
  2. Feature engineering        (feature_engineering)
  3. Unsupervised anomaly det.  (anomaly_detection)  → Stage 1 scores
  4. Pseudo-label + RF          (supervised_model)   → fraud_risk_score

Output
------
outputs/stage1_scores.csv      — per-policy Isolation Forest / LOF / AE / ensemble scores
outputs/fraud_risk_scores.csv  — final deliverable with fraud_risk_score for all policies
outputs/models/                — serialised sklearn and PyTorch models + scaler

Usage
-----
    pixi run score
    # or
    python src/score_all.py
"""

from __future__ import annotations

import pathlib
import sys
import time

import pandas as pd

from anomaly_detection import run_anomaly_detection
from data_loader import load_all
from feature_engineering import build_features
from supervised_model import run_supervised

OUTPUTS_DIR = pathlib.Path(__file__).parent.parent / "outputs"
STAGE1_CACHE = OUTPUTS_DIR / "stage1_scores.csv"
# Pass --force to bypass the Stage-1 cache and retrain all models
FORCE_RETRAIN = "--force" in sys.argv


def main() -> None:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # ------------------------------------------------------------------
    # 1. Load data
    # ------------------------------------------------------------------
    print("=" * 60)
    print("STAGE 0 — Data loading")
    print("=" * 60)
    main_df, claim_df = load_all(verbose=True)

    # ------------------------------------------------------------------
    # 2. Feature engineering
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STAGE 0 — Feature engineering")
    print("=" * 60)
    X, ids = build_features(main_df, claim_df, verbose=True)

    # ------------------------------------------------------------------
    # 3. Unsupervised anomaly detection  (cached if --force not passed)
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STAGE 1 — Unsupervised anomaly detection")
    print("=" * 60)

    if not FORCE_RETRAIN and STAGE1_CACHE.exists():
        print(f"[score_all] Loading cached Stage 1 scores from {STAGE1_CACHE}")
        stage1_cached = pd.read_csv(STAGE1_CACHE)
        scores_df = stage1_cached[
            ["iso_score", "lof_score", "ae_score", "ensemble_anomaly_score"]
        ].reset_index(drop=True)
        print(f"[score_all] Loaded {len(scores_df):,} cached scores.")
    else:
        scores_df = run_anomaly_detection(X, verbose=True)
        # Persist Stage 1 scores
        stage1_full = pd.concat([ids.rename("ID"), scores_df], axis=1)
        stage1_full.to_csv(STAGE1_CACHE, index=False)
        print(f"\n[score_all] Stage 1 scores saved → {STAGE1_CACHE}")

    # ------------------------------------------------------------------
    # 4. Pseudo-label + supervised model
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("STAGE 2 — Pseudo-labelling + Random Forest")
    print("=" * 60)
    supervised_df = run_supervised(X, scores_df, verbose=True)

    # ------------------------------------------------------------------
    # 5. Assemble final output
    # ------------------------------------------------------------------
    final = pd.concat(
        [
            ids.rename("ID"),
            scores_df,
            supervised_df,
        ],
        axis=1,
    )

    # Add risk tier labels based on the continuous ensemble anomaly score
    # (the RF fraud_risk_score is bimodal by design; ensemble score is smoother)
    def _tier(score: float) -> str:
        if score >= 0.88:
            return "HIGH"
        if score >= 0.70:
            return "MEDIUM"
        if score >= 0.50:
            return "LOW"
        return "VERY_LOW"

    final["risk_tier"] = final["ensemble_anomaly_score"].map(_tier)

    output_path = OUTPUTS_DIR / "fraud_risk_scores.csv"
    final.to_csv(output_path, index=False)

    elapsed = time.time() - t0

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total time : {elapsed:.1f} s")
    print(f"Output     : {output_path}")
    print(f"Rows       : {len(final):,}")

    # Summary statistics
    print("\nFraud risk score distribution:")
    print(final["fraud_risk_score"].describe().round(4).to_string())

    print("\nRisk tier breakdown:")
    tier_counts = (
        final["risk_tier"]
        .value_counts()
        .reindex(["HIGH", "MEDIUM", "LOW", "VERY_LOW"], fill_value=0)
    )
    for tier, cnt in tier_counts.items():
        pct = 100 * cnt / len(final)
        print(f"  {tier:9s}: {cnt:7,}  ({pct:5.1f}%)")

    print("\nTop 20 highest-risk policies (by ensemble anomaly score):")
    top20 = (
        final[["ID", "ensemble_anomaly_score", "fraud_risk_score", "risk_tier"]]
        .nlargest(20, "ensemble_anomaly_score")
        .reset_index(drop=True)
    )
    print(top20.to_string(index=False))


if __name__ == "__main__":
    main()
