"""
models.py — All SQLAlchemy ORM models in one file (clean for MVP).

Rules:
- No PostgreSQL-specific types (UUID, ENUM) — everything is String/Integer/Float/Text.
- Primary keys are plain auto-increment integers for simplicity.
- Status fields are plain String columns with documented allowed values.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship

from app.database import Base


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(120), nullable=False)
    email         = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=_now, nullable=False)

    subjects = relationship("Subject", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

class Subject(Base):
    __tablename__ = "subjects"

    id         = Column(Integer, primary_key=True, index=True)
    owner_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name       = Column(String(200), nullable=False)
    code       = Column(String(50), nullable=True)
    department = Column(String(150), nullable=True)
    university = Column(String(200), nullable=True)
    semester   = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    owner  = relationship("User", back_populates="subjects")
    papers = relationship("Paper", back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject id={self.id} name={self.name}>"


# ---------------------------------------------------------------------------
# Paper
# ---------------------------------------------------------------------------
# status allowed values: "uploaded" | "processing" | "processed" | "failed"

class Paper(Base):
    __tablename__ = "papers"

    id                = Column(Integer, primary_key=True, index=True)
    subject_id        = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    year              = Column(Integer, nullable=True)
    semester          = Column(String(50), nullable=True)
    original_filename = Column(String(255), nullable=False)
    file_path         = Column(String(500), nullable=False)
    status            = Column(String(20), default="uploaded", nullable=False)
    page_count        = Column(Integer, nullable=True)
    uploaded_at       = Column(DateTime, default=_now, nullable=False)

    subject   = relationship("Subject", back_populates="papers")
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Paper id={self.id} file={self.original_filename} status={self.status}>"


# ---------------------------------------------------------------------------
# Question
# ---------------------------------------------------------------------------
# question_type allowed values: "long" | "short" | "mcq" | "numerical" | "unknown"

class Question(Base):
    __tablename__ = "questions"

    id            = Column(Integer, primary_key=True, index=True)
    paper_id      = Column(Integer, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    subject_id    = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_num  = Column(String(20), nullable=True)   # e.g. "Q3", "21"
    unit          = Column(String(150), nullable=True)
    topic         = Column(String(200), nullable=True)
    marks         = Column(Integer, nullable=True)
    question_type = Column(String(20), default="unknown", nullable=False)
    created_at    = Column(DateTime, default=_now, nullable=False)

    paper   = relationship("Paper", back_populates="questions")
    subject = relationship("Subject")

    def __repr__(self):
        return f"<Question id={self.id} text='{self.question_text[:40]}...'>"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

class Prediction(Base):
    __tablename__ = "predictions"

    id               = Column(Integer, primary_key=True, index=True)
    subject_id       = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    question_text    = Column(Text, nullable=False)     # canonical (de-duplicated) question
    topic            = Column(String(200), nullable=True)
    unit             = Column(String(150), nullable=True)
    frequency        = Column(Integer, default=0)        # how many papers it appeared in
    frequency_score  = Column(Float, default=0.0)        # frequency / total_papers * 100
    recency_score    = Column(Float, default=0.0)        # weighted toward recent years
    marks_score      = Column(Float, default=0.0)        # avg marks weight
    confidence_score = Column(Float, default=0.0)        # final weighted score 0–100
    rank             = Column(Integer, nullable=True)
    source_years     = Column(String(200), nullable=True) # e.g. "2019,2021,2023"
    created_at       = Column(DateTime, default=_now, nullable=False)

    subject = relationship("Subject")

    def __repr__(self):
        return f"<Prediction id={self.id} rank={self.rank} conf={self.confidence_score:.1f}>"
