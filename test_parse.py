import pdfplumber
import sys
import re
from pathlib import Path
from typing import List, Optional

DEFAULT_KEYWORDS = [
    "$",
    "payment",
    "payments",
    "credit",
    "credits",
    "purchase",
    "purchases",
    "new balance",
    "statement balance",
    "account summary",
    "total",
]

AMOUNT_RE = re.compile(r"[-+()]?\$[\d,]+\.\d{2}")
DATE_RE = re.compile(
    r"(\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b)|(\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b\s+\d{1,2}\b)",
    re.IGNORECASE,
)

def parse_pages_arg(pages_arg: str, num_pages: int) -> List[int]:
    """
    Supports:
      "3"         -> [3]
      "1,3,5"     -> [1,3,5]
      "2-4"       -> [2,3,4]
      "1,2-4,7"   -> [1,2,3,4,7]
    Pages are 1-based in CLI, returned list is 1-based.
    """
    pages = set()
    for part in pages_arg.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a.strip())
            end = int(b.strip())
            for p in range(start, end + 1):
                pages.add(p)
        else:
            pages.add(int(part))
    # clamp to document
    pages = [p for p in sorted(pages) if 1 <= p <= num_pages]
    return pages

def debug_pdf_raw(
    pdf_path: str,
    pages: Optional[List[int]] = None,
    keywords: Optional[List[str]] = None,
    show_full_text: bool = True,
    show_line_numbers: bool = True,
    show_keyword_hits: bool = True,
    show_auto_hits: bool = True,
    out_path: Optional[str] = None,
):
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"{pdf_path} does not exist")

    kw = [k.lower() for k in (keywords or DEFAULT_KEYWORDS)]

    output_lines = []
    def emit(s: str = ""):
        output_lines.append(s)

    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        if pages is None:
            pages_to_read = [1]  # default to page 1
        else:
            pages_to_read = pages

        emit("\n" + "=" * 80)
        emit(f"RAW PDF DEBUG: {pdf_path.name}")
        emit(f"PAGES: {pages_to_read} (of {total_pages})")
        emit("=" * 80)

        for page_num in pages_to_read:
            if page_num < 1 or page_num > total_pages:
                emit(f"\n[SKIP] Page {page_num} out of range (1..{total_pages})")
                continue

            page = pdf.pages[page_num - 1]
            text = page.extract_text() or ""

            emit("\n" + "=" * 80)
            emit(f"RAW TEXT DEBUG: {pdf_path.name} | PAGE {page_num}")
            emit("=" * 80)

            if show_full_text:
                emit("\n--- FULL PAGE TEXT ---\n")
                emit(text)

            lines = text.split("\n")

            if show_line_numbers:
                emit("\n--- LINE-BY-LINE OUTPUT (WITH LINE NUMBERS) ---\n")
                for i, line in enumerate(lines, start=1):
                    emit(f"{i:03d}: {repr(line)}")

            if show_keyword_hits:
                emit("\n--- LINES CONTAINING KEYWORDS ---\n")
                for i, line in enumerate(lines, start=1):
                    l = line.lower()
                    if any(k in l for k in kw):
                        emit(f"{i:03d}: {repr(line)}")

            if show_auto_hits:
                emit("\n--- AUTO-DETECTED 'INTERESTING' LINES (DATES / AMOUNTS) ---\n")
                for i, line in enumerate(lines, start=1):
                    if AMOUNT_RE.search(line) or DATE_RE.search(line):
                        emit(f"{i:03d}: {repr(line)}")

    final_output = "\n".join(output_lines)

    if out_path:
        Path(out_path).write_text(final_output, encoding="utf-8")
        print(f"Wrote debug output to: {out_path}")

    print(final_output)


if __name__ == "__main__":
    # Usage examples:
    #   python debug_pdf_raw.py statement.pdf
    #   python debug_pdf_raw.py statement.pdf --page 3
    #   python debug_pdf_raw.py statement.pdf --pages 1,3,5
    #   python debug_pdf_raw.py statement.pdf --pages 2-4 --keywords "uber,venmo,$"
    #   python debug_pdf_raw.py statement.pdf --all --out debug.txt

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python debug_pdf_raw.py <statement.pdf> [--page N | --pages A,B-C | --all] "
              "[--keywords \"k1,k2,k3\"] [--out debug.txt]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    args = sys.argv[2:]

    page = None
    pages_arg = None
    all_pages = False
    keywords_arg = None
    out_path = None

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--page":
            i += 1
            page = int(args[i])
        elif a == "--pages":
            i += 1
            pages_arg = args[i]
        elif a == "--all":
            all_pages = True
        elif a == "--keywords":
            i += 1
            keywords_arg = args[i]
        elif a == "--out":
            i += 1
            out_path = args[i]
        else:
            raise ValueError(f"Unknown argument: {a}")
        i += 1

    # Determine pages list
    with pdfplumber.open(str(pdf_path)) as pdf:
        num_pages = len(pdf.pages)

    if all_pages:
        pages = list(range(1, num_pages + 1))
    elif page is not None:
        pages = [page]
    elif pages_arg is not None:
        pages = parse_pages_arg(pages_arg, num_pages)
    else:
        # Default: page 1 (good for summary/balance areas across banks)
        pages = [1]

    keywords = None
    if keywords_arg:
        keywords = [k.strip() for k in keywords_arg.split(",") if k.strip()]

    debug_pdf_raw(
        pdf_path=pdf_path,
        pages=pages,
        keywords=keywords,
        out_path=out_path,
    )
