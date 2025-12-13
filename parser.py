import pdfplumber
import pandas as pd
import re

# -----------------------------
# PAYMENT TO CARD (EXCLUDE)
# -----------------------------
def is_card_payment(description: str) -> bool:
    """
    Detect payments made TO the credit card.
    These should never be treated as transactions.
    """
    desc = description.lower()
    desc = re.sub(r"[^a-z ]", " ", desc)
    desc = re.sub(r"\s+", " ", desc).strip()

    PAYMENT_PATTERNS = [
        "payment",
        "thank you",
        "autopay",
        "payment received",
        "ach"
    ]

    return any(p in desc for p in PAYMENT_PATTERNS)

# -----------------------------
# STATEMENT SUMMARY FILTER
# -----------------------------
SUMMARY_KEYWORDS = [
    "statement balance",
    "new balance",
    "previous balance",
    "balance as of",
    "minimum payment",
    "payment due",
    "late payment",
    "account summary",
    "account ending",
    "credit limit",
    "available credit",
    "total fees",
    "total interest",
    "interest charged",
    "finance charge",
    "cash advance"
]

def is_statement_summary(description: str) -> bool:
    desc = description.lower()
    return any(k in desc for k in SUMMARY_KEYWORDS)

# -----------------------------
# MERCHANT SANITY CHECK
# -----------------------------
def is_invalid_merchant(description: str) -> bool:
    if not description:
        return True
    desc = description.strip()
    if desc == "":
        return True
    if re.fullmatch(r"[\d\W_]+", desc):
        return True
    if len(desc) < 3:
        return True
    return False

# -----------------------------
# MAIN PARSER
# -----------------------------
def extract_transactions_from_pdf(pdf_file, card_name):
    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                amounts = re.findall(
                    r"-?\$?\d{1,3}(?:,\d{3})*\.\d{2}", line
                )
                date_match = re.search(
                    r"\d{2}/\d{2}/\d{4}|\d{2}/\d{2}", line
                )

                if not amounts or not date_match:
                    continue

                raw_amount = amounts[-1]
                amount_val = float(raw_amount.replace("$", "").replace(",", ""))

                description = re.sub(
                    r"-?\$?\d{1,3}(?:,\d{3})*\.\d{2}", "", line
                )
                description = re.sub(
                    r"\d{2}/\d{2}/\d{4}|\d{2}/\d{2}", "", description
                ).strip()

                # ❌ Hard exclusions
                if is_invalid_merchant(description):
                    continue
                if is_statement_summary(description):
                    continue
                if is_card_payment(description):
                    continue   # 🔴 PAYMENTS NEVER ENTER DATA

                transaction_type = "spend" if amount_val > 0 else "credit"

                rows.append({
                    "date": date_match.group(),
                    "card": card_name,
                    "merchant": description,
                    "amount": amount_val,
                    "transaction_type": transaction_type
                })

    return pd.DataFrame(rows)
