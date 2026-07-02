"""
pdf_processor.py — PDF text extraction and question parsing pipeline.

THREE-TIER EXTRACTION:
  1. PyMuPDF direct text extraction
  2. pdfplumber fallback
  3. OCR via pytesseract (for scanned PDFs)

PARSING STRATEGY (v2 — rebuilt for real OCR exam paper formats):
  Real-world Indian university question papers, especially MCQ sections,
  often use a tabular layout:
      <question text>          <Marks> <BL> <CO>
      (A) opt1   (B) opt2   (C) opt3   (D) opt4

  OCR flattens this into a single line, e.g.:
      "Communication barrier is anything... 1 2 1 8 (A) impedes (B) enhances..."

  The "1 2 1 8" is NOT the question number — it's Marks/BL/CO/something
  columns that got OCR'd inline. The old parser mistook these for question
  numbers, causing erratic numbering and polluted text.

  This version:
    - Splits each question at the FIRST occurrence of "(A)" — everything
      before is the question stem, everything after is MCQ options.
    - Strips trailing/leading digit clusters (the metadata columns) from
      the question stem instead of treating them as marks.
    - Detects question boundaries primarily via the "(A) ... (B) ... (C)
      ... (D) ..." option pattern, which is far more reliable in MCQ
      papers than numbering (which OCR frequently mangles or drops).
    - Caps question length hard at ~300 chars to prevent passage-swallowing
      merges; long reading-comprehension passages are kept as context but
      truncated for storage, not used to swallow subsequent questions.
    - Cleans common OCR character substitution errors.
"""
import re
import io
import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tesseract OCR binary location
# ---------------------------------------------------------------------------
_DEFAULT_WINDOWS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

try:
    import pytesseract
    tess_cmd = os.getenv("TESSERACT_CMD")
    if tess_cmd:
        pytesseract.pytesseract.tesseract_cmd = tess_cmd
    elif os.name == "nt" and Path(_DEFAULT_WINDOWS_PATH).exists():
        pytesseract.pytesseract.tesseract_cmd = _DEFAULT_WINDOWS_PATH
except ImportError:
    pass


@dataclass
class ParsedQuestion:
    question_num:  str
    question_text: str
    marks:         Optional[int] = None
    section:       Optional[str] = None
    question_type: str = "unknown"
    options:       Optional[list[str]] = None  # MCQ options A-D if detected


# ---------------------------------------------------------------------------
# Text extraction (unchanged 3-tier strategy)
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    text, pages = _pymupdf(file_path)
    chars_per_page = len(text) / max(pages, 1)
    logger.info(f"[Tier 1: PyMuPDF] {len(text)} chars, {pages} pages ({chars_per_page:.0f} chars/page)")

    if pages == 0 or chars_per_page < 100:
        text2, pages2 = _pdfplumber(file_path)
        chars_per_page2 = len(text2) / max(pages2, 1)
        logger.info(f"[Tier 2: pdfplumber] {len(text2)} chars, {pages2} pages ({chars_per_page2:.0f} chars/page)")
        if len(text2) > len(text):
            text, pages = text2, pages2
            chars_per_page = chars_per_page2

    if pages == 0 or chars_per_page < 100:
        logger.info("[Tier 3: OCR] Digital text layer is empty/sparse — running OCR")
        text3, pages3 = _ocr_extract(file_path)
        logger.info(f"[Tier 3: OCR] {len(text3)} chars, {pages3} pages")
        if len(text3) > len(text):
            text, pages = text3, pages3

    return text, pages


def _pymupdf(path: str) -> tuple[str, int]:
    try:
        import fitz
        doc = fitz.open(path)
        out = [page.get_text("text") for page in doc]
        n = len(out)
        doc.close()
        return "\n".join(out), n
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")
        return "", 0


def _pdfplumber(path: str) -> tuple[str, int]:
    try:
        import pdfplumber
        out = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text(layout=True) or page.extract_text() or ""
                out.append(t)
        return "\n".join(out), len(out)
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
        return "", 0


def _ocr_extract(path: str) -> tuple[str, int]:
    try:
        import fitz
        import pytesseract
        from PIL import Image

        doc = fitz.open(path)
        out = []
        zoom = fitz.Matrix(2.0, 2.0)

        for page_num, page in enumerate(doc):
            pix = page.get_pixmap(matrix=zoom)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            page_text = pytesseract.image_to_string(img, lang="eng")
            out.append(page_text)
            logger.info(f"  OCR page {page_num + 1}/{len(doc)}: {len(page_text)} chars")

        doc.close()
        return "\n".join(out), len(out)

    except ImportError as e:
        logger.error(f"OCR dependencies missing: {e}")
        return "", 0
    except Exception as e:
        logger.error(f"OCR extraction failed for {path}: {e}")
        return "", 0


# ---------------------------------------------------------------------------
# OCR text cleanup — fix common character substitution errors
# ---------------------------------------------------------------------------

_OCR_FIXES = [
    (re.compile(r'\bjs\b'), 'is'),
    (re.compile(r'\(0\)'), '(D)'),          # zero mistaken for D in options
    (re.compile(r'\(8\)(?=\s*[A-Za-z])'), '(B)'),  # 8 mistaken for B before a word
    (re.compile(r'[_~]{1,3}'), ' '),         # stray underscores/tildes from OCR noise
    (re.compile(r'\s{2,}'), ' '),            # collapse multiple spaces
    (re.compile(r'\bfulflling\b'), 'fulfilling'),
]

def _clean_ocr_text(text: str) -> str:
    for pattern, repl in _OCR_FIXES:
        text = pattern.sub(repl, text)
    return text.strip()


# ---------------------------------------------------------------------------
# Marks / metadata column stripping
# ---------------------------------------------------------------------------

# Matches trailing "1 2 1 8" style metadata column clusters (Marks/BL/CO/etc)
# that OCR flattens onto the question line — typically 2-4 single/double
# digit numbers right before "(A)" or at line end.
_METADATA_COLS_RE = re.compile(r'(?:\s+\d{1,2}){2,4}\s*(?=\(?[Aa]\)|$)')

_MARKS_RE = [
    re.compile(r'\[(\d{1,2})\s*[Mm]arks?\]'),
    re.compile(r'\((\d{1,2})\s*[Mm]arks?\)'),
    re.compile(r'\((\d{1,2})\s*[Mm]\)'),
]

def _extract_marks_explicit(text: str) -> Optional[int]:
    """Only matches EXPLICIT marks annotations like (8 Marks) — not bare numbers."""
    for pat in _MARKS_RE:
        m = pat.search(text)
        if m:
            v = int(m.group(1))
            if 1 <= v <= 20:
                return v
    return None


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

_SEC_RE = re.compile(
    r'(PART\s*[-:]?\s*[A-Z]|UNIT\s*[-:]?\s*[IVX\d]+|SECTION\s*[-:]?\s*[A-Z\d]+|MODULE\s*[-:]?\s*\d+)',
    re.IGNORECASE
)

def _find_section(text: str) -> Optional[str]:
    m = _SEC_RE.search(text)
    return m.group(0).strip().upper() if m else None


# ---------------------------------------------------------------------------
# Question type
# ---------------------------------------------------------------------------

_SHORT_KW = re.compile(r'\b(define|what is|what are|list|state|name|write a note|expand|enlist|give)\b', re.I)
_LONG_KW  = re.compile(r'\b(explain|describe|derive|discuss|elaborate|compare|differentiate|analyse|analyze|evaluate|justify|prove|illustrate|write in detail)\b', re.I)
_NUM_KW   = re.compile(r'\b(calculate|find|determine|compute|solve|obtain|estimate)\b', re.I)

def _qtype(text: str, marks: Optional[int], has_options: bool) -> str:
    if has_options: return "mcq"
    if _NUM_KW.search(text):  return "numerical"
    if marks:
        if marks <= 3: return "short"
        if marks >= 6: return "long"
    if _SHORT_KW.search(text): return "short"
    if _LONG_KW.search(text):  return "long"
    return "unknown"


# ---------------------------------------------------------------------------
# MCQ-aware parser (primary strategy for option-based papers)
# ---------------------------------------------------------------------------

# Matches an MCQ option block: (A) text (B) text (C) text (D) text
# Tolerant of OCR noise: extra spaces, missing parens replaced by similar chars
_OPTION_BLOCK_RE = re.compile(
    r'\(?[Aa]\)?[\s_]*(.+?)\s*'
    r'\(?[Bb]\)?[\s_]*(.+?)\s*'
    r'\(?[Cc]\)?[\s_]*(.+?)\s*'
    r'\(?[Dd]\)?[\s_]*(.+?)'
    r'(?=\(?[Aa]\)|$)',  # stop at next question's (A) or end of string
)

# Anchor used to SPLIT text into chunks, one per MCQ question.
# We split right before each "(A)" that is followed eventually by (B)(C)(D)
# on the same chunk — but simplest robust approach: split the whole text on
# the lookahead of "(A)" itself, since every question has exactly one.
_A_OPTION_SPLIT_RE = re.compile(r'(?=\(?[Aa]\)\s*[A-Za-z_])')


def _parse_mcq_questions(raw_text: str) -> list[ParsedQuestion]:
    """
    Splits OCR text into chunks, each ending right before the next "(A)"
    marker. Each chunk = [question stem][[metadata cols]](A)...(B)...(C)...(D)...
    """
    text = _clean_ocr_text(raw_text)

    # Quick check: does this text even look like an MCQ paper?
    a_count = len(re.findall(r'\(?[Aa]\)\s*[A-Za-z_]', text))
    if a_count < 2:
        return []  # Not enough option markers to be confident this is MCQ format

    results = []
    q_num = 1
    current_section = None
    last_end = 0
    # 4 options, repeatedly, consuming the string left to right.
    # CRITICAL: option D must stop at a newline OR the next "(A)" — without
    # the newline anchor, option D greedily swallows the next question's
    # entire stem too (since DOTALL/greedy .+? has nothing else to stop it
    # when two questions appear on consecutive lines with no blank line
    # between them, which is the normal OCR layout for MCQ blocks).
    pattern = re.compile(
        r'(?P<stem>.*?)'
        r'\(?[Aa]\)\s*(?P<opt_a>.+?)\s*'
        r'\(?[Bb]\)\s*(?P<opt_b>.+?)\s*'
        r'\(?[Cc]\)\s*(?P<opt_c>.+?)\s*'
        r'\(?[Dd]\)\s*(?P<opt_d>[^\n]+?)'
        r'(?=\n|\(?[Aa]\)\s*[A-Za-z_]|\Z)',
    )

    for m in pattern.finditer(text):
        # IMPORTANT: scan for section headers in the full slice of text
        # between the end of the previous match and the start of this one.
        # We can't rely solely on m.group('stem') here — Python's regex
        # engine tries successive start positions for the lazy .*?, which
        # can silently skip over a section header like "PART - A" sitting
        # just before the question if an earlier start position fails to
        # produce a full match.
        preceding_text = text[last_end:m.end()]
        sec = _find_section(preceding_text)
        if sec:
            current_section = sec

        stem = m.group('stem').strip()
        stem = _SEC_RE.sub('', stem).strip()

        # Strip leading question-number-ish tokens like "32.a.i." "1." "Q5)"
        stem = re.sub(r'^[\d.\s\(\)a-zA-Z]{0,12}(?=[A-Z][a-z])', '', stem) if len(stem) > 30 else stem

        # Strip trailing metadata columns (Marks/BL/CO digit clusters)
        stem = _METADATA_COLS_RE.sub('', stem).strip()
        stem = re.sub(r'\s+', ' ', stem).strip(' .')

        # Cap length — if stem is huge, it likely swallowed a passage;
        # keep only the LAST sentence-like portion (closest to the options,
        # which is almost always the actual question, not the passage).
        if len(stem) > 280:
            sentences = re.split(r'(?<=[.?])\s+', stem)
            stem = sentences[-1] if sentences else stem[-280:]
            stem = stem.strip()

        if len(stem) < 8:
            continue  # too short to be a real question after cleanup

        opts = [
            m.group('opt_a').strip(' .'),
            m.group('opt_b').strip(' .'),
            m.group('opt_c').strip(' .'),
            m.group('opt_d').strip(' .'),
        ]
        # Clean each option of trailing metadata noise
        opts = [re.sub(r'\s+', ' ', o)[:80] for o in opts]

        results.append(ParsedQuestion(
            question_num  = str(q_num),
            question_text = stem,
            marks         = _extract_marks_explicit(stem),
            section       = current_section,
            question_type = "mcq",
            options       = opts,
        ))
        q_num += 1
        last_end = m.end()

    return results


# ---------------------------------------------------------------------------
# Numbered long-answer parser (for PART B / descriptive sections)
# ---------------------------------------------------------------------------

_Q_RE = re.compile(
    r'^(?:'
    r'Q(?:uestion)?\.?\s*(\d{1,2})[.):\s]'
    r'|(\d{1,2})\s*[.)]\s+(?=[A-Z])'
    r'|\((\d{1,2})\)\s+(?=[A-Z])'
    r')',
    re.IGNORECASE
)

def _get_qnum(m: re.Match) -> str:
    return next(g for g in m.groups() if g is not None)


def _parse_numbered(raw_text: str) -> list[ParsedQuestion]:
    lines   = raw_text.splitlines()
    results = []
    current_section = None
    current_num     = None
    current_lines   = []

    def flush():
        if not current_num or not current_lines:
            return
        block = " ".join(l.strip() for l in current_lines if l.strip())
        if len(block) < 12:
            return
        m = _extract_marks_explicit(block)
        txt = re.sub(r'\[?\d{1,2}\s*[Mm]arks?\]?', '', block).strip()
        txt = re.sub(r'\s+', ' ', txt).strip()
        if len(txt) < 10 or len(txt) > 400:
            return
        results.append(ParsedQuestion(
            question_num  = current_num,
            question_text = txt,
            marks         = m,
            section       = current_section,
            question_type = _qtype(txt, m, has_options=False),
        ))

    for line in lines:
        s = line.strip()
        if not s:
            continue

        sec = _find_section(s)
        if sec and len(s) < 30:  # standalone header line, not embedded in a question
            flush()
            current_num, current_lines = None, []
            current_section = sec
            continue

        m = _Q_RE.match(s)
        if m:
            flush()
            current_num   = _get_qnum(m)
            rest          = s[m.end():].strip()
            current_lines = [rest] if rest else []
        elif current_num is not None:
            current_lines.append(s)

    flush()
    return results


# ---------------------------------------------------------------------------
# Main entry point — tries MCQ parser first, then numbered, merges results
# ---------------------------------------------------------------------------

def parse_questions(raw_text: str) -> list[ParsedQuestion]:
    if not raw_text or not raw_text.strip():
        return []

    cleaned = _clean_ocr_text(raw_text)

    mcq_results = _parse_mcq_questions(cleaned)
    logger.info(f"MCQ parser found {len(mcq_results)} questions")

    numbered_results = _parse_numbered(cleaned)
    logger.info(f"Numbered parser found {len(numbered_results)} questions")

    # Use whichever found more — for a paper that's mostly MCQ, the MCQ
    # parser will dominate; for mostly-descriptive papers, numbered wins.
    # If both found a reasonable amount, prefer MCQ since it's more precise
    # when options are present (less prone to false splits).
    if len(mcq_results) >= 3:
        combined = mcq_results
        # Append any numbered (PART B style) questions that don't overlap
        mcq_texts_lower = {q.question_text[:40].lower() for q in mcq_results}
        for nq in numbered_results:
            if nq.question_text[:40].lower() not in mcq_texts_lower and len(nq.question_text) < 280:
                combined.append(nq)
    else:
        combined = numbered_results if numbered_results else mcq_results

    logger.info(f"Total questions after merge: {len(combined)}")
    return combined


# ---------------------------------------------------------------------------
# Topic extraction
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "the","a","an","and","or","of","to","in","is","are","be","with","for",
    "on","at","by","from","this","that","it","its","what","how","why","when",
    "where","which","who","explain","describe","define","derive","discuss",
    "state","write","give","calculate","find","determine","solve","obtain",
    "list","name","compare","differentiate","elaborate","evaluate","justify",
    "prove","using","suitable","example","examples","detail","following",
    "between","various","important","marks","briefly","short","note","any",
    "two","three","four","five","with","also","their","these","those",
    "following","followings","correct","one","sentence","sentences",
}

def extract_topic_keywords(question_text: str, top_n: int = 3) -> str:
    caps = re.findall(r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', question_text)
    if caps:
        return caps[0][:60]

    upper = re.findall(r'\b[A-Z]{2,}\b', question_text)
    if upper:
        return upper[0]

    words    = re.sub(r'[^\w\s]', ' ', question_text).split()
    keywords = [w for w in words if len(w) > 3 and w.lower() not in _STOPWORDS]
    if keywords:
        return " ".join(keywords[:top_n]).title()

    return "General"
