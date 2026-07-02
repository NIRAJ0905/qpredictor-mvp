"""Prediction endpoints — run the prediction engine, return ranked questions."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Subject, Paper, Prediction
from app.predictor import run_prediction
from app.schemas import PredictionOut, PredictionReport, SubjectOut

router     = APIRouter(prefix="/api/subjects", tags=["predictions"])
MIN_PAPERS = 10


def _get_subject_or_404(subject_id: int, user: User, db: Session) -> Subject:
    s = db.get(Subject, subject_id)
    if not s or s.owner_id != user.id:
        raise HTTPException(404, "Subject not found.")
    return s


@router.post("/{subject_id}/predictions", response_model=PredictionReport)
def generate_predictions(
    subject_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Run the prediction engine for a subject and return ranked predictions.
    Requires at least 10 processed papers for meaningful results
    (will run with fewer but returns a warning in the message).
    """
    s = _get_subject_or_404(subject_id, user, db)

    processed_count = (
        db.query(Paper)
        .filter(Paper.subject_id == subject_id, Paper.status == "processed")
        .count()
    )

    message = ""
    if processed_count == 0:
        raise HTTPException(
            400,
            "No processed papers found. Upload and process at least 1 paper first."
        )
    if processed_count < MIN_PAPERS:
        message = (
            f"Warning: Only {processed_count} processed paper(s) found. "
            f"Predictions improve significantly with {MIN_PAPERS}+ papers. "
        )

    predictions = run_prediction(subject_id, db)

    if not message:
        message = f"Generated {len(predictions)} predictions from {processed_count} papers."

    return PredictionReport(
        subject=SubjectOut.model_validate(s),
        generated_at=datetime.now(timezone.utc),
        total_predictions=len(predictions),
        predictions=[PredictionOut.model_validate(p) for p in predictions],
        message=message,
    )


@router.get("/{subject_id}/predictions", response_model=PredictionReport)
def get_predictions(
    subject_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """Fetch the most recently generated predictions (without re-running the engine)."""
    s = _get_subject_or_404(subject_id, user, db)

    preds = (
        db.query(Prediction)
        .filter(Prediction.subject_id == subject_id)
        .order_by(Prediction.rank)
        .all()
    )

    message = (
        f"{len(preds)} predictions on file. POST to this URL to regenerate."
        if preds else
        "No predictions yet. POST to this URL to generate them."
    )

    return PredictionReport(
        subject=SubjectOut.model_validate(s),
        generated_at=datetime.now(timezone.utc),
        total_predictions=len(preds),
        predictions=[PredictionOut.model_validate(p) for p in preds],
        message=message,
    )
