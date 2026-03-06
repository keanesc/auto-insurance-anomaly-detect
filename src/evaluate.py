"""
evaluate.py
-----------
Diagnostics and validation of the fraud detection pipeline.

Since no ground-truth labels exist in this dataset, evaluation uses:
  1. Intrinsic metrics on Stage 1 anomaly scores
       – Score distribution per risk feature quantile
       – Descriptor statistics for HIGH vs VERY_LOW risk groups
  2. Stage 2 RF feature importance (saved during training)
  3. Correlation between fraud risk score and known fraud signals
       (loss_ratio, avg_claim_cost, R_Claims_history, n_claims_history)
  4. Comparison tables: top-risk policies vs overall population
  5. Matplotlib figures saved to outputs/figures/

Usage
-----
    pixi run evaluate
    # or
    python src/evaluate.py       (run after score_all.py)
"""

from __future__ import annotations

import pathlib

import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # non-interactive backend (headless servers)
import matplotlib.pyplot as plt
import seaborn as sns

from data_loader import load_all
from feature_engineering import build_features

OUTPUTS_DIR = pathlib.Path(__file__).parent.parent / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
MODELS_DIR = OUTPUTS_DIR / "models"
SCORES_PATH = OUTPUTS_DIR / "fraud_risk_scores.csv"

RISK_FEATURES = [
    "loss_ratio",
    "avg_claim_cost",
    "r_claims_history",
    "n_claims_history",
    "lifetime_claim_rate",
    "cost_premium_excess",
    "n_claims_year",
    "has_injury_claim",
    "has_negligence_claim",
    "has_fire_claim",
]


def _require_scores() -> pd.DataFrame:
    if not SCORES_PATH.exists():
        raise FileNotFoundError(
            f"Scores file not found: {SCORES_PATH}\n"
            "Run `pixi run score` (or `python src/score_all.py`) first."
        )
    return pd.read_csv(SCORES_PATH)


# ---------------------------------------------------------------------------
# 1. Score distribution plot
# ---------------------------------------------------------------------------


def plot_score_distributions(scores: pd.DataFrame) -> None:
    """Histogram + KDE for ensemble and RF fraud scores."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Fraud Score Distributions", fontsize=14, fontweight="bold")

    for ax, col, colour, title in [
        (
            axes[0],
            "ensemble_anomaly_score",
            "steelblue",
            "Stage 1 — Ensemble Anomaly Score",
        ),
        (axes[1], "fraud_risk_score", "firebrick", "Stage 2 — RF Fraud Risk Score"),
    ]:
        data = scores[col].dropna()
        ax.hist(
            data, bins=100, color=colour, alpha=0.6, density=True, label="histogram"
        )
        data.plot.kde(ax=ax, color=colour, linewidth=2, label="KDE")
        ax.axvline(
            0.75,
            color="black",
            linestyle="--",
            linewidth=1.2,
            label="0.75 threshold",
        )
        ax.set_title(title)
        ax.set_xlabel("Score")
        ax.set_ylabel("Density")
        ax.legend()

    plt.tight_layout()
    out = FIGURES_DIR / "score_distributions.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[evaluate] Saved → {out}")


# ---------------------------------------------------------------------------
# 2. Feature importance
# ---------------------------------------------------------------------------


def plot_feature_importance() -> None:
    """Load the saved RF and plot the top 25 feature importances."""
    # Prefer the uncalibrated RF (has feature_importances_ directly)
    rf_path = MODELS_DIR / "random_forest_uncalibrated.pkl"
    if not rf_path.exists():
        rf_path = MODELS_DIR / "random_forest.pkl"
    if not rf_path.exists():
        print(
            "[evaluate] Random Forest model not found — skipping feature importance plot."
        )
        return

    rf = joblib.load(rf_path)
    # RandomForestClassifier has feature_importances_ directly.
    # CalibratedClassifierCV stores fold models in .calibrated_classifiers_[i].estimator
    if hasattr(rf, "feature_importances_"):
        base_rf = rf
    elif hasattr(rf, "calibrated_classifiers_"):
        base_rf = rf.calibrated_classifiers_[0].estimator
    else:
        print(
            "[evaluate] No feature_importances_ \u2014 skipping feature importance plot."
        )
        return
    if not hasattr(base_rf, "feature_importances_"):
        print(
            "[evaluate] No feature_importances_ \u2014 skipping feature importance plot."
        )
        return

    # We need feature names; load the feature matrix quickly
    main_df, claim_df = load_all(verbose=False)
    X, _ = build_features(main_df, claim_df, verbose=False)

    importances = pd.Series(base_rf.feature_importances_, index=X.columns)
    top25 = importances.nlargest(25).sort_values()

    fig, ax = plt.subplots(figsize=(10, 8))
    top25.plot.barh(ax=ax, color="steelblue", alpha=0.8)
    ax.set_title("Random Forest — Top 25 Feature Importances", fontweight="bold")
    ax.set_xlabel("Importance")
    plt.tight_layout()
    out = FIGURES_DIR / "feature_importance.png"
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"[evaluate] Saved → {out}")

    print("\n[evaluate] Top 10 features:")
    for feat, imp in importances.nlargest(10).items():
        print(f"  {feat:35s}: {imp:.4f}")


# ---------------------------------------------------------------------------
# 3. Risk stratification: HIGH vs VERY_LOW
# ---------------------------------------------------------------------------


def risk_group_comparison(scores: pd.DataFrame, X: pd.DataFrame) -> None:
    """Describe distributions of key fraud signals by risk tier."""
    combined = pd.concat(
        [
            X[RISK_FEATURES].reset_index(drop=True),
            scores[["fraud_risk_score", "risk_tier"]].reset_index(drop=True),
        ],
        axis=1,
    )

    high = combined[combined["risk_tier"] == "HIGH"]
    very_low = combined[combined["risk_tier"] == "VERY_LOW"]
    all_data = combined

    print("\n[evaluate] === Risk group comparison ===")
    print(f"HIGH risk     : {len(high):,} policies")
    print(f"VERY_LOW risk : {len(very_low):,} policies")
    print(f"Total         : {len(all_data):,} policies\n")

    comparison = pd.DataFrame(
        {
            "ALL_mean": all_data[RISK_FEATURES].mean(),
            "HIGH_mean": high[RISK_FEATURES].mean(),
            "VERY_LOW_mean": very_low[RISK_FEATURES].mean(),
        }
    )
    comparison["HIGH_vs_ALL_ratio"] = (
        comparison["HIGH_mean"] / comparison["ALL_mean"].replace(0, np.nan)
    ).round(2)
    print(comparison.round(3).to_string())

    # Box plot comparisons for key features
    plot_features = [
        f
        for f in RISK_FEATURES
        if f in combined.columns and combined[f].nunique() > 2
    ][:4]

    if plot_features:
        plot_df = combined[
            combined["risk_tier"].isin(["HIGH", "MEDIUM", "LOW", "VERY_LOW"])
        ].copy()
        plot_df["risk_tier"] = pd.Categorical(
            plot_df["risk_tier"], categories=["HIGH", "MEDIUM", "LOW", "VERY_LOW"]
        )
        fig, axes = plt.subplots(
            1, len(plot_features), figsize=(5 * len(plot_features), 6)
        )
        if len(plot_features) == 1:
            axes = [axes]
        for ax, feat in zip(axes, plot_features):
            sns.boxplot(
                data=plot_df,
                x="risk_tier",
                y=feat,
                hue="risk_tier",
                ax=ax,
                palette="RdYlGn_r",
                showfliers=False,
                legend=False,
            )
            ax.set_title(feat, fontsize=10)
            ax.set_xlabel("")
            ax.tick_params(axis="x", rotation=15)
        fig.suptitle(
            "Key Fraud Signal Distributions by Risk Tier", fontweight="bold"
        )
        plt.tight_layout()
        out = FIGURES_DIR / "risk_tier_boxplots.png"
        plt.savefig(out, dpi=150)
        plt.close()
        print(f"\n[evaluate] Saved → {out}")


# ---------------------------------------------------------------------------
# 4. Correlation: fraud_risk_score vs known fraud signals
# ---------------------------------------------------------------------------


def print_correlations(scores: pd.DataFrame, X: pd.DataFrame) -> None:
    """Print Pearson and Spearman correlations of fraud_risk_score with risk features."""
    combined = pd.concat(
        [
            X[RISK_FEATURES].reset_index(drop=True),
            scores[["fraud_risk_score"]].reset_index(drop=True),
        ],
        axis=1,
    )
    pearson = combined.corr(method="pearson")["fraud_risk_score"].drop(
        "fraud_risk_score"
    )
    spearman = combined.corr(method="spearman")["fraud_risk_score"].drop(
        "fraud_risk_score"
    )
    corr_df = pd.DataFrame({"Pearson": pearson, "Spearman": spearman})
    print("\n[evaluate] === Correlation with fraud_risk_score ===")
    print(corr_df.sort_values("Spearman", ascending=False).round(4).to_string())


# ---------------------------------------------------------------------------
# 5. Top 50 riskiest policies profile
# ---------------------------------------------------------------------------


def top_risk_profile(scores: pd.DataFrame, main_df: pd.DataFrame) -> None:
    """Print a summary of the 50 highest-risk policies."""
    top50_ids = scores.nlargest(50, "fraud_risk_score")["ID"].values
    top50 = main_df[main_df["ID"].isin(top50_ids)].copy()

    print("\n[evaluate] === Top 50 highest-risk policy profiles ===")
    summary_cols = [
        "ID",
        "Premium",
        "Cost_claims_year",
        "N_claims_year",
        "N_claims_history",
        "R_Claims_history",
        "Seniority",
        "Type_risk",
        "Area",
        "Power",
        "Value_vehicle",
    ]
    available = [c for c in summary_cols if c in top50.columns]
    print(top50[available].describe().round(2).to_string())

    # Compare vs overall population
    print("\n[evaluate] Overall population comparison:")
    print(main_df[available].describe().round(2).to_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("[evaluate] Loading scores …")
    scores = _require_scores()

    print("[evaluate] Loading features for analysis …")
    main_df, claim_df = load_all(verbose=False)
    X, _ = build_features(main_df, claim_df, verbose=False)

    # --- Plots ---
    plot_score_distributions(scores)
    plot_feature_importance()

    # --- Tabular analysis ---
    print_correlations(scores, X)
    risk_group_comparison(scores, X)
    top_risk_profile(scores, main_df)

    print("\n[evaluate] Figures saved to:", FIGURES_DIR)


if __name__ == "__main__":
    main()
