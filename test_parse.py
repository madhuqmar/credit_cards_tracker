import pdfplumber
import sys
from pathlib import Path


def debug_citi_raw(pdf_path: str, page_num: int = 3):
    """
    Debug raw extracted text for a specific Citi statement page.
    Default: page 3 (1-based), where transactions live.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"{pdf_path} does not exist")

    with pdfplumber.open(pdf_path) as pdf:
        if page_num < 1 or page_num > len(pdf.pages):
            raise ValueError(f"PDF has {len(pdf.pages)} pages, cannot read page {page_num}")

        page = pdf.pages[page_num - 1]
        text = page.extract_text() or ""

    print("\n" + "=" * 80)
    print(f"RAW TEXT DEBUG: {pdf_path.name} | PAGE {page_num}")
    print("=" * 80)

    print("\n--- FULL PAGE TEXT ---\n")
    print(text)

    print("\n--- LINE-BY-LINE OUTPUT (WITH LINE NUMBERS) ---\n")
    for i, line in enumerate(text.split("\n"), start=1):
        print(f"{i:03d}: {repr(line)}")

    print("\n--- LINES CONTAINING KEYWORDS ---\n")
    KEYWORDS = ["taskrabbit", "gloss", "silver", "metro", "$"]

    for i, line in enumerate(text.split("\n"), start=1):
        if any(k in line.lower() for k in KEYWORDS):
            print(f"{i:03d}: {repr(line)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python debug_citi_raw.py <citi_statement.pdf> [page_num]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    page_num = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    debug_citi_raw(pdf_path, page_num)
