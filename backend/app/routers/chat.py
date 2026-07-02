"""
Chat endpoint — answers questions about a subject's uploaded papers.

This is an intentionally simple rule-based chatbot for the MVP.
It queries the predictions and analysis data and generates natural-language
answers without an external LLM (no API key needed, works offline).

Phase 3 will replace this with a proper RAG pipeline.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import Counter

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Subject, Prediction, Question, Paper
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_subject_or_404(subject_id: int, user: User, db: Session) -> Subject:
    s = db.get(Subject, subject_id)
    if not s or s.owner_id != user.id:
        raise HTTPException(404, "Subject not found.")
    return s


def _intent(msg: str) -> str:
    m = msg.lower()
    if any(w in m for w in ["study first", "start", "begin", "priority", "important first"]):
        return "study_order"
    if any(w in m for w in ["unit", "chapter", "module"]):
        return "unit_query"
    if any(w in m for w in ["predict", "likely", "probably", "come", "appear", "expected"]):
        return "predictions"
    if any(w in m for w in ["topic", "subject", "repeated", "frequent", "most"]):
        return "top_topics"
    if any(w in m for w in ["revision", "plan", "schedule", "prepare", "strategy"]):
        return "revision_plan"
    if any(w in m for w in ["mcq", "multiple choice", "short"]):
        return "mcq"
    if any(w in m for w in ["long", "descriptive", "essay", "8 mark", "10 mark"]):
        return "long_questions"
    return "general"


def _extract_unit_num(msg: str) -> str | None:
    import re
    m = re.search(r'unit\s*(\d+|[ivxIVX]+)', msg, re.IGNORECASE)
    return m.group(1).upper() if m else None


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    db:      Session = Depends(get_db),
    user:    User    = Depends(get_current_user),
):
    s = _get_subject_or_404(payload.subject_id, user, db)

    preds = (
        db.query(Prediction)
        .filter(Prediction.subject_id == payload.subject_id)
        .order_by(Prediction.rank)
        .all()
    )
    questions = (
        db.query(Question)
        .filter(Question.subject_id == payload.subject_id)
        .all()
    )
    papers = (
        db.query(Paper)
        .filter(Paper.subject_id == payload.subject_id)
        .all()
    )

    intent  = _intent(payload.message)
    sources = []

    if not questions:
        return ChatResponse(
            reply="No papers have been processed yet for this subject. "
                  "Please upload and process at least 10 previous year papers first.",
            sources=[],
        )

    # --- study_order ---
    if intent == "study_order":
        if not preds:
            reply = "Run predictions first (POST /predictions), then I can tell you what to study first."
        else:
            top3 = preds[:3]
            items = "\n".join(
                f"  {p.rank}. {p.topic or p.question_text[:60]} (confidence: {p.confidence_score:.0f}%)"
                for p in top3
            )
            reply = (
                f"Based on {len(papers)} papers analysed, start with these high-priority topics:\n"
                f"{items}\n\n"
                f"These appeared most frequently and in recent papers."
            )
            sources = [p.topic for p in top3 if p.topic]

    # --- unit query ---
    elif intent == "unit_query":
        unit_num = _extract_unit_num(payload.message)
        unit_qs  = [
            q for q in questions
            if unit_num and unit_num in (q.unit or "").upper()
        ] if unit_num else []

        if not unit_num:
            units = Counter(q.unit for q in questions if q.unit)
            top   = units.most_common(5)
            reply = (
                "The most question-heavy units are:\n"
                + "\n".join(f"  {u}: {c} question(s)" for u, c in top)
                + "\n\nAsk me about a specific unit, e.g. 'important topics in Unit 2'."
            )
        elif unit_qs:
            topics = Counter(q.topic for q in unit_qs if q.topic).most_common(5)
            reply  = (
                f"Unit {unit_num} has {len(unit_qs)} question(s) across {len(papers)} papers.\n"
                "Top topics:\n"
                + "\n".join(f"  • {t}: {c}x" for t, c in topics)
            )
            sources = [t for t, _ in topics]
        else:
            reply = f"No questions found for Unit {unit_num}. Try another unit number."

    # --- predictions ---
    elif intent == "predictions":
        if not preds:
            reply = "No predictions yet. POST to /predictions to generate them first."
        else:
            top5  = preds[:5]
            items = "\n".join(
                f"  {p.rank}. [{p.confidence_score:.0f}%] {p.question_text[:80]}"
                for p in top5
            )
            reply = (
                f"Top {len(top5)} predicted questions for {s.name}:\n{items}\n\n"
                f"These are ranked by a weighted score: frequency (40%), recency (20%), "
                f"marks weight (20%), topic spread (10%), year variety (10%)."
            )
            sources = [p.topic for p in top5 if p.topic]

    # --- top_topics ---
    elif intent == "top_topics":
        topics = Counter(q.topic for q in questions if q.topic).most_common(8)
        if not topics:
            reply = "Topics haven't been extracted yet. Ensure papers are fully processed."
        else:
            items  = "\n".join(f"  • {t}: appeared {c} time(s)" for t, c in topics)
            reply  = f"Most frequent topics in {s.name}:\n{items}"
            sources = [t for t, _ in topics[:5]]

    # --- revision plan ---
    elif intent == "revision_plan":
        if not preds:
            reply = "Generate predictions first, then I can build a revision plan."
        else:
            high   = [p for p in preds if p.confidence_score >= 70][:5]
            medium = [p for p in preds if 50 <= p.confidence_score < 70][:3]
            low    = [p for p in preds if p.confidence_score < 50][:2]

            def fmt(lst):
                return "\n".join(f"    • {p.topic or p.question_text[:50]}" for p in lst) or "    (none)"

            reply = (
                f"Suggested revision plan for {s.name} ({len(papers)} papers analysed):\n\n"
                f"📌 HIGH PRIORITY (do these first):\n{fmt(high)}\n\n"
                f"📘 MEDIUM PRIORITY:\n{fmt(medium)}\n\n"
                f"📄 LOW PRIORITY (time permitting):\n{fmt(low)}"
            )

    # --- mcq ---
    elif intent == "mcq":
        mcq_qs = [q for q in questions if q.question_type == "mcq"]
        reply  = (
            f"Found {len(mcq_qs)} MCQ-type questions across {len(papers)} papers."
            if mcq_qs else
            "No MCQ questions detected in the uploaded papers. "
            "The papers may not contain multiple-choice sections, or the format wasn't detected."
        )

    # --- long questions ---
    elif intent == "long_questions":
        long_qs = [q for q in questions if q.question_type == "long"]
        if long_qs:
            topics  = Counter(q.topic for q in long_qs if q.topic).most_common(5)
            items   = "\n".join(f"  • {t}: {c}x" for t, c in topics)
            reply   = (
                f"Found {len(long_qs)} long/descriptive questions. Top topics:\n{items}"
            )
            sources = [t for t, _ in topics]
        else:
            reply = "No long-answer questions detected. Try re-processing your papers."

    # --- general ---
    else:
        topic_count = len({q.topic for q in questions if q.topic})
        reply = (
            f"I can answer questions about {s.name} based on {len(papers)} uploaded paper(s) "
            f"and {len(questions)} extracted question(s) covering {topic_count} topic(s).\n\n"
            "Try asking:\n"
            "  • 'What should I study first?'\n"
            "  • 'What are the most repeated topics?'\n"
            "  • 'What questions are likely in Unit 3?'\n"
            "  • 'Give me a revision plan'\n"
            "  • 'What are the top predicted questions?'"
        )

    return ChatResponse(reply=reply, sources=list(set(sources)))
