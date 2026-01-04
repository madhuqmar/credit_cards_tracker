import pdfplumber
import pandas as pd
import re

from parser_utils import (
    detect_bank_type_from_filename,
    normalize_amount,
    is_transaction_row,
    extract_bank_of_america_summary,
    extract_barclays_summary,
    extract_capital_one_payments_and_credits,
    extract_capital_one_transactions_total,
    extract_citi_summary,
    extract_discover_statement_balance,
    extract_discover_summary,
    extract_bank_of_america_summary,
    extract_amex_summary,
    extract_apple_statement_balance,
    extract_apple_total_payments,
    extract_apple_total_spend,
    parse_date,
)


CITI_ROW_REGEX = re.compile(
    r"""
    (?P<trans_date>\d{1,2}/\d{1,2})      # transaction date
    .*?
    (?P<amount>-?\$[\d,]+\.\d{2})        # amount anywhere
    """,
    re.VERBOSE,
)

BOA_ROW_REGEX = re.compile(
    r"""
    ^(?P<trans_date>\d{1,2}/\d{1,2})\s+
    (?P<post_date>\d{1,2}/\d{1,2})\s+
    (?P<desc>.+?)\s+
    (?P<ref>\d{3,4})\s+
    (?P<acct>\d{4})\s+
    (?P<amount>-?\d[\d,]*\.\d{2})$
    """,
    re.VERBOSE,
)

CAPONE_ROW_REGEX = re.compile(
    r"""
    ^(?P<trans_date>[A-Za-z]{3}\s+\d{1,2})\s+
    (?P<post_date>[A-Za-z]{3}\s+\d{1,2})\s+
    (?P<desc>.+?)\s+
    (?P<amount>-?\$[\d,]+\.\d{2})$
    """,
    re.VERBOSE,
)

BARCLAYS_ROW_REGEX = re.compile(
    r"""
    ^(?P<trans_date>[A-Za-z]{3}\s+\d{1,2})\s+
    (?P<post_date>[A-Za-z]{3}\s+\d{1,2})\s+
    (?P<desc>.+?)\s+
    (?P<points>N/A|-?\d+)\s+
    (?P<amount>-?\$[\d,]+\.\d{2})$
    """,
    re.VERBOSE,
)

AMEX_ROW_REGEX = re.compile(
    r"""
    ^(?P<trans_date>\d{1,2}/\d{1,2}/\d{2})\*?\s+
    (?P<desc>.+?)\s+
    (?P<amount>-?\$[\d,]+\.\d{2})
    (?:\S*)?$   # swallow trailing symbols like ⧫
    """,
    re.VERBOSE,
)


# Bank-agnostic keyword hints
CREDIT_KEYWORDS = [
    "payment",
    "credit",
    "refund",
    "return",
    "credit adjustment",
    "thank you",
]

SKIP_KEYWORDS = [
    "total",
    "interest charged",
    "fees charged",
]

def stitch_wrapped_lines(lines):
    """
    Generic line stitcher for statements where transactions can wrap:
      - Citi: MM/DD ... $amt
      - Amex: MM/DD/YY ... $amt OR $amt may appear inline
             followed by reference line like "DG3W3WBT 20002"
    """
    stitched = []
    buffer = ""

    # Start-of-transaction patterns
    starts_with_date = re.compile(r"^(?:\d{1,2}/\d{1,2}(?:/\d{2,4})?|[A-Za-z]{3}\s+\d{1,2})\b")

    # "Has an amount anywhere" (not necessarily at end)
    has_amount = re.compile(r"-?\$[\d,]+\.\d{2}")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If line starts with a date, start a new buffer
        if starts_with_date.match(line):
            if buffer:
                # only keep prior buffer if it contains an amount
                if has_amount.search(buffer):
                    stitched.append(buffer.strip())
            buffer = line
        else:
            buffer += " " + line

        # Finalize if buffer has amount and line looks like it ends a record
        # (Amex sometimes has inline amount, then next line is just reference code)
        if has_amount.search(buffer):
            # if this line contains amount, we can finalize immediately
            if has_amount.search(line):
                stitched.append(buffer.strip())
                buffer = ""

    if buffer and has_amount.search(buffer):
        stitched.append(buffer.strip())

    return stitched




def extract_transactions_from_pdf(pdf_file, card_name: str) -> pd.DataFrame:
    rows = []
    payments_credits_total = 0.0
    statement_balance = None
    spend_total = None

    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    bank_type = detect_bank_type_from_filename(card_name)

    # -----------------------------
    # Statement balance (all banks)
    # -----------------------------
    balance_patterns = [
        r"New Balance\s*=\s*\$([\d,]+\.\d{2})",
        r"New Balance\s*\n\s*\$([\d,]+\.\d{2})",
        r"(?:New Balance|Statement Balance(?: as of.*)?|New Balance Total)\s*\$([\d,]+\.\d{2})",
    ]

    for pattern in balance_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            statement_balance = normalize_amount(match.group(1))
            break

    # -----------------------------
    # Row-level extraction (BANK-AGNOSTIC)
    # -----------------------------
    raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
    if bank_type in {"citi", "amex"}:
        lines = stitch_wrapped_lines(raw_lines)
    else:
        lines = raw_lines



    for line in lines:
        date = merchant = None
        amount = None


        # -------------------------
        # Capital One rows
        # -------------------------
        if bank_type == "capital_one":
            match = CAPONE_ROW_REGEX.match(line)
            if not match:
                continue

            date = parse_date(match.group("trans_date"))
            amount = normalize_amount(match.group("amount"))
            merchant = match.group("desc").strip()

        elif bank_type == "barclays":
            match = BARCLAYS_ROW_REGEX.match(line)
            if not match:
                continue

            date = parse_date(match.group("trans_date"))
            merchant = match.group("desc").strip()
            amount = normalize_amount(match.group("amount"))


        # =========================
        # Bank of America (FIRST)
        # =========================
        elif bank_type == "bank_of_america":
            match = BOA_ROW_REGEX.match(line)
            if not match:
                continue

            date = parse_date(match.group("trans_date"))
            merchant = match.group("desc").strip()
            amount = float(match.group("amount").replace(",", ""))

        # =========================
        # Citi
        # =========================
        elif bank_type == "citi":
            match = CITI_ROW_REGEX.search(line)
            if not match:
                continue

            date = parse_date(match.group("trans_date"))
            amount = normalize_amount(match.group("amount"))

            merchant = line
            merchant = re.sub(r"^\d{1,2}/\d{1,2}", "", merchant)
            merchant = re.sub(r"-?\$[\d,]+\.\d{2}.*$", "", merchant)
            merchant = merchant.strip()
        
        # =========================
        # Amex
        # =========================
        elif bank_type == "amex":
            match = AMEX_ROW_REGEX.match(line.replace("⧫", "").strip())
            if not match:
                continue

            date = parse_date(match.group("trans_date"))
            merchant = match.group("desc").strip()
            amount = normalize_amount(match.group("amount"))  # will be positive magnitude

            # preserve sign from the raw string
            if match.group("amount").strip().startswith("-"):
                amount = -abs(amount)


        # ---- Generic rows
        else:
            if not is_transaction_row(line):
                continue

            parts = line.split()
            try:
                amount = normalize_amount(parts[-1])
            except Exception:
                continue

            date = parse_date(parts[0])
            merchant = " ".join(parts[1:-1]).strip()

        STATEMENT_NOISE_KEYWORDS = [
            "minimum payment",
            "payment due",
            "new balance",
            "statement balance",
            "account summary",
            "billing period",
            "credit limit",
            "available credit",
            "total fees",
            "interest charged",
            "eligible purchases",
            "eligible payments",
            "online payment",
            "mobile payment",
            "mobile pymt",
            "payment received",
            "internet payment",
            "credit adjustment",
            "points for statement credit",
            "ach deposit"
        ]

        merchant_lower = merchant.lower()

        # Drop statement-level noise rows
        if any(k in merchant_lower for k in STATEMENT_NOISE_KEYWORDS):
            continue

        # -----------------------------
        # Classification (SOURCE OF TRUTH)
        # -----------------------------
        if amount < 0:
            transaction_type = "credit"
            amount = -abs(amount)

        elif any(k in merchant_lower for k in CREDIT_KEYWORDS):
            transaction_type = "credit"
            amount = -abs(amount)

        else:
            transaction_type = "spend"
            amount = abs(amount)

        rows.append({
            "date": date,
            "card": card_name,
            "merchant": merchant,
            "amount": amount,
            "transaction_type": transaction_type,
            "bank_type": bank_type,
        })

    df = pd.DataFrame(
        rows,
        columns=["date", "card", "merchant", "amount", "transaction_type", "bank_type"],
    )

    # Ensure row parsing never contributes to totals
    payments_credits_total = None
    spend_total = None

    # -----------------------------
    # SUMMARY-BASED TOTALS (SOURCE OF TRUTH)
    # -----------------------------
    if bank_type == "barclays":
        spend_total, payments_credits_total = extract_barclays_summary(text)
        print("DEBUG BARCLAYS:", payments_credits_total, spend_total)


    elif bank_type == "capital_one":
        spend_total = extract_capital_one_transactions_total(text)
        payments_credits_total = extract_capital_one_payments_and_credits(pdf)

    elif bank_type == "discover":
        spend_total, payments_credits_total, _ = extract_discover_summary(text)
        statement_balance = extract_discover_statement_balance(text)

    elif bank_type == "citi":
        spend_total, payments_credits_total = extract_citi_summary(text)

    elif bank_type == "bank_of_america":
        spend_total, payments_credits_total = extract_bank_of_america_summary(text)

    elif bank_type == "amex":
        statement_balance, payments_credits_total, spend_total = extract_amex_summary(text)

    if bank_type == "apple":
        statement_balance = extract_apple_statement_balance(pdf)
        payments_credits_total = extract_apple_total_payments(pdf)
        spend_total = extract_apple_total_spend(pdf)

    # If summary extraction returned None (or wasn't run), calculate from rows
    if spend_total is None:
        spend_total = df[df["transaction_type"] == "spend"]["amount"].sum()
        
    if payments_credits_total is None:
        payments_credits_total = abs(
            df[df["transaction_type"] == "credit"]["amount"].sum()
        )

    # # -----------------------------
    # # Inject single authoritative spend row
    # # -----------------------------
    # # Inject single authoritative spend row (DO NOT delete detail rows)
    # if spend_total and spend_total > 0:
    #     df = pd.concat([
    #         df,
    #         pd.DataFrame([{
    #             "date": None,
    #             "card": card_name,
    #             "merchant": f"{bank_type.replace('_', ' ').title()} Statement Spend (Summary)",
    #             "amount": spend_total,
    #             "transaction_type": "spend_summary",
    #             "bank_type": bank_type,
    #         }])
    #     ], ignore_index=True)


    # -----------------------------
    # Attach statement-level metadata
    # -----------------------------
    df.attrs["statement_balance"] = statement_balance
    df.attrs["payments_credits_total"] = payments_credits_total
    df.attrs["bank_type"] = bank_type
    df.attrs["spend_total"] = spend_total   

    return df


# -----------------------------
# DEBUGGER (run parser.py directly)
# -----------------------------
if __name__ == "__main__":
    import sys
    from pathlib import Path

    print("\n🧪 PARSER DEBUG MODE\n")

    # Expect PDF paths as command-line arguments
    pdf_paths = sys.argv[1:]

    if not pdf_paths:
        print("Usage:")
        print("  python parser.py <statement1.pdf> <statement2.pdf> ...\n")
        sys.exit(0)

    debug_rows = []

    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        card_name = pdf_path.stem

        try:
            df = extract_transactions_from_pdf(str(pdf_path), card_name)
        except Exception as e:
            print(f"❌ Failed to parse {pdf_path.name}: {e}")
            continue

        statement_balance = df.attrs.get("statement_balance")
        payments_credits = df.attrs.get("payments_credits_total", 0.0)
        bank_type = df.attrs.get("bank_type", "unknown")

        # if not df.empty and "transaction_type" in df.columns:
        #     total_spend = df[df["transaction_type"] == "spend"]["amount"].sum()
        # else:
        #     total_spend = 0.0

        summary_spend = df.attrs.get("spend_total")

        if summary_spend is not None:
            total_spend = summary_spend
        elif not df.empty and "transaction_type" in df.columns:
            total_spend = df[df["transaction_type"] == "spend"]["amount"].sum()
        else:
            total_spend = 0.0


        print(f"\n{'='*80}")
        print(f"📄 Statement: {card_name}")
        print(f"🏦 Bank Type: {bank_type}")
        print(f"{'='*80}\n")

        # Show row-level transactions
        if not df.empty:
            print("🔍 Row-Level Transactions:\n")
            display_df = df.copy()
            display_df["amount"] = display_df["amount"].map(lambda x: f"${x:,.2f}")
            print(display_df[["date", "merchant", "amount", "transaction_type"]].to_string(index=False))
            print(f"\nTotal rows: {len(df)}")
            
            # Show section detection debug
            if hasattr(df, 'attrs') and 'debug_sections' in df.attrs:
                print(f"\n🔖 Sections Detected:")
                for s in df.attrs['debug_sections']:
                    print(f"  {s}")
        else:
            print("⚠️  No transactions found")

        print(f"\n📊 Summary:")
        print(f"  Statement Balance: ${statement_balance:,.2f}" if statement_balance else "  Statement Balance: N/A")
        print(f"  Payments/Credits: ${payments_credits:,.2f}")
        print(f"  Total Spend: ${total_spend:,.2f}")

        debug_rows.append({
            "Statement": card_name,
            "Bank Type": bank_type,
            "Statement Balance": statement_balance,
            "Payments / Credits": payments_credits,
            "Total Spend": total_spend
        })

    print(f"\n{'='*80}")
    print("📊 Overall Summary")
    print(f"{'='*80}\n")

    debug_df = pd.DataFrame(debug_rows)

    # Pretty formatting
    pd.set_option("display.float_format", "${:,.2f}".format)

    print(debug_df.to_string(index=False))
    print("\n✅ Debug complete\n")
