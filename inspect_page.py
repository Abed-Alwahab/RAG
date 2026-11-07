
import pymupdf

pdf_path = (
    "data/تعليمات منح درجة البكالوريوس - "
    "الجامعة العربية الامريكية - 29-07-2026.pdf"
)

with pymupdf.open(pdf_path) as pdf:
    page = pdf[2]  # Page 3
    print(page.get_text())
