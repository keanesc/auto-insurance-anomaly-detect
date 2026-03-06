"""
anomaly_detection.py
--------------------
Stage 1: Unsupervised anomaly detection.

Three detectors are trained independently on the feature matrix:
  • Isolation Forest
  • Local Outlier Factor (novelty=False; transductive)
  • Autoencoder (PyTorch) — reconstruction-error as anomaly score

Each detector's raw score is rank-normalised to [0, 1].
The ensemble score is the arithmetic mean of the three normalised scores.
A high score (→1) indicates the policy looks anomalous / potentially fraudulent.

Public API
----------
run_anomaly_detection(X, verbose=True, contamination=0.05)
    -> pd.DataFrame with columns:
         iso_score, lof_score, ae_score, ensemble_anomaly_score
"""

from __future__ import annotations

import pathlib

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset

OUTPUTS_DIR = pathlib.Path(__file__).parent.parent / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"

CONTAMINATION = 0.05  # ~5 % fraud assumed, consistent with paper's ~6 % rate
ISO_N_ESTIMATORS = 200
LOF_N_NEIGHBORS = 20
AE_HIDDEN_DIMS = [64, 32, 16]  # encoder bottleneck; decoder mirrors
AE_EPOCHS = 50
AE_BATCH_SIZE = 2048
AE_LR = 1e-3


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rank_normalise(scores: np.ndarray) -> np.ndarray:
    """Map raw scores to [0, 1] via rank percentile (robust to outliers)."""
    from scipy.stats import rankdata  # scipy is a dep of sklearn

    ranks = rankdata(scores)
    return (ranks - 1) / (len(ranks) - 1)


def _rank_normalise_inverted(scores: np.ndarray) -> np.ndarray:
    """
    Isolation Forest and LOF return *negative* scores for anomalies
    (lower = more anomalous).  Invert before rank-normalising so that
    high values = anomalous.
    """
    return _rank_normalise(-scores)


# ---------------------------------------------------------------------------
# Isolation Forest
# ---------------------------------------------------------------------------


def _run_isolation_forest(
    X_scaled: np.ndarray, contamination: float, verbose: bool
) -> np.ndarray:
    if verbose:
        print("[anomaly] Training Isolation Forest …")
    iso = IsolationForest(
        n_estimators=ISO_N_ESTIMATORS,
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    iso.fit(X_scaled)
    raw_scores = iso.score_samples(X_scaled)  # negative; lower = more anomalous
    joblib.dump(iso, MODELS_DIR / "isolation_forest.pkl")
    if verbose:
        print(
            f"[anomaly] Isolation Forest done. Score range: [{raw_scores.min():.3f}, {raw_scores.max():.3f}]"
        )
    return raw_scores


# ---------------------------------------------------------------------------
# Local Outlier Factor
# ---------------------------------------------------------------------------


def _run_lof(
    X_scaled: np.ndarray, contamination: float, verbose: bool
) -> np.ndarray:
    if verbose:
        print("[anomaly] Training Local Outlier Factor …")
    lof = LocalOutlierFactor(
        n_neighbors=LOF_N_NEIGHBORS,
        contamination=contamination,
        n_jobs=-1,
    )
    lof.fit(X_scaled)
    raw_scores = lof.negative_outlier_factor_  # negative; lower = more anomalous
    joblib.dump(lof, MODELS_DIR / "lof.pkl")
    if verbose:
        print(
            f"[anomaly] LOF done. Score range: [{raw_scores.min():.3f}, {raw_scores.max():.3f}]"
        )
    return raw_scores


# ---------------------------------------------------------------------------
# Autoencoder (PyTorch)
# ---------------------------------------------------------------------------


class _Autoencoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dims: list[int]):
        super().__init__()
        # Encoder
        enc_layers: list[nn.Module] = []
        in_d = input_dim
        for h in hidden_dims:
            enc_layers += [nn.Linear(in_d, h), nn.BatchNorm1d(h), nn.ReLU()]
            in_d = h
        self.encoder = nn.Sequential(*enc_layers)

        # Decoder (mirror)
        dec_layers: list[nn.Module] = []
        for h in reversed(hidden_dims[:-1]):
            dec_layers += [nn.Linear(in_d, h), nn.BatchNorm1d(h), nn.ReLU()]
            in_d = h
        dec_layers.append(nn.Linear(in_d, input_dim))
        self.decoder = nn.Sequential(*dec_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.decoder(self.encoder(x))


def _run_autoencoder(X_scaled: np.ndarray, verbose: bool) -> np.ndarray:
    if verbose:
        print("[anomaly] Training Autoencoder …")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_t = torch.tensor(X_scaled, dtype=torch.float32)
    loader = DataLoader(TensorDataset(X_t), batch_size=AE_BATCH_SIZE, shuffle=True)

    model = _Autoencoder(X_scaled.shape[1], AE_HIDDEN_DIMS).to(device)
    optimiser = torch.optim.Adam(model.parameters(), lr=AE_LR)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(AE_EPOCHS):
        epoch_loss = 0.0
        n_batches = 0
        for (batch,) in loader:
            batch = batch.to(device)
            recon = model(batch)
            loss = criterion(recon, batch)
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            epoch_loss += loss.item()
            n_batches += 1
        if verbose and (epoch + 1) % 10 == 0:
            print(
                f"[anomaly]   AE epoch {epoch + 1}/{AE_EPOCHS}  loss={epoch_loss / n_batches:.5f}"
            )

    # Compute per-sample reconstruction error (MSE per row)
    model.eval()
    with torch.no_grad():
        recon_all = model(X_t.to(device)).cpu().numpy()
    recon_errors = np.mean((X_scaled - recon_all) ** 2, axis=1)

    torch.save(model.state_dict(), MODELS_DIR / "autoencoder.pt")
    if verbose:
        print(
            f"[anomaly] Autoencoder done. Reconstruction error range: [{recon_errors.min():.5f}, {recon_errors.max():.5f}]"
        )
    return recon_errors  # higher = more anomalous (no inversion needed)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_anomaly_detection(
    X: pd.DataFrame,
    verbose: bool = True,
    contamination: float = CONTAMINATION,
) -> pd.DataFrame:
    """
    Fit all three detectors and return an ensemble anomaly score DataFrame.

    Parameters
    ----------
    X             : feature matrix (output of feature_engineering.build_features)
    verbose       : print progress
    contamination : assumed fraction of anomalies (0–0.5)

    Returns
    -------
    pd.DataFrame with columns:
        iso_score, lof_score, ae_score, ensemble_anomaly_score
    All values in [0, 1]; higher → more suspicious.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.values.astype(np.float32))
    joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

    # Run detectors
    iso_raw = _run_isolation_forest(X_scaled, contamination, verbose)
    lof_raw = _run_lof(X_scaled, contamination, verbose)
    ae_raw = _run_autoencoder(X_scaled, verbose)

    # Normalise to [0, 1]; ISO and LOF are inverted (lower raw = more anomalous)
    iso_norm = _rank_normalise_inverted(iso_raw)
    lof_norm = _rank_normalise_inverted(lof_raw)
    ae_norm = _rank_normalise(ae_raw)  # already: higher = more anomalous

    ensemble = (iso_norm + lof_norm + ae_norm) / 3.0

    scores_df = pd.DataFrame(
        {
            "iso_score": iso_norm,
            "lof_score": lof_norm,
            "ae_score": ae_norm,
            "ensemble_anomaly_score": ensemble,
        }
    )

    if verbose:
        q = scores_df["ensemble_anomaly_score"].quantile(
            [0.5, 0.75, 0.9, 0.95, 0.99]
        )
        print("[anomaly] Ensemble score quantiles:")
        for pct, val in q.items():
            print(f"  {int(pct * 100)}th pct: {val:.4f}")
        flagged = (scores_df["ensemble_anomaly_score"] >= 0.75).sum()
        print(
            f"[anomaly] Policies scoring ≥ 0.75: {flagged:,} ({100 * flagged / len(scores_df):.1f}%)"
        )

    return scores_df
