
import re
from pathlib import Path

import pymupdf


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

OCR_FILE = BASE_DIR / "ocr_output.txt"

OCR_SOURCE = "Student-Guide-2024-2025-Ar.pdf"


# ==========================================
# LOAD CACHED OCR PAGES
# ==========================================

def load_ocr_pages():
    if not OCR_FILE.is_file():
        raise FileNotFoundError(
            f"OCR file not found: {OCR_FILE}"
        )

    content = OCR_FILE.read_text(encoding="utf-8")

    pattern = re.compile(
        r"PAGE\s+(\d+)\s+-\s+(SUCCESS|EMPTY|FAILED)"
    )

    matches = list(pattern.finditer(content))

    if not matches:
        raise ValueError(
            "No valid OCR page markers found in ocr_output.txt"
        )

    pages = []

    for i, match in enumerate(matches):
        page_number = int(match.group(1))
        status = match.group(2)

        start = match.end()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(content)
        )

        text = content[start:end].strip("= \t\r\n")

        if status == "FAILED":
            raise RuntimeError(
                f"OCR failed on page {page_number}"
            )

        if status == "SUCCESS" and text:
            pages.append({
                "text": text,
                "source": OCR_SOURCE,
                "page": page_number,
                "method": "unstructured_ocr"
            })

    return pages


# ==========================================
# LOAD ALL PDF DOCUMENTS
# ==========================================

def load_pdfs():
    if not DATA_DIR.is_dir():
        raise FileNotFoundError(
            f"PDF directory not found: {DATA_DIR}"
        )

    pdf_files = sorted(DATA_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {DATA_DIR}"
        )

    documents = []

    print(
        f"\nFound {len(pdf_files)} PDF files.\n",
        flush=True
    )

    for pdf_path in pdf_files:
        print(
            f"[START] Processing: {pdf_path.name}",
            flush=True
        )

        pages_before = len(documents)

        if pdf_path.name == OCR_SOURCE:
            ocr_pages = load_ocr_pages()
            documents.extend(ocr_pages)

        else:
            with pymupdf.open(pdf_path) as pdf:
                for page_number, page in enumerate(
                    pdf,
                    start=1
                ):
                    text = page.get_text().strip()

                    if text:
                        documents.append({
                            "text": text,
                            "source": pdf_path.name,
                            "page": page_number,
                            "method": "pymupdf"
                        })

        extracted = len(documents) - pages_before

        print(
            f"[DONE] {pdf_path.name}: "
            f"{extracted} pages extracted.\n",
            flush=True
        )

    print("=" * 50)
    print(f"Total PDF files: {len(pdf_files)}")
    print(f"Total extracted pages: {len(documents)}")
    print("=" * 50)

    return documents


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":
    docs = load_pdfs()

    for doc in docs[:3]:
        print(
            doc["source"],
            "| Page:", doc["page"],
            "| Method:", doc["method"]
        )
