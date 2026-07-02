"""
Paper upload and processing endpoints.

POST /api/subjects/{subject_id}/upload-papers
    Upload one or more PDFs. Each file is validated, saved to disk,
    a Paper row is created, and processing is triggered synchronously.

POST /api/subjects/{subject_id}/process
    Re-trigger extraction for all uploaded-but-unprocessed papers.

GET  /api/subjects/{subject_id}/papers
    List all papers for a subject.

DELETE /api/subjects/{subject_id}/papers/{paper_id}
    Remove a single paper and its questions.
"""
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User, Subject, Paper, Question
from app.pdf_processor import extract_text_from_pdf, parse_questions, extract_topic_keywords
from app.schemas import PaperOut, UploadResponse

logger = logging.getLogger(__name__)

router     = APIRouter(prefix="/api/subjects", tags=["papers"])
STORAGE    = Path(__file__).resolve().parent.parent.parent / "storage" / "papers"
MIN_PAPERS = 10
MAX_MB     = 30


def _get_subject_or_404(subject_id: int, user: User, db: Session) -> Subject:
    subj = db.get(Subject, subject_id)
    if not subj or subj.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Subject not found.")
    return subj


def _validate_pdf(file: UploadFile, data: bytes) -> None:
    """Extension + magic-byte + size checks."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, f"'{file.filename}' is not a PDF file.")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(400, f"'{file.filename}' is not a valid PDF (bad magic bytes).")
    if len(data) > MAX_MB * 1024 * 1024:
        raise HTTPException(400, f"'{file.filename}' exceeds the {MAX_MB} MB size limit.")
    if len(data) == 0:
        raise HTTPException(400, f"'{file.filename}' is empty.")


def _save_to_disk(data: bytes, subject_id: int, filename: str) -> Path:
    """Save raw bytes to storage/papers/<subject_id>/. Returns the saved path."""
    dest_dir = STORAGE / str(subject_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{Path(filename).name}"
    dest = dest_dir / safe_name
    dest.write_bytes(data)
    return dest


def _process_paper(paper: Paper, db: Session) -> None:
    """
    Extract questions from a single Paper, persist them, and mark the
    paper as processed (or failed). Called synchronously in MVP.
    """
    logger.info(f"=== Processing paper {paper.id}: {paper.original_filename} ===")
    paper.status = "processing"
    db.commit()
    try:
        # Delete any existing questions for this paper first (handles re-process)
        deleted = db.query(Question).filter(Question.paper_id == paper.id).delete()
        if deleted:
            logger.info(f"Deleted {deleted} old question(s) before re-processing")
        db.commit()

        logger.info(f"Calling extract_text_from_pdf({paper.file_path!r})")
        text, page_count = extract_text_from_pdf(paper.file_path)
        logger.info(f"extract_text_from_pdf returned: {len(text)} chars, {page_count} pages")
        paper.page_count = page_count

        logger.info(f"Calling parse_questions() on {len(text)} chars of text")
        parsed = parse_questions(text)
        logger.info(f"parse_questions returned {len(parsed)} ParsedQuestion objects")

        if not parsed:
            logger.warning(
                f"No questions found in paper {paper.id} ({paper.original_filename}). "
                f"Extracted text length was {len(text)} chars. "
                f"First 200 chars of extracted text: {text[:200]!r}"
            )

        for pq in parsed:
            topic = extract_topic_keywords(pq.question_text)
            unit  = pq.section or "Unknown"
            q = Question(
                paper_id      = paper.id,
                subject_id    = paper.subject_id,
                question_text = pq.question_text,
                question_num  = pq.question_num,
                topic         = topic,
                unit          = unit,
                marks         = pq.marks,
                question_type = pq.question_type,
            )
            db.add(q)

        paper.status = "processed"
        db.commit()
        logger.info(f"Paper {paper.id}: SAVED {len(parsed)} questions to database")

    except Exception as e:
        logger.error(f"Processing FAILED for paper {paper.id}: {type(e).__name__}: {e}", exc_info=True)
        paper.status = "failed"
        db.commit()
        raise


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/{subject_id}/upload-papers", response_model=UploadResponse, status_code=201)
def upload_papers(
    subject_id: int,
    files:    list[UploadFile] = File(..., description="One or more PDF files"),
    year:     int | None       = Form(default=None),
    semester: str | None       = Form(default=None),
    db:       Session          = Depends(get_db),
    user:     User             = Depends(get_current_user),
):
    _get_subject_or_404(subject_id, user, db)

    if not files:
        raise HTTPException(400, "No files provided.")

    saved_papers: list[Paper] = []
    processing_errors: list[str] = []

    for upload in files:
        data = upload.file.read()
        try:
            _validate_pdf(upload, data)
        except HTTPException as exc:
            processing_errors.append(exc.detail)
            continue

        dest = _save_to_disk(data, subject_id, upload.filename)
        paper = Paper(
            subject_id=subject_id,
            year=year,
            semester=semester,
            original_filename=upload.filename,
            file_path=str(dest),
            status="uploaded",
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        # Process synchronously in MVP
        try:
            _process_paper(paper, db)
        except Exception:
            pass  # status already set to "failed" inside _process_paper

        db.refresh(paper)
        saved_papers.append(paper)

    if not saved_papers and processing_errors:
        raise HTTPException(400, "; ".join(processing_errors))

    total = db.query(Paper).filter(Paper.subject_id == subject_id).count()
    ready = total >= MIN_PAPERS

    parts = [f"{len(saved_papers)} paper(s) uploaded and processed."]
    if processing_errors:
        parts.append(f"Skipped {len(processing_errors)} invalid file(s): {'; '.join(processing_errors)}")
    parts.append(f"{total}/{MIN_PAPERS} papers on file.")
    if ready:
        parts.append("Minimum reached — run /analysis and /predictions now.")

    return UploadResponse(
        subject_id=subject_id,
        uploaded=[PaperOut.model_validate(p) for p in saved_papers],
        total_papers_for_subject=total,
        min_required=MIN_PAPERS,
        ready_for_analysis=ready,
        message=" ".join(parts),
    )


@router.post("/{subject_id}/process", status_code=200)
def reprocess_papers(
    subject_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    """
    Re-run extraction on ALL papers for a subject (not just failed ones) —
    this is important after upgrading pdf_processor.py (e.g. adding OCR),
    since old papers were processed with the OLD code and need a fresh pass.
    """
    _get_subject_or_404(subject_id, user, db)
    papers = (
        db.query(Paper)
        .filter(Paper.subject_id == subject_id)
        .all()
    )
    logger.info(f"Reprocessing {len(papers)} paper(s) for subject {subject_id}")

    results = {"reprocessed": 0, "failed": 0, "total_questions_found": 0}
    for p in papers:
        try:
            _process_paper(p, db)
            q_count = db.query(Question).filter(Question.paper_id == p.id).count()
            results["reprocessed"] += 1
            results["total_questions_found"] += q_count
        except Exception:
            results["failed"] += 1

    logger.info(f"Reprocess complete: {results}")
    return results


@router.get("/{subject_id}/papers", response_model=list[PaperOut])
def list_papers(
    subject_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    _get_subject_or_404(subject_id, user, db)
    return db.query(Paper).filter(Paper.subject_id == subject_id).all()


@router.delete("/{subject_id}/papers/{paper_id}", status_code=204)
def delete_paper(
    subject_id: int,
    paper_id:   int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    _get_subject_or_404(subject_id, user, db)
    paper = db.get(Paper, paper_id)
    if not paper or paper.subject_id != subject_id:
        raise HTTPException(404, "Paper not found.")
    db.delete(paper)
    db.commit()
