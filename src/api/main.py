"""
main.py
-------
FastAPI application for the auto insurance fraud detection API.

Endpoints
---------
GET  /health               — liveness / readiness check
POST /predict              — score a single claim
POST /predict/batch        — score multiple claims
GET  /claim/{id}           — retrieve previously scored results for a policy ID

The FraudPredictor singleton is loaded once at startup (takes ~60 s on first
run because it builds the reference feature matrix and refits the reference LOF).
Subsequent requests are fast.

Usage
-----
    pixi run serve
    # or directly:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import pathlib
import sys
import time
from contextlib import asynccontextmanager

# ---------------------------------------------------------------------------
# Ensure src/ is on the path so imports work from project root
# ---------------------------------------------------------------------------
_SRC_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from api.predictor import FraudPredictor
from api.schemas import (
    BatchPredictRequest,
    BatchPredictResponse,
    ClaimInput,
    HealthResponse,
    PredictionResponse,
)

# ---------------------------------------------------------------------------
# Application lifespan — load predictor once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(
        "[startup] Initialising FraudPredictor (this may take ~60 s) …", flush=True
    )
    t0 = time.time()
    app.state.predictor = FraudPredictor(verbose=True)
    elapsed = time.time() - t0
    print(f"[startup] FraudPredictor ready in {elapsed:.1f} s.", flush=True)
    yield
    # Shutdown: nothing to clean up
    print("[shutdown] API shutting down.", flush=True)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Auto Insurance Fraud Detection API",
    description=(
        "Scores motor vehicle insurance claims for fraud risk using a two-stage "
        "ensemble pipeline: unsupervised anomaly detection (Isolation Forest, LOF, "
        "Autoencoder) followed by a calibrated Random Forest classifier."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins by default — restrict to specific frontend origin in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _get_predictor(request: Request) -> FraudPredictor:
    predictor: FraudPredictor | None = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is still initialising. Please retry in a few seconds.",
        )
    return predictor


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness / readiness check",
    tags=["Health"],
)
async def health(request: Request) -> HealthResponse:
    """Returns 200 when the predictor is loaded and ready to serve requests."""
    predictor: FraudPredictor | None = getattr(request.app.state, "predictor", None)
    loaded = predictor is not None
    return HealthResponse(
        status="ok" if loaded else "initialising",
        models_loaded=loaded,
        n_reference_policies=predictor.n_reference_policies if loaded else 0,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Score a single insurance claim",
    tags=["Inference"],
)
async def predict_single(claim: ClaimInput, request: Request) -> PredictionResponse:
    """
    Submit one policy record and receive fraud risk scores.

    - **ensemble_anomaly_score**: mean of the three unsupervised detector scores [0, 1]
    - **fraud_risk_score**: calibrated Random Forest P(fraud) [0, 1]
    - **risk_tier**: HIGH | MEDIUM | LOW | VERY_LOW
    """
    predictor = _get_predictor(request)
    try:
        results = predictor.predict([claim])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Prediction failed: {exc}",
        ) from exc
    return PredictionResponse(**results[0])


@app.post(
    "/predict/batch",
    response_model=BatchPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Score multiple insurance claims in one request",
    tags=["Inference"],
)
async def predict_batch(
    body: BatchPredictRequest, request: Request
) -> BatchPredictResponse:
    """
    Submit a list of policy records and receive fraud risk scores for each.

    LOF is refit once for the entire batch, so batching is significantly more
    efficient than calling `/predict` repeatedly.

    Maximum recommended batch size: 1 000 claims.
    """
    predictor = _get_predictor(request)
    if not body.claims:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="'claims' list must not be empty.",
        )
    try:
        results = predictor.predict(body.claims)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Batch prediction failed: {exc}",
        ) from exc
    return BatchPredictResponse(results=[PredictionResponse(**r) for r in results])


@app.get(
    "/claim/{policy_id}",
    response_model=list[PredictionResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve stored fraud scores for a policy ID",
    tags=["Lookup"],
)
async def get_claim_scores(
    policy_id: int, request: Request
) -> list[PredictionResponse]:
    """
    Look up all stored fraud risk records for a given policy ID.

    This includes:
    - All ~105 000 policies scored during the offline batch run.
    - Any additional policies scored via `/predict` or `/predict/batch` since
      the server started (in-memory only; not persisted to disk).

    Returns **404** if no records exist for this ID.
    """
    predictor = _get_predictor(request)
    records = predictor.get_cached(policy_id)
    if records is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No fraud risk scores found for policy ID {policy_id}.",
        )
    return [PredictionResponse(**r) for r in records]
