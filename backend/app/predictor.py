"""
predictor.py — Prediction engine.

Scoring formula (matches project spec):
    confidence = (
        0.40 * frequency_score    # how often across papers
      + 0.20 * recency_score      # appeared in recent papers
      + 0.20 * marks_score        # high-mark questions weighted up
      + 0.10 * topic_score        # topic appeared in multiple units
      + 0.10 * variety_score      # spread across different years (not just one year)
    )

Grouping:
    Uses TF-IDF + cosine similarity (scikit-learn) to cluster semantically
    similar questions into one canonical question, so "Explain Hall Effect"
    and "Derive Hall coefficient and explain Hall Effect" are merged before
    counting frequency.
"""
import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Question, Paper, Prediction, Subject

logger = logging.getLogger(__name__)

# Similarity threshold: questions with cosine similarity >= this are merged
SIMILARITY_THRESHOLD = 0.45

# How many top predictions to generate
TOP_N = 20


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation for comparison."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _year_from_paper(paper: Paper) -> int:
    return paper.year or 2020  # default if year not extracted


# ---------------------------------------------------------------------------
# Semantic grouping with TF-IDF cosine similarity
# ---------------------------------------------------------------------------

def _group_similar_questions(
    questions: list[Question],
) -> list[list[Question]]:
    """
    Group questions that ask about the same topic.
    Returns a list of groups; each group is a list of Question ORM objects.

    Uses scikit-learn TF-IDF + cosine similarity. Falls back to exact-text
    deduplication if sklearn is unavailable (shouldn't happen given requirements).
    """
    if not questions:
        return []

    texts = [_normalize(q.question_text) for q in questions]

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            min_df=1,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        sim_matrix   = cosine_similarity(tfidf_matrix)

        n = len(questions)
        visited  = [False] * n
        groups   = []

        for i in range(n):
            if visited[i]:
                continue
            group = [questions[i]]
            visited[i] = True
            for j in range(i + 1, n):
                if not visited[j] and sim_matrix[i, j] >= SIMILARITY_THRESHOLD:
                    group.append(questions[j])
                    visited[j] = True
            groups.append(group)

        return groups

    except Exception as e:
        logger.warning(f"TF-IDF grouping failed ({e}), falling back to exact dedup")
        # Fallback: group by identical normalized text
        seen: dict[str, list[Question]] = {}
        for q in questions:
            key = _normalize(q.question_text)[:80]
            seen.setdefault(key, []).append(q)
        return list(seen.values())


# ---------------------------------------------------------------------------
# Score computation
# ---------------------------------------------------------------------------

def _compute_scores(
    group:        list[Question],
    papers:       list[Paper],
    total_papers: int,
) -> dict:
    """
    Compute all component scores for a group of semantically similar questions.
    Returns a dict ready to populate a Prediction row.
    """
    paper_ids_in_group = {q.paper_id for q in group}
    paper_map          = {p.id: p for p in papers}

    years_seen = sorted({
        _year_from_paper(paper_map[pid])
        for pid in paper_ids_in_group
        if pid in paper_map
    })

    frequency      = len(paper_ids_in_group)
    max_year       = max(years_seen) if years_seen else 2020
    current_year   = datetime.now(timezone.utc).year

    # --- frequency score (0-100) ---
    frequency_score = (frequency / total_papers) * 100

    # --- recency score (0-100) ---
    # Questions from last 2 years get full marks; older ones decay linearly.
    recency_vals = []
    for yr in years_seen:
        age    = max(current_year - yr, 0)
        weight = max(0.0, 1.0 - age * 0.15)   # lose 15% per year
        recency_vals.append(weight)
    recency_score = (sum(recency_vals) / len(recency_vals)) * 100 if recency_vals else 0.0

    # --- marks score (0-100) ---
    marks_values = [q.marks for q in group if q.marks is not None]
    if marks_values:
        avg_marks    = sum(marks_values) / len(marks_values)
        marks_score  = min((avg_marks / 10.0) * 100, 100)  # 10-mark Q = 100%
    else:
        marks_score  = 40.0   # neutral default
        avg_marks    = None

    # --- topic_score: did this topic appear across multiple units/sections? ---
    units = {q.unit for q in group if q.unit}
    topic_score = min(len(units) * 25, 100)   # 4+ different units = 100

    # --- variety_score: spread across different years ---
    variety_score = min((len(years_seen) / max(total_papers, 1)) * 100, 100)

    # --- final weighted confidence ---
    confidence_score = (
        0.40 * frequency_score
      + 0.20 * recency_score
      + 0.20 * marks_score
      + 0.10 * topic_score
      + 0.10 * variety_score
    )
    confidence_score = min(round(confidence_score, 2), 99.9)  # cap at 99.9

    # Pick the longest/most descriptive question text as the canonical one
    canonical = max(group, key=lambda q: len(q.question_text))

    return {
        "question_text":    canonical.question_text,
        "topic":            canonical.topic,
        "unit":             canonical.unit,
        "frequency":        frequency,
        "frequency_score":  round(frequency_score, 2),
        "recency_score":    round(recency_score, 2),
        "marks_score":      round(marks_score, 2),
        "confidence_score": confidence_score,
        "source_years":     ",".join(str(y) for y in years_seen),
    }


# ---------------------------------------------------------------------------
# Main: run prediction for a subject
# ---------------------------------------------------------------------------

def run_prediction(subject_id: int, db: Session) -> list[Prediction]:
    """
    Runs the full prediction pipeline for a subject:
      1. Load all processed questions from all uploaded papers.
      2. Group semantically similar questions.
      3. Score each group.
      4. Rank by confidence.
      5. Persist Prediction rows (replace existing).
      6. Return top-N Prediction objects.
    """
    papers = (
        db.query(Paper)
        .filter(Paper.subject_id == subject_id, Paper.status == "processed")
        .all()
    )
    if not papers:
        logger.warning(f"No processed papers for subject {subject_id}")
        return []

    questions = (
        db.query(Question)
        .filter(Question.subject_id == subject_id)
        .all()
    )
    if not questions:
        logger.warning(f"No questions found for subject {subject_id}")
        return []

    total_papers = len(papers)
    logger.info(f"Running prediction: subject={subject_id}, papers={total_papers}, questions={len(questions)}")

    groups = _group_similar_questions(questions)
    logger.info(f"Grouped into {len(groups)} unique question clusters")

    # Score every group
    scored = []
    for group in groups:
        scores = _compute_scores(group, papers, total_papers)
        scored.append(scores)

    # Sort by confidence descending
    scored.sort(key=lambda s: s["confidence_score"], reverse=True)

    # Delete old predictions for this subject
    db.query(Prediction).filter(Prediction.subject_id == subject_id).delete()

    # Persist top-N
    saved: list[Prediction] = []
    for rank, score_dict in enumerate(scored[:TOP_N], start=1):
        pred = Prediction(
            subject_id=subject_id,
            rank=rank,
            **score_dict,
        )
        db.add(pred)
        saved.append(pred)

    db.commit()
    for p in saved:
        db.refresh(p)

    logger.info(f"Saved {len(saved)} predictions for subject {subject_id}")
    return saved


# ---------------------------------------------------------------------------
# Analysis report (used by /analysis endpoint)
# ---------------------------------------------------------------------------

def build_analysis_report(subject_id: int, db: Session) -> dict:
    """
    Build the structured analysis report for a subject (does not run
    predictions — just aggregates existing Question data).
    """
    papers = (
        db.query(Paper)
        .filter(Paper.subject_id == subject_id)
        .all()
    )
    questions = (
        db.query(Question)
        .filter(Question.subject_id == subject_id)
        .all()
    )

    if not questions:
        return {
            "papers_analysed":     len(papers),
            "total_questions":     0,
            "unique_topics":       0,
            "topic_frequency":     [],
            "question_frequency":  [],
            "unit_analysis":       [],
            "most_repeated_topic": None,
            "analysis_ready":      False,
        }

    # --- paper year map ---
    year_map = {p.id: (p.year or 2020) for p in papers}

    # --- topic frequency ---
    topic_papers: dict[str, set] = defaultdict(set)
    topic_years:  dict[str, list] = defaultdict(list)
    for q in questions:
        topic = q.topic or "Unknown"
        topic_papers[topic].add(q.paper_id)
        yr = year_map.get(q.paper_id, 2020)
        if yr not in topic_years[topic]:
            topic_years[topic].append(yr)

    total_papers = max(len(papers), 1)
    topic_freq = sorted(
        [
            {
                "topic":      t,
                "count":      len(pids),
                "percentage": round(len(pids) / total_papers * 100, 1),
                "years":      sorted(topic_years[t]),
            }
            for t, pids in topic_papers.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    # --- question-level frequency ---
    groups = _group_similar_questions(questions)
    q_freq = []
    for group in groups:
        pids  = {q.paper_id for q in group}
        yrs   = sorted({year_map.get(pid, 2020) for pid in pids})
        marks = next((q.marks for q in group if q.marks), None)
        canonical = max(group, key=lambda q: len(q.question_text))
        q_freq.append({
            "question_text": canonical.question_text[:200],
            "frequency":     len(pids),
            "percentage":    round(len(pids) / total_papers * 100, 1),
            "marks":         marks,
            "years":         yrs,
        })
    q_freq.sort(key=lambda x: x["frequency"], reverse=True)

    # --- unit analysis ---
    unit_qs: dict[str, list[Question]] = defaultdict(list)
    for q in questions:
        unit_qs[q.unit or "Unknown"].append(q)

    total_q = max(len(questions), 1)
    unit_analysis = []
    for unit, uqs in unit_qs.items():
        marks_vals = [q.marks for q in uqs if q.marks]
        avg_marks  = sum(marks_vals) / len(marks_vals) if marks_vals else 0.0
        topics     = list({q.topic for q in uqs if q.topic})[:5]
        unit_analysis.append({
            "unit":           unit,
            "question_count": len(uqs),
            "avg_marks":      round(avg_marks, 1),
            "percentage":     round(len(uqs) / total_q * 100, 1),
            "top_topics":     topics,
        })
    unit_analysis.sort(key=lambda x: x["question_count"], reverse=True)

    most_repeated = topic_freq[0]["topic"] if topic_freq else None

    return {
        "papers_analysed":     len(papers),
        "total_questions":     len(questions),
        "unique_topics":       len(topic_papers),
        "topic_frequency":     topic_freq[:15],
        "question_frequency":  q_freq[:20],
        "unit_analysis":       unit_analysis,
        "most_repeated_topic": most_repeated,
        "analysis_ready":      len(papers) >= 10,
    }
