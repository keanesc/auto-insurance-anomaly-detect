"""
schemas.py
----------
Pydantic request/response models for the fraud-detection API.

Field names intentionally match the raw CSV column names exactly so that
the predictor can convert them to a pandas DataFrame with zero renaming.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Sub-record: one row from the claim-type CSV
# ---------------------------------------------------------------------------


class ClaimTypeRecord(BaseModel):
    """A single row from the claim-type cost breakdown file."""

    Cost_claims_year: float = Field(
        description="Total claim cost for this policy year",
        ge=0,
    )
    Claims_type: str = Field(
        description=(
            "Claim type label (e.g. 'travel assistance', 'broken windows', "
            "'complaint', 'negligence', 'theft', 'fire', 'all risks', "
            "'injuries', 'other')"
        )
    )
    Cost_claims_by_type: float = Field(
        description="Cost attributable to this specific claim type",
        ge=0,
    )


# ---------------------------------------------------------------------------
# Primary request: one insurance policy / claim
# ---------------------------------------------------------------------------


class ClaimInput(BaseModel):
    """
    All raw fields for a single motor vehicle insurance policy record.
    Dates must be supplied in DD/MM/YYYY format (matching the original CSV).
    """

    # Identity
    ID: int = Field(description="Policy identifier (may repeat across years)")

    # Date fields (DD/MM/YYYY strings)
    Date_start_contract: str = Field(
        description="Contract start date (DD/MM/YYYY)",
        examples=["01/01/2015"],
    )
    Date_last_renewal: str = Field(
        description="Most recent renewal date (DD/MM/YYYY)",
        examples=["01/01/2019"],
    )
    Date_next_renewal: str = Field(
        description="Next scheduled renewal date (DD/MM/YYYY)",
        examples=["01/01/2020"],
    )
    Date_birth: str = Field(
        description="Policy holder date of birth (DD/MM/YYYY)",
        examples=["15/06/1980"],
    )
    Date_driving_licence: str = Field(
        description="Date driving licence was issued (DD/MM/YYYY)",
        examples=["20/09/1998"],
    )
    Date_lapse: Optional[str] = Field(
        default=None,
        description="Lapse date, if the policy has lapsed (DD/MM/YYYY). Null if active.",
    )

    # Policy / administrative
    Seniority: float = Field(description="Years the policy has been held", ge=0)
    Policies_in_force: float = Field(
        description="Number of policies currently active", ge=0
    )
    Max_policies: float = Field(
        description="Maximum number of policies the holder has ever held", ge=0
    )
    Max_products: float = Field(
        description="Maximum number of products ever held", ge=0
    )
    Lapse: float = Field(
        description="Lapse indicator (0 = active, 1 = lapsed)", ge=0
    )
    Payment: float = Field(
        description="Payment frequency code (0 = annual, 1 = semi-annual)"
    )
    Distribution_channel: float = Field(
        description="Distribution channel code (0 = direct, 1 = broker)"
    )
    Second_driver: float = Field(
        description="Second driver flag (0 = no, 1 = yes)", ge=0
    )

    # Financial
    Premium: float = Field(description="Annual premium (EUR)", ge=0)
    Cost_claims_year: float = Field(
        description="Total claim cost this policy year (EUR)", ge=0
    )
    N_claims_year: float = Field(
        description="Number of claims this policy year", ge=0
    )
    N_claims_history: float = Field(description="Total lifetime claim count", ge=0)
    R_Claims_history: float = Field(
        description="Lifetime claim rate (claims per year)", ge=0
    )

    # Vehicle
    Type_risk: float = Field(
        description="Vehicle risk type code (1=motorbike, 2=van, 3=car, 4=other)",
        ge=1,
    )
    Area: float = Field(description="Area code (0=rural, 1=urban)", ge=0)
    Year_matriculation: float = Field(
        description="Year vehicle was first registered", ge=1950
    )
    Power: float = Field(description="Engine power (horsepower)", ge=0)
    Cylinder_capacity: float = Field(
        description="Engine cylinder capacity (cc)", ge=0
    )
    Value_vehicle: float = Field(description="Estimated vehicle value (EUR)", ge=0)
    N_doors: float = Field(description="Number of doors", ge=0)
    Length: Optional[float] = Field(
        default=None, description="Vehicle length (mm). Null for motorbikes."
    )
    Weight: float = Field(description="Vehicle weight (kg)", ge=0)
    Type_fuel: Optional[str] = Field(
        default=None,
        description="Fuel type: 'P' (petrol), 'D' (diesel), or null if unknown.",
        examples=["P", "D"],
    )

    # Optional claim-type breakdown records for this policy
    claim_records: Optional[List[ClaimTypeRecord]] = Field(
        default=None,
        description=(
            "Optional list of claim-type cost records for this policy. "
            "If supplied, proportional claim-type features (injury, fire, etc.) "
            "will be computed; otherwise those features default to zero."
        ),
    )


# ---------------------------------------------------------------------------
# Response: scored result for one policy
# ---------------------------------------------------------------------------


class PredictionResponse(BaseModel):
    """Fraud risk scores and tier for a single policy."""

    ID: int = Field(description="Policy identifier")
    iso_score: float = Field(
        description="Normalised Isolation Forest anomaly score [0, 1]"
    )
    lof_score: float = Field(
        description="Normalised Local Outlier Factor anomaly score [0, 1]"
    )
    ae_score: float = Field(
        description="Normalised autoencoder reconstruction error [0, 1]"
    )
    ensemble_anomaly_score: float = Field(
        description="Mean of iso-, lof- and ae_score [0, 1]"
    )
    fraud_risk_score: float = Field(
        description="Calibrated Random Forest P(fraud) [0, 1]"
    )
    risk_tier: str = Field(description="Risk tier: HIGH | MEDIUM | LOW | VERY_LOW")


# ---------------------------------------------------------------------------
# Batch request / response
# ---------------------------------------------------------------------------


class BatchPredictRequest(BaseModel):
    claims: List[ClaimInput] = Field(description="List of policy records to score")


class BatchPredictResponse(BaseModel):
    results: List[PredictionResponse]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    n_reference_policies: int = Field(
        description="Number of policies in the reference dataset used for LOF refitting"
    )
