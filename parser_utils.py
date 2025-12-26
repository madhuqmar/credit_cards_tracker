# parser.py
import pdfplumber
import pandas as pd
import re
from datetime import datetime
from typing import Optional, Tuple


# =============================
# Helpers
# =============================
def normalize_amount(raw: str) -> float:
    return float(raw.replace("$", "").replace(",", "").strip())


def parse_date(token: str):
    """
    Parse dates safely with explicit year.
    Supports:
    - MM/DD/YY   (Amex)
    - MM/DD
    - Mon DD
    """
    token = token.strip()
    year = datetime.now().year

    # 1) MM/DD/YY  (Amex, some Citi variants)
    try:
        return datetime.strptime(token, "%m/%d/%y").date()
    except Exception:
        pass

    # 2) MM/DD (assume current year)
    try:
        return datetime.strptime(f"{token}/{year}", "%m/%d/%Y").date()
    except Exception:
        pass

    # 3) Mon DD (assume current year)
    try:
        return datetime.strptime(f"{token} {year}", "%b %d %Y").date()
    except Exception:
        return None



def is_transaction_row(line: str) -> bool:
    return bool(
        re.search(r"\d{1,2}/\d{1,2}.*\$[\d,]+\.\d{2}", line)
    )


def _money_to_float(s: str) -> float:
    # accepts "612.08" or "$612.08" or "612.08 " etc.
    s = s.strip().replace("$", "").replace(",", "")
    return float(s)


# =============================
# Bank detection (filename-based)
# =============================
def detect_bank_type_from_filename(card_name: str) -> str:
    name = card_name.lower()

    # Apple Card (Goldman Sachs)
    if "apple card" in name or "applecard" in name or "apple_card" in name:
        return "apple"


    # Amex
    amex_month = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
    if (
        # explicit keywords (if present)
        "amex" in name
        or "americanexpress" in name
        or "american_express" in name
        # OR Amex-style date range filenames
        or re.search(
            rf"{amex_month}.*{amex_month}.*\d{{4}}",
            name
        )
    ):
        return "amex"

    # Capital One
    if "venture" in name or "capitalone" in name or "capital_one" in name:
        return "capital_one"

    # Barclays
    if "barclays" in name or "creditcardstatement" in name:
        return "barclays"

    # Bank of America
    if "estmt" in name or "bankofamerica" in name or "boa" in name:
        return "bank_of_america"

    # Citi (month+year NO SPACE)
    if re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\d{4}", name):
        return "citi"

    # Discover (month + space + year)
    if re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}", name):
        return "discover"

    return "generic"




# =============================
# Summary extractors
# =============================
def extract_barclays_summary(text: str):
    purchases = payments = credits = 0.0

    m = re.search(
        r"\bPurchases\b\s*\+?\s*\$?\s*([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if m:
        purchases = normalize_amount(m.group(1))

    m = re.search(r"Payments.*?\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        payments = normalize_amount(m.group(1))

    m = re.search(r"Other Credits.*?\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        credits = normalize_amount(m.group(1))

    return purchases, payments + credits


def extract_capital_one_transactions_total(text: str):
    m = re.search(
        r"Transactions\s*\+\s*\$([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if m:
        return normalize_amount(m.group(1))
    return None


def extract_capital_one_payments_and_credits(pdf) -> float:
    first_page_text = pdf.pages[0].extract_text() or ""

    payments = 0.0
    credits = 0.0

    m = re.search(
        r"Payments\s+-\s*\$([\d,]+\.\d{2})",
        first_page_text,
        re.IGNORECASE
    )
    if m:
        payments = normalize_amount(m.group(1))

    m = re.search(
        r"Other Credits\s+\$([\d,]+\.\d{2})",
        first_page_text,
        re.IGNORECASE
    )
    if m:
        credits = normalize_amount(m.group(1))

    return payments + credits

def extract_discover_summary(text: str):
    numbers = {}

    patterns = {
        "previous_balance": r"Previous Balance\s*\$([\d,]+\.\d{2})",
        "purchases": r"Purchases\s*\+?\$([\d,]+\.\d{2})",
        "payments_credits": r"-\s*\$([\d,]+\.\d{2})",
        # DO NOT TRUST new_balance here
        "new_balance": r"New Balance:\s*\$([\d,]+\.\d{2})"
    }

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            numbers[key] = normalize_amount(matches[0])

    # (We will IGNORE computed new_balance)
    return (
        numbers.get("purchases"),
        numbers.get("payments_credits"),
        None
    )


def extract_discover_statement_balance(text: str):
    matches = re.findall(
        r"New\s*Balance\s*:?\s*\$([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )

    if matches:
        # First occurrence is the Account Summary balance
        return normalize_amount(matches[0])

    return None


def extract_citi_summary(text: str):
    payments = credits = purchases = None

    m = re.search(r"Payments\s*-\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        payments = normalize_amount(m.group(1))

    m = re.search(r"Credits\s*-\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        credits = normalize_amount(m.group(1))

    m = re.search(r"Purchases\s*\+\$([\d,]+\.\d{2})", text, re.IGNORECASE)
    if m:
        purchases = normalize_amount(m.group(1))

    payments_credits_total = None
    if payments is not None or credits is not None:
        payments_credits_total = (payments or 0.0) + (credits or 0.0)

    return purchases, payments_credits_total

def extract_bank_of_america_summary(text: str):
    payments_credits = spend_total = None

    # Payments and Other Credits
    m = re.search(
        r"Payments and Other Credits\s*-\$([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if m:
        payments_credits = normalize_amount(m.group(1))

    # Purchases and Adjustments
    m = re.search(
        r"Purchases and Adjustments\s*\$([\d,]+\.\d{2})",
        text,
        re.IGNORECASE
    )
    if m:
        spend_total = normalize_amount(m.group(1))

    return spend_total, payments_credits


def extract_amex_summary(text: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Returns (statement_balance, payments_credits_total, spend_total)

    Intended behavior (per your example):
      - statement_balance = 612.08
      - payments_credits_total = 869.39   (Pay Over Time and/or Cash Advance section)
      - spend_total = 636.18              (Account Total section, New Charges)
    """
    if not text:
        return None, None, None

    # Normalize whitespace to make regex more reliable across PDF extraction quirks
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\r", "\n", t)

    statement_balance = None
    payments_credits_total = None
    spend_total = None

    # ------------------------------------------------------------
    # 1) Statement Balance: prefer "Pay Over Time and/or Cash Advance" New Balance
    # ------------------------------------------------------------
    m = re.search(
        r"Pay Over Time and/or Cash Advance.*?"
        r"New Balance\s*=\s*\$?([\d,]+\.\d{2})",
        t,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        statement_balance = _money_to_float(m.group(1))
    else:
        # Fallback: the big "New Balance" box often appears as "New Balance $612.08"
        m2 = re.search(r"\bNew Balance\b\s*\$?([\d,]+\.\d{2})", t, flags=re.IGNORECASE)
        if m2:
            statement_balance = _money_to_float(m2.group(1))

    # ------------------------------------------------------------
    # 2) Payments/Credits total: prefer Pay Over Time and/or Cash Advance Payments/Credits
    #    Example shows: Payments/Credits -$869.39
    # ------------------------------------------------------------
    m = re.search(
        r"Pay Over Time and/or Cash Advance.*?"
        r"Payments/Credits\s*-\s*\$?([\d,]+\.\d{2})",
        t,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        payments_credits_total = _money_to_float(m.group(1))
    else:
        # Fallback: Account Total Payments/Credits -$881.44
        m2 = re.search(
            r"Account Total.*?"
            r"Payments/Credits\s*-\s*\$?([\d,]+\.\d{2})",
            t,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if m2:
            payments_credits_total = _money_to_float(m2.group(1))

    # ------------------------------------------------------------
    # 3) Total purchases/charges/spend (Amex)
    # ------------------------------------------------------------

    # Primary: Account Total -> New Charges (page 1 layout)
    m = re.search(
        r"Account Total.*?"
        r"New Charges\s*\+?\s*\$?\s*([\d,]+\.\d{2})",
        t,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        spend_total = _money_to_float(m.group(1))
    else:
        # Fallback: "Total New Charges $12.05 $624.13 $636.18"
        # Rule: take the LAST dollar amount on that line
        m2 = re.search(
            r"^.*Total New Charges.*$",
            t,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if m2:
            amounts = re.findall(r"\$[\d,]+\.\d{2}", m2.group(0))
            if amounts:
                spend_total = _money_to_float(amounts[-1])


    return statement_balance, payments_credits_total, spend_total


def extract_apple_statement_balance(pdf) -> Optional[float]:
    """
    Apple Card (Goldman Sachs): extract ONLY the statement balance from page 1.

    Strategy (in order):
      1) Prefer 'Total Balance $X.XX' (stable and unambiguous)
      2) Fallback: the big summary block 'Your <Month> Balance ...' and take the FIRST $ amount
         (because that line also contains minimum payment and due date context)
      3) Never match 'Previous Monthly Balance' or 'Previous Total Balance'
    """
    if pdf is None or not getattr(pdf, "pages", None) or len(pdf.pages) == 0:
        return None

    text = pdf.pages[0].extract_text() or ""
    if not text.strip():
        return None

    # Normalize whitespace to reduce PDF extraction variance
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\r", "\n", t)

    def _to_float(s: str) -> float:
        return float(s.replace("$", "").replace(",", "").strip())

    # 1) Strongest signal: "Total Balance $767.74"
    m = re.search(
    r"(?im)^\s*Total Balance\s*\$([\d,]+\.\d{2})\s*$",
    t,
)

    if m:
        return _to_float(m.group(1))

    return None

def extract_apple_total_payments(pdf) -> Optional[float]:
    """
    Extract total payments from the Apple Card 'Payments' table section.
    Source of truth:
        'Total payments for this period   -$X.XX'
    Returns positive magnitude (e.g. 937.09)
    """
    if pdf is None or not getattr(pdf, "pages", None):
        return None

    text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Normalize whitespace
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\r", "\n", t)

    m = re.search(
        r"(?im)^Total payments for this period\s+-?\$([\d,]+\.\d{2})\s*$",
        t,
    )

    if not m:
        return None

    return float(m.group(1).replace(",", ""))

def extract_apple_total_spend(pdf) -> Optional[float]:
    """
    Extract total purchases / spend from the Apple Card Transactions section.

    Source of truth:
        'Total charges, credits and returns   $X.XX'

    Returns positive magnitude (e.g. 757.14)
    """
    if pdf is None or not getattr(pdf, "pages", None):
        return None

    text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Normalize whitespace
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\r", "\n", t)

    m = re.search(
        r"(?im)^Total charges, credits and returns\s+\$([\d,]+\.\d{2})\s*$",
        t,
    )

    if not m:
        return None

    return float(m.group(1).replace(",", ""))



# =============================
# Section detection (rows only)
# =============================
SECTION_MAP = {
    "payments": ["payments", "payment received"],
    "credits": ["other credits"],
    "purchases": ["purchase activity", "standard purchases", "purchases"],
    "cash_advances": ["cash advances"],
    "fees": ["fees charged"],
    "interest": ["interest charged"],
}


def detect_section_header(line: str):
    l = line.lower()
    for section, keys in SECTION_MAP.items():
        if any(k in l for k in keys):
            return section
    return None


