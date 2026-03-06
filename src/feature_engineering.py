"""
feature_engineering.py
-----------------------
Derives the full feature matrix from the main dataset and the optional
claim-type sample. Mirrors the signal categories identified in the research
paper (policy lifecycle, demographics, financial ratios, vehicle, claim
history) and adapts them to the available columns.

Public API:
    build_features(main_df, claim_df=None) -> (X: pd.DataFrame, ids: pd.Series)

The returned DataFrame X contains only numeric columns, imputed and ready
for scaling. The companion ids Series maps each row to its original policy ID.
"""

from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd

# Reference date used for age / vehicle-age calculations
# (dataset covers up to 2019; use end-of-observation year)
REFERENCE_DATE = pd.Timestamp("2019-01-01")

# Claim types from the secondary file
CLAIM_TYPE_COLS = [
    "travel assistance",
    "broken windows",
    "complaint",
    "negligence",
    "theft",
    "fire",
    "all risks",
    "injuries",
    "other",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _years_between(date_series: pd.Series, reference: pd.Timestamp) -> pd.Series:
    """Fractional years from date_series to reference date."""
    delta = (reference - date_series).dt.days / 365.25
    return delta.clip(lower=0)


def _safe_divide(
    numerator: pd.Series, denominator: pd.Series, fill_value: float = 0.0
) -> pd.Series:
    """Divide two series, replacing division-by-zero with fill_value."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = numerator / denominator.replace(0, np.nan)
    return result.fillna(fill_value)


# ---------------------------------------------------------------------------
# Claim-type pivot (from secondary CSV)
# ---------------------------------------------------------------------------


def _build_claim_type_features(claim_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate the claim-type sample into per-ID features:
      - proportion of each claim type in total cost
      - flag columns for high-severity types (injuries, fire, negligence)
      - distinct claim type count
    Returns a DataFrame indexed by ID.
    """
    ct = claim_df.copy()
    ct["Claims_type"] = ct["Claims_type"].str.strip().str.lower()

    # Total cost per ID (across all rows in the sample)
    id_total = (
        ct.groupby("ID")["Cost_claims_by_type"].sum().rename("sample_total_cost")
    )

    # Pivot: cost per type per ID
    pivot = ct.pivot_table(
        index="ID",
        columns="Claims_type",
        values="Cost_claims_by_type",
        aggfunc="sum",
        fill_value=0.0,
    )

    # Keep only the known claim types (ignore unexpected categories)
    for t in CLAIM_TYPE_COLS:
        if t not in pivot.columns:
            pivot[t] = 0.0
    pivot = pivot[CLAIM_TYPE_COLS]

    # Proportion of each type in that ID's total sampled cost
    prop = pivot.div(id_total, axis=0).fillna(0.0)
    prop.columns = [f"prop_claim_{c.replace(' ', '_')}" for c in prop.columns]

    # High-severity binary flags
    flags = pd.DataFrame(index=pivot.index)
    flags["has_injury_claim"] = (pivot.get("injuries", 0) > 0).astype(int)
    flags["has_negligence_claim"] = (pivot.get("negligence", 0) > 0).astype(int)
    flags["has_fire_claim"] = (pivot.get("fire", 0) > 0).astype(int)
    flags["has_theft_claim"] = (pivot.get("theft", 0) > 0).astype(int)

    # Number of distinct claim types
    flags["claim_type_count"] = (pivot > 0).sum(axis=1).astype(int)

    return pd.concat([prop, flags], axis=1)


# ---------------------------------------------------------------------------
# Main feature builder
# ---------------------------------------------------------------------------


def build_features(
    main_df: pd.DataFrame,
    claim_df: Optional[pd.DataFrame] = None,
    verbose: bool = True,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Build the full feature matrix.

    Parameters
    ----------
    main_df    : cleaned main dataset (output of data_loader.load_main_dataset)
    claim_df   : optional cleaned claim-type dataset (output of data_loader.load_claim_types)
    verbose    : print feature summary

    Returns
    -------
    X    : pd.DataFrame  — numeric feature matrix (no NaNs, imputed)
    ids  : pd.Series     — policy IDs aligned to X rows
    """
    df = main_df.copy()
    ids = df["ID"].copy()

    feats = pd.DataFrame(index=df.index)

    # ------------------------------------------------------------------
    # 1. Temporal / demographic features
    #    (mirrors paper: "Age of Driver", "Policy Year")
    # ------------------------------------------------------------------
    feats["age_at_renewal"] = _years_between(df["Date_birth"], REFERENCE_DATE)
    feats["driving_experience_years"] = _years_between(
        df["Date_driving_licence"], REFERENCE_DATE
    )
    feats["vehicle_age"] = REFERENCE_DATE.year - df["Year_matriculation"].clip(
        lower=1950, upper=2019
    )
    feats["policy_duration_years"] = _years_between(
        df["Date_start_contract"], REFERENCE_DATE
    )
    # Licence obtained age — very young or very old licences are unusual
    feats["age_when_licensed"] = (
        _years_between(df["Date_birth"], REFERENCE_DATE)
        - feats["driving_experience_years"]
    ).clip(lower=0)

    # Days until next renewal (short cycle → suspicious rapid renewals)
    feats["days_to_next_renewal"] = (
        (df["Date_next_renewal"] - df["Date_last_renewal"])
        .dt.days.fillna(365)
        .clip(lower=0)
    )

    # ------------------------------------------------------------------
    # 2. Financial ratio features
    #    (mirrors paper: "Deductible", "Vehicle Price")
    # ------------------------------------------------------------------
    feats["loss_ratio"] = _safe_divide(
        df["Cost_claims_year"], df["Premium"], fill_value=0.0
    )
    feats["avg_claim_cost"] = _safe_divide(
        df["Cost_claims_year"], df["N_claims_year"], fill_value=0.0
    )
    feats["lifetime_claim_rate"] = _safe_divide(
        df["N_claims_history"], df["Seniority"], fill_value=0.0
    )
    feats["premium_per_hp"] = _safe_divide(
        df["Premium"], df["Power"], fill_value=0.0
    )
    feats["value_per_kg"] = _safe_divide(
        df["Value_vehicle"], df["Weight"], fill_value=0.0
    )
    # Absolute cost excess over premium (negative → no excess)
    feats["cost_premium_excess"] = (df["Cost_claims_year"] - df["Premium"]).clip(
        lower=0
    )

    # Raw financials (preserved for the model)
    feats["premium"] = df["Premium"].fillna(0)
    feats["cost_claims_year"] = df["Cost_claims_year"].fillna(0)
    feats["n_claims_year"] = df["N_claims_year"].fillna(0)
    feats["n_claims_history"] = df["N_claims_history"].fillna(0)
    feats["r_claims_history"] = df["R_Claims_history"].fillna(0)

    # ------------------------------------------------------------------
    # 3. Policy behaviour features
    #    (mirrors paper: "Past Claims", "Address Change", "Agent Type")
    # ------------------------------------------------------------------
    feats["seniority"] = df["Seniority"].fillna(0)
    feats["policies_in_force"] = df["Policies_in_force"].fillna(1)
    feats["max_policies"] = df["Max_policies"].fillna(1)
    feats["policy_concentration"] = (
        (df["Max_policies"] - df["Policies_in_force"]).clip(lower=0).fillna(0)
    )
    feats["multi_driver_flag"] = df["Second_driver"].fillna(0).astype(int)
    feats["broker_channel_flag"] = df["Distribution_channel"].fillna(0).astype(int)
    feats["semi_annual_payment"] = df["Payment"].fillna(0).astype(int)
    feats["lapse_flag"] = (df["Lapse"] > 0).astype(int).fillna(0)

    # ------------------------------------------------------------------
    # 4. Vehicle features
    #    (mirrors paper: "Make", "Vehicle Category", "Vehicle Price")
    # ------------------------------------------------------------------
    feats["type_risk"] = df["Type_risk"].fillna(3).astype(int)  # 3=car predominant
    feats["area_urban"] = df["Area"].fillna(0).astype(int)
    feats["power"] = df["Power"].fillna(df["Power"].median())
    feats["cylinder_capacity"] = df["Cylinder_capacity"].fillna(
        df["Cylinder_capacity"].median()
    )
    feats["value_vehicle"] = df["Value_vehicle"].fillna(df["Value_vehicle"].median())
    feats["n_doors"] = df["N_doors"].fillna(0).astype(int)
    feats["weight"] = df["Weight"].fillna(df["Weight"].median())
    feats["length"] = df["Length"].fillna(df["Length"].median())

    # Fuel: P=0, D=1, NaN=2 (unknown)
    fuel_map = {"P": 0, "D": 1}
    feats["type_fuel_enc"] = df["Type_fuel"].map(fuel_map).fillna(2).astype(int)

    # ------------------------------------------------------------------
    # 5. Claim-type features (from secondary CSV, left-joined on ID)
    #    (mirrors paper: injury/fault signals)
    # ------------------------------------------------------------------
    if claim_df is not None and len(claim_df) > 0:
        ct_feats = _build_claim_type_features(claim_df)
        # Join on ID: set feats index to ID values, join, then restore integer index
        orig_index = feats.index
        feats.index = ids.values
        feats = feats.join(ct_feats, how="left")
        feats.index = orig_index
        # Fill NaN for policies not in the claim sample → 0 (no claim info)
        ct_cols = ct_feats.columns.tolist()
        feats[ct_cols] = feats[ct_cols].fillna(0.0)
    else:
        # Insert zero-filled placeholder columns so downstream code is stable
        for t in CLAIM_TYPE_COLS:
            feats[f"prop_claim_{t.replace(' ', '_')}"] = 0.0
        for c in [
            "has_injury_claim",
            "has_negligence_claim",
            "has_fire_claim",
            "has_theft_claim",
            "claim_type_count",
        ]:
            feats[c] = 0

    # ------------------------------------------------------------------
    # Final imputation: any remaining NaNs → column median (safety net)
    # ------------------------------------------------------------------
    feats = feats.infer_objects()
    for col in feats.columns:
        if feats[col].isnull().any():
            feats[col] = feats[col].fillna(feats[col].median())
    # Ensure all float
    feats = feats.astype(float)

    if verbose:
        print(
            f"[feature_engineering] Feature matrix: {feats.shape[0]:,} rows × {feats.shape[1]} features"
        )
        print(f"[feature_engineering] Feature columns: {feats.columns.tolist()}")

    return feats, ids
