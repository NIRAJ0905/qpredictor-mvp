"""
diagnose_ocr.py — Run this directly to find out exactly why OCR isn't working.

Usage:
    cd backend
    python diagnose_ocr.py "storage/papers/1/<some_file>.pdf"

Or with no argument, it will auto-find the first PDF in storage/papers/
"""
import sys
import os
import glob
from pathlib import Path

print("=" * 60)
print("STEP 1 — Checking imports")
print("=" * 60)

try:
    import fitz
    print(f"✅ PyMuPDF (fitz) imported OK — version {fitz.version}")
except ImportError as e:
    print(f"❌ PyMuPDF import FAILED: {e}")
    print("   Fix: pip install pymupdf")
    sys.exit(1)

try:
    import pytesseract
    print(f"✅ pytesseract imported OK")
except ImportError as e:
    print(f"❌ pytesseract import FAILED: {e}")
    print("   Fix: pip install pytesseract")
    sys.exit(1)

try:
    from PIL import Image
    print(f"✅ Pillow (PIL) imported OK")
except ImportError as e:
    print(f"❌ Pillow import FAILED: {e}")
    print("   Fix: pip install pillow")
    sys.exit(1)

print()
print("=" * 60)
print("STEP 2 — Checking Tesseract binary path")
print("=" * 60)

default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
env_path = os.getenv("TESSERACT_CMD")

if env_path:
    print(f"TESSERACT_CMD env var is set to: {env_path}")
    pytesseract.pytesseract.tesseract_cmd = env_path
elif os.path.exists(default_path):
    print(f"Found Tesseract at default path: {default_path}")
    pytesseract.pytesseract.tesseract_cmd = default_path
else:
    print(f"⚠️  Default path not found: {default_path}")
    print(f"   Current pytesseract.tesseract_cmd = {pytesseract.pytesseract.tesseract_cmd}")

print()
print("=" * 60)
print("STEP 3 — Testing Tesseract binary directly")
print("=" * 60)
try:
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract binary works! Version: {version}")
except Exception as e:
    print(f"❌ Tesseract binary call FAILED: {e}")
    print(f"   pytesseract is trying to call: {pytesseract.pytesseract.tesseract_cmd}")
    print(f"   Does this file actually exist? {os.path.exists(pytesseract.pytesseract.tesseract_cmd)}")
    sys.exit(1)

print()
print("=" * 60)
print("STEP 4 — Finding a real PDF to test")
print("=" * 60)

if len(sys.argv) > 1:
    pdf_path = sys.argv[1]
else:
    candidates = glob.glob("storage/papers/**/*.pdf", recursive=True)
    if not candidates:
        print("❌ No PDFs found in storage/papers/. Pass a path as argument:")
        print('   python diagnose_ocr.py "storage/papers/1/somefile.pdf"')
        sys.exit(1)
    pdf_path = candidates[0]
    print(f"Auto-selected: {pdf_path}")

if not os.path.exists(pdf_path):
    print(f"❌ File not found: {pdf_path}")
    sys.exit(1)

print(f"✅ Testing with: {pdf_path}")
print(f"   File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")

print()
print("=" * 60)
print("STEP 5 — Running PyMuPDF direct text extraction")
print("=" * 60)
try:
    doc = fitz.open(pdf_path)
    print(f"PDF has {len(doc)} pages")
    total_text = ""
    for i, page in enumerate(doc):
        t = page.get_text("text")
        total_text += t
        print(f"  Page {i+1}: {len(t)} chars extracted directly")
    doc.close()
    print(f"TOTAL direct text: {len(total_text)} chars")
    if len(total_text) < 100:
        print("⚠️  Very little/no text — this confirms it's a scanned/image PDF. OCR is needed.")
except Exception as e:
    print(f"❌ PyMuPDF extraction failed: {e}")

print()
print("=" * 60)
print("STEP 6 — Running OCR on page 1 only (quick test)")
print("=" * 60)
try:
    import io
    doc = fitz.open(pdf_path)
    page = doc[0]
    zoom = fitz.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=zoom)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    print(f"Rendered page 1 as image: {img.size[0]}x{img.size[1]} pixels")

    print("Running pytesseract.image_to_string() ... (may take a few seconds)")
    text = pytesseract.image_to_string(img, lang="eng")
    doc.close()

    print(f"✅ OCR SUCCESS — extracted {len(text)} characters from page 1")
    print()
    print("First 500 characters of OCR output:")
    print("-" * 60)
    print(text[:500])
    print("-" * 60)

except Exception as e:
    print(f"❌ OCR FAILED: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
