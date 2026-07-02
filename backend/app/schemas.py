"""
schemas.py — All Pydantic v2 schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===========================================================================
# Auth
# ===========================================================================

class SignupRequest(BaseModel):
    name:     str       = Field(min_length=1, max_length=120)
    email:    EmailStr
    password: str       = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    name:       str
    email:      str
    created_at: datetime


# ===========================================================================
# Subject
# ===========================================================================

class SubjectCreate(BaseModel):
    name:       str            = Field(min_length=1, max_length=200)
    code:       Optional[str]  = Field(default=None, max_length=50)
    department: Optional[str]  = Field(default=None, max_length=150)
    university: Optional[str]  = Field(default=None, max_length=200)
    semester:   Optional[str]  = Field(default=None, max_length=50)


class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    name:       str
    code:       Optional[str]
    department: Optional[str]
    university: Optional[str]
    semester:   Optional[str]
    created_at: datetime


class SubjectDetail(SubjectOut):
    paper_count:    int
    question_count: int
    is_ready:       bool   # True when >= 10 papers processed


# ===========================================================================
# Paper
# ===========================================================================

class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                int
    subject_id:        int
    year:              Optional[int]
    semester:          Optional[str]
    original_filename: str
    status:            str
    page_count:        Optional[int]
    uploaded_at:       datetime


class UploadResponse(BaseModel):
    subject_id:              int
    uploaded:                list[PaperOut]
    total_papers_for_subject: int
    min_required:            int
    ready_for_analysis:      bool
    message:                 str


# ===========================================================================
# Question
# ===========================================================================

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:            int
    paper_id:      int
    question_text: str
    question_num:  Optional[str]
    topic:         Optional[str]
    unit:          Optional[str]
    marks:         Optional[int]
    question_type: str


# ===========================================================================
# Analysis
# ===========================================================================

class TopicFrequency(BaseModel):
    topic:       str
    count:       int
    percentage:  float
    years:       list[int]


class QuestionFrequency(BaseModel):
    question_text: str
    frequency:     int
    percentage:    float
    marks:         Optional[int]
    years:         list[int]


class UnitAnalysis(BaseModel):
    unit:            str
    question_count:  int
    avg_marks:       float
    percentage:      float
    top_topics:      list[str]


class AnalysisReport(BaseModel):
    subject:              SubjectOut
    papers_analysed:      int
    total_questions:      int
    unique_topics:        int
    topic_frequency:      list[TopicFrequency]
    question_frequency:   list[QuestionFrequency]
    unit_analysis:        list[UnitAnalysis]
    most_repeated_topic:  Optional[str]
    analysis_ready:       bool


# ===========================================================================
# Prediction
# ===========================================================================

class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:               int
    question_text:    str
    topic:            Optional[str]
    unit:             Optional[str]
    frequency:        int
    frequency_score:  float
    confidence_score: float
    rank:             Optional[int]
    source_years:     Optional[str]


class PredictionReport(BaseModel):
    subject:           SubjectOut
    generated_at:      datetime
    total_predictions: int
    predictions:       list[PredictionOut]
    message:           str


# ===========================================================================
# Chat
# ===========================================================================

class ChatRequest(BaseModel):
    subject_id: int
    message:    str = Field(min_length=1, max_length=500)


class ChatResponse(BaseModel):
    reply:   str
    sources: list[str] = []
