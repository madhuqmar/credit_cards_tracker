# parser.py
import pdfplumber
import pandas as pd
import re
from datetime import datetime


# =============================
# Helpers
# =============================
def normalize_amount(raw: str) -> float:
    return float(raw.replace("$", "").replace(",", "").strip())


def parse_date(token: str):
    """
    Parse dates safely with explicit year.
    Supports:
    - MM/DD
    - Mon DD
    """
    year = datetime.now().year
    try:
        return datetime.strptime(f"{token}/{year}", "%m/%d/%Y").date()
    except Exception:
        try:
            return datetime.strptime(f"{token} {year}", "%b %d %Y").date()
        except Exception:
            return None


def is_transaction_row(line: str) -> bool:
    return bool(
        re.search(r"\d{1,2}/\d{1,2}.*\$[\d,]+\.\d{2}", line)
    )



# =============================
# Bank detection (filename-based)
# =============================
def detect_bank_type_from_filename(card_name: str) -> str:
    name = card_name.lower()

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

    m = re.search(r"Purchases\s+\+?\$([\d,]+\.\d{2})", text, re.IGNORECASE)
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