
import re
from pathlib import Path

import pymupdf

DATA_DIR = Path("data")
OCR_FILE = Path("ocr_output.txt")
OCR_SOURCE = "Student-Guide-2024-2025-Ar.pdf"


def load_ocr_pages():
    if not OCR_FILE.exists():
        raise FileNotFoundError(
            f"OCR file not found: {OCR_FILE}"
        )

    content = OCR_FILE.read_text(encoding="utf-8")

    pattern = re.compile(
        r"PAGE\s+(\d+)\s+-\s+(SUCCESS|EMPTY|FAILED)"
    )

    matches = list(pattern.finditer(content))
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

        text = content[start:end]
        text = re.sub(r"^[=\s]+", "", text)
        text = re.sub(r"[=\s]+$", "", text)

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


def load_pdfs():
    documents = []

    for pdf_path in sorted(DATA_DIR.glob("*.pdf")):
        print(f"Processing: {pdf_path.name}")

        if pdf_path.name == OCR_SOURCE:
            ocr_pages = load_ocr_pages()
            documents.extend(ocr_pages)
            print(f"OCR pages loaded: {len(ocr_pages)}")
            continue

        with pymupdf.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text().strip()

                if text:
                    documents.append({
                        "text": text,
                        "source": pdf_path.name,
                        "page": page_number,
                        "method": "pymupdf"
                    })

    print(f"\nTotal extracted pages: {len(documents)}")
    return documents


if __name__ == "__main__":
    docs = load_pdfs()

    for doc in docs[:3]:
        print(
            doc["source"],
            "Page:", doc["page"],
            "Method:", doc["method"]
        )
