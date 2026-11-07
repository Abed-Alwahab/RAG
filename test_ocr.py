
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf
from unstructured.partition.pdf import partition_pdf

PDF_PATH = Path("data/Student-Guide-2024-2025-Ar.pdf")
OUTPUT_PATH = Path("ocr_output.txt")

if not PDF_PATH.exists():
    raise FileNotFoundError(f"File not found: {PDF_PATH}")

successful = 0
empty = []
failed = []
output = []

with pymupdf.open(PDF_PATH) as original:
    total_pages = len(original)

    print(f"Total pages: {total_pages}")

    with TemporaryDirectory() as temp_dir:
        for page_index in range(total_pages):
            page_number = page_index + 1
            temp_pdf = Path(temp_dir) / f"page_{page_number}.pdf"

            with pymupdf.open() as single_page:
                single_page.insert_pdf(
                    original,
                    from_page=page_index,
                    to_page=page_index
                )
                single_page.save(temp_pdf)

            print(f"Processing page {page_number}/{total_pages}...")

            try:
                elements = partition_pdf(
                    filename=str(temp_pdf),
                    strategy="ocr_only",
                    languages=["ara", "eng"]
                )

                text = "\n".join(
                    str(element).strip()
                    for element in elements
                    if str(element).strip()
                )

                if text:
                    successful += 1
                    status = "SUCCESS"
                else:
                    empty.append(page_number)
                    status = "EMPTY"

                output.append(
                    f"\n{'=' * 60}\n"
                    f"PAGE {page_number} - {status}\n"
                    f"{'=' * 60}\n"
                    f"{text}\n"
                )

            except Exception as error:
                failed.append(page_number)

                output.append(
                    f"\nPAGE {page_number} - FAILED\n"
                    f"Error: {error}\n"
                )

                print(f"ERROR on page {page_number}: {error}")

OUTPUT_PATH.write_text(
    "\n".join(output),
    encoding="utf-8"
)

print("\n" + "=" * 50)
print("OCR REPORT")
print("=" * 50)
print("Total pages:", total_pages)
print("Successful:", successful)
print("Empty pages:", empty)
print("Failed pages:", failed)
print("Saved to:", OUTPUT_PATH)
