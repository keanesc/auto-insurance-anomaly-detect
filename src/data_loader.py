"""
data_loader.py
--------------
Loads and performs initial cleaning of the motor vehicle insurance datasets.

Outputs
-------
load_main_dataset()   -> pd.DataFrame (105 555 rows × 30 cols, typed)
load_claim_types()    -> pd.DataFrame (sample_type_claim, ~7 367 rows × 4 cols)
load_all()            -> (main_df, claim_df)  ready for feature engineering
"""

from __future__ import annotations

import pathlib
from typing import Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR = (
    pathlib.Path(__file__).parent.parent
    / "data"
    / "Dataset of an actual motor vehicle insurance portfolio"
)
MAIN_CSV = DATA_DIR / "Motor vehicle insurance data.csv"
CLAIM_CSV = DATA_DIR / "sample type claim.csv"

# ---------------------------------------------------------------------------
# Date columns (DD/MM/YYYY)
# ---------------------------------------------------------------------------
DATE_COLS = [
    "Date_start_contract",
    "Date_last_renewal",
    "Date_next_renewal",
    "Date_birth",
    "Date_driving_licence",
    "Date_lapse",
]


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse all date columns from DD/MM/YYYY; non-parseable values → NaT."""
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
    return df


def _clean_main(df: pd.DataFrame) -> pd.DataFrame:
    """Type coercions, fill sentinels, and trivial cleaning on the main dataset."""
    # Numeric columns that may arrive as strings due to locale (comma decimals)
    numeric_cols = [
        "Seniority",
        "Policies_in_force",
        "Max_policies",
        "Max_products",
        "Lapse",
        "Payment",
        "Premium",
        "Cost_claims_year",
        "N_claims_year",
        "N_claims_history",
        "R_Claims_history",
        "Type_risk",
        "Area",
        "Second_driver",
        "Year_matriculation",
        "Power",
        "Cylinder_capacity",
        "Value_vehicle",
        "N_doors",
        "Length",
        "Weight",
        "Distribution_channel",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "."), errors="coerce"
            )

    # Type_fuel: strip whitespace, uppercase, map "NA" string → np.nan
    if "Type_fuel" in df.columns:
        df["Type_fuel"] = df["Type_fuel"].astype(str).str.strip().str.upper()
        df["Type_fuel"] = df["Type_fuel"].replace(
            {"NA": np.nan, "NAN": np.nan, "": np.nan}
        )

    # Length: already numeric after above; any remaining NaN stays NaN (motorbikes)

    # Non-negative guard for financial columns
    for col in ["Premium", "Cost_claims_year", "N_claims_year", "N_claims_history"]:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    return df


def load_main_dataset(
    path: pathlib.Path = MAIN_CSV, verbose: bool = True
) -> pd.DataFrame:
    """Load and clean the main insurance portfolio CSV."""
    df = pd.read_csv(path, sep=";", low_memory=False)
    df = _parse_dates(df)
    df = _clean_main(df)

    if verbose:
        print(
            f"[data_loader] Main dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} cols"
        )
        null_counts = df.isnull().sum()
        null_counts = null_counts[null_counts > 0]
        if len(null_counts):
            print("[data_loader] Columns with nulls:")
            for col, cnt in null_counts.items():
                print(f"  {col}: {cnt:,} ({100 * cnt / len(df):.1f}%)")

    return df


def load_claim_types(
    path: pathlib.Path = CLAIM_CSV, verbose: bool = True
) -> pd.DataFrame:
    """Load and validate the claim-type sample CSV."""
    df = pd.read_csv(path, sep=";", low_memory=False)

    # Standardise column name variations seen in the file
    df.columns = df.columns.str.strip()
    rename_map = {
        "Cost_claims_by_type": "Cost_claims_by_type",
        "Cost_claims_type": "Cost_claims_by_type",  # alternate header name
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Numeric coercions
    for col in ["Cost_claims_year", "Cost_claims_by_type"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "."), errors="coerce"
            )

    # Normalise claim type strings
    if "Claims_type" in df.columns:
        df["Claims_type"] = df["Claims_type"].astype(str).str.strip().str.lower()

    if verbose:
        print(
            f"[data_loader] Claim-type dataset loaded: {df.shape[0]:,} rows × {df.shape[1]} cols"
        )
        if "Claims_type" in df.columns:
            print("[data_loader] Claim type distribution:")
            print(df["Claims_type"].value_counts().to_string())

    return df


def load_all(verbose: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return (main_df, claim_df) — both cleaned and typed."""
    main_df = load_main_dataset(verbose=verbose)
    claim_df = load_claim_types(verbose=verbose)
    return main_df, claim_df


if __name__ == "__main__":
    main_df, claim_df = load_all()
    print("\nMain dataset dtypes:\n", main_df.dtypes)
    print("\nClaim-type sample:\n", claim_df.head())
