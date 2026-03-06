"""
supervised_model.py
-------------------
Stage 2: Pseudo-labelling + Random Forest classifier (adapted from the
research paper: SMOTE + Random Forest achieved 96.7 % F1 on a labelled dataset).

Workflow
--------
1. Policies with ensemble_anomaly_score ≥ HIGH_THRESHOLD → pseudo-label 1 (fraud)
   Policies with ensemble_anomaly_score ≤ LOW_THRESHOLD  → pseudo-label 0 (normal)
   Middle band (uncertain) is excluded from training.

2. SMOTE balances the pseudo-labelled training set (mirrors the paper's approach).

3. A Random Forest is trained on the pseudo-labelled set with 5-fold stratified CV.

4. The final RF's predict_proba(class=1) is computed for ALL 105 555 policies,
   giving a calibrated fraud_risk_score in [0, 1].

Public API
----------
run_supervised(X, scores_df, verbose=True)
    -> pd.DataFrame with columns:
         pseudo_label (int or NaN), fraud_risk_score (float)
       and prints cross-validation metrics.
"""

from __future__ import annotations

import pathlib
import warnings

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    make_scorer,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate

OUTPUTS_DIR = pathlib.Path(__file__).parent.parent / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"

# Thresholds for pseudo-labelling
# Raised HIGH to 0.90 so only the clearest anomalies become pseudo-fraud
# (~top 10% of ensemble scores, close to the paper's 6% fraud base rate).
# LOW kept at 0.15 to provide a clean normal training set.
HIGH_THRESHOLD = 0.90  # above → suspected fraud
LOW_THRESHOLD = 0.15  # below → likely normal

# Random Forest hyper-parameters (mirrors paper's RF, extended for dataset size)
RF_N_ESTIMATORS = 300
RF_MAX_DEPTH = None  # grow full trees; forest handles variance
RF_N_JOBS = -1
RF_RANDOM_STATE = 42

CV_FOLDS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pseudo_label(scores: pd.Series) -> pd.Series:
    """
    Assign pseudo-labels based on ensemble anomaly score thresholds.
    Returns a Series with values 0, 1, or NaN (uncertain / excluded).
    """
    labels = pd.Series(np.nan, index=scores.index)
    labels[scores >= HIGH_THRESHOLD] = 1
    labels[scores <= LOW_THRESHOLD] = 0
    return labels


def _print_cv_metrics(
    cv_results: dict, dataset_name: str = "pseudo-labelled"
) -> None:
    """Pretty-print cross-validation scores."""
    print(f"\n[supervised] === Cross-validation results on {dataset_name} set ===")
    for metric in ["accuracy", "precision", "recall", "f1"]:
        vals = cv_results[f"test_{metric}"]
        print(
            f"  {metric:12s}: {vals.mean():.4f} ± {vals.std():.4f}  "
            f"(paper RF: acc=0.967 f1=0.967)"
        )
    print()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_supervised(
    X: pd.DataFrame,
    scores_df: pd.DataFrame,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Pseudo-label → SMOTE → Random Forest → fraud_risk_score for all rows.

    Parameters
    ----------
    X          : feature matrix (output of feature_engineering.build_features)
    scores_df  : Stage 1 scores (output of anomaly_detection.run_anomaly_detection)
    verbose    : print progress and CV metrics

    Returns
    -------
    pd.DataFrame with columns:
        pseudo_label       : int (0/1) or NaN if uncertain
        fraud_risk_score   : float in [0, 1] — RF P(fraud) for all rows
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    ensemble_scores = scores_df["ensemble_anomaly_score"]
    pseudo_labels = _pseudo_label(ensemble_scores)

    n_fraud = (pseudo_labels == 1).sum()
    n_normal = (pseudo_labels == 0).sum()
    n_unsure = pseudo_labels.isna().sum()

    if verbose:
        print("[supervised] Pseudo-labels assigned:")
        print(f"  Fraud  (score ≥ {HIGH_THRESHOLD}): {n_fraud:,} policies")
        print(f"  Normal (score ≤ {LOW_THRESHOLD}):  {n_normal:,} policies")
        print(f"  Uncertain (excluded):              {n_unsure:,} policies")

    # --- Build training set (exclude uncertain rows) ----------------------
    mask_labelled = pseudo_labels.notna()
    X_train = X[mask_labelled].values.astype(np.float32)
    y_train = pseudo_labels[mask_labelled].values.astype(int)

    if verbose:
        print(
            f"[supervised] Training set: {len(X_train):,} rows "
            f"(fraud={int(y_train.sum()):,}, normal={int((y_train == 0).sum()):,})"
        )

    # --- SMOTE -----------------------------------------------------------
    # Mirror the paper: balance classes before training the RF
    smote = SMOTE(random_state=RF_RANDOM_STATE)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    if verbose:
        print(
            f"[supervised] After SMOTE: {len(X_resampled):,} rows "
            f"(fraud={int(y_resampled.sum()):,}, normal={int((y_resampled == 0).sum()):,})"
        )

    # --- Cross-validation on SMOTE-balanced set --------------------------
    rf = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        class_weight="balanced",
        n_jobs=RF_N_JOBS,
        random_state=RF_RANDOM_STATE,
    )

    scoring = {
        "accuracy": make_scorer(accuracy_score),
        "precision": make_scorer(precision_score, zero_division=0),
        "recall": make_scorer(recall_score, zero_division=0),
        "f1": make_scorer(f1_score, zero_division=0),
    }

    if verbose:
        print(f"[supervised] Running {CV_FOLDS}-fold stratified cross-validation …")

    cv_results = cross_validate(
        rf,
        X_resampled,
        y_resampled,
        cv=StratifiedKFold(
            n_splits=CV_FOLDS, shuffle=True, random_state=RF_RANDOM_STATE
        ),
        scoring=scoring,
        n_jobs=RF_N_JOBS,
    )

    if verbose:
        _print_cv_metrics(cv_results)

    # --- Final model: RF with isotonic calibration (3-fold CV) ----
    # Isotonic regression calibration corrects RF's over-confident 0/1 probs
    # so the output reflects a realistic fraud base rate (~5-10%).
    if verbose:
        print(
            "[supervised] Training calibrated Random Forest (3-fold isotonic CV) …"
        )

    rf_base = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        class_weight="balanced",
        n_jobs=RF_N_JOBS,
        random_state=RF_RANDOM_STATE,
    )

    # CalibratedClassifierCV fits rf_base and calibrator jointly via 3-fold CV
    calibrated_rf = CalibratedClassifierCV(rf_base, cv=3, method="isotonic")
    calibrated_rf.fit(X_resampled, y_resampled)

    # Brier score on the SMOTE training set (in-sample; proxy for calibration quality)
    cal_probs = calibrated_rf.predict_proba(X_resampled)[:, 1]
    brier = brier_score_loss(y_resampled, cal_probs)
    if verbose:
        print(
            f"[supervised] Calibration Brier score (train): {brier:.4f}  "
            f"(0.0=perfect, 0.25=random)"
        )

    # Save models: calibrated wrapper + uncalibrated constituent estimator
    joblib.dump(calibrated_rf, MODELS_DIR / "random_forest.pkl")
    # Extract one of the internal uncalibrated folds for feature importances
    rf_for_importances = calibrated_rf.calibrated_classifiers_[0].estimator
    joblib.dump(rf_for_importances, MODELS_DIR / "random_forest_uncalibrated.pkl")
    if verbose:
        print(f"[supervised] Models saved → {MODELS_DIR}")

    # --- Score ALL policies (including uncertain ones) --------------------
    fraud_risk_scores = calibrated_rf.predict_proba(X.values.astype(np.float32))[
        :, 1
    ]

    # --- Feature importance summary (top 15) -----------------------------
    if verbose:
        importances = pd.Series(
            rf_for_importances.feature_importances_, index=X.columns
        )
        top15 = importances.nlargest(15)
        print("[supervised] Top 15 feature importances:")
        for feat, imp in top15.items():
            print(f"  {feat:35s}: {imp:.4f}")

    result_df = pd.DataFrame(
        {
            "pseudo_label": pseudo_labels.values,
            "fraud_risk_score": fraud_risk_scores,
        }
    )

    if verbose:
        high_risk = (fraud_risk_scores >= 0.75).sum()
        print(
            f"\n[supervised] Policies with fraud_risk_score ≥ 0.75: "
            f"{high_risk:,} ({100 * high_risk / len(fraud_risk_scores):.1f}%)"
        )

    return result_df
