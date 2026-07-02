"""Analysis endpoints — frequency reports, unit analysis, question listing."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Subject, Question
from app.predictor import build_analysis_report
from app.schemas import AnalysisReport, SubjectOut, QuestionOut

router = APIRouter(prefix="/api/subjects", tags=["analysis"])


def _get_subject_or_404(subject_id: int, user: User, db: Session) -> Subject:
    s = db.get(Subject, subject_id)
    if not s or s.owner_id != user.id:
        raise HTTPException(404, "Subject not found.")
    return s


@router.get("/{subject_id}/analysis", response_model=AnalysisReport)
def get_analysis(
    subject_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Returns the full frequency analysis for a subject.
    No minimum-paper requirement enforced here — you can call it after
    even 1 paper, though the results improve significantly with 10+.
    """
    s    = _get_subject_or_404(subject_id, user, db)
    data = build_analysis_report(subject_id, db)
    return AnalysisReport(subject=SubjectOut.model_validate(s), **data)


@router.get("/{subject_id}/questions", response_model=list[QuestionOut])
def list_questions(
    subject_id: int,
    limit:  int = 100,
    offset: int = 0,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """List all extracted questions for a subject (paginated)."""
    _get_subject_or_404(subject_id, user, db)
    return (
        db.query(Question)
        .filter(Question.subject_id == subject_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
