"""Subject management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Subject, Paper, Question
from app.schemas import SubjectCreate, SubjectOut, SubjectDetail

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

MIN_PAPERS = 10


def _get_subject_or_404(subject_id: int, user: User, db: Session) -> Subject:
    subj = db.get(Subject, subject_id)
    if not subj or subj.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Subject not found.")
    return subj


@router.post("", response_model=SubjectOut, status_code=201)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subj = Subject(owner_id=user.id, **payload.model_dump())
    db.add(subj)
    db.commit()
    db.refresh(subj)
    return subj


@router.get("", response_model=list[SubjectDetail])
def list_subjects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subjects = db.query(Subject).filter(Subject.owner_id == user.id).all()
    result = []
    for s in subjects:
        pc = db.query(Paper).filter(Paper.subject_id == s.id).count()
        qc = db.query(Question).filter(Question.subject_id == s.id).count()
        result.append(SubjectDetail(
            **SubjectOut.model_validate(s).model_dump(),
            paper_count=pc,
            question_count=qc,
            is_ready=(pc >= MIN_PAPERS),
        ))
    return result


@router.get("/{subject_id}", response_model=SubjectDetail)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s  = _get_subject_or_404(subject_id, user, db)
    pc = db.query(Paper).filter(Paper.subject_id == s.id).count()
    qc = db.query(Question).filter(Question.subject_id == s.id).count()
    return SubjectDetail(
        **SubjectOut.model_validate(s).model_dump(),
        paper_count=pc,
        question_count=qc,
        is_ready=(pc >= MIN_PAPERS),
    )


@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    s = _get_subject_or_404(subject_id, user, db)
    db.delete(s)
    db.commit()
