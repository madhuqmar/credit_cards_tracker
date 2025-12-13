import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from parser import extract_transactions_from_pdf
from categorizer import categorize_transaction

# -----------------------------
# CONFIG
# -----------------------------
BUDGET = 2300

st.set_page_config(
    page_title="Credit Card Spend Dashboard",
    layout="wide"
)

st.title("💳 Monthly Credit Card Spend Dashboard")

# -----------------------------
# FILE UPLOAD
# -----------------------------
uploaded_files = st.file_uploader(
    "Upload credit card statement PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("Upload one or more PDFs to begin.")
    st.stop()

# -----------------------------
# PARSE PDFs
# -----------------------------
frames = []

for pdf in uploaded_files:
    card_name = pdf.name.replace(".pdf", "")
    df = extract_transactions_from_pdf(pdf, card_name)

    if not df.empty:
        # 🔹 UPDATED: category + subcategory
        df[["category", "subcategory"]] = df["merchant"].apply(
            lambda x: pd.Series(categorize_transaction(x))
        )
        frames.append(df)

data = pd.concat(frames, ignore_index=True)

# -----------------------------
# HARD EXCLUDE CARD PAYMENTS (DEFENSIVE)
# -----------------------------
PAYMENT_PATTERNS = [
    "payment",
    "thank you",
    "autopay",
    "payment received",
    "ach"
]

data = data[
    ~data["merchant"]
    .str.lower()
    .str.replace("-", " ", regex=False)
    .str.contains("|".join(PAYMENT_PATTERNS), na=False)
].copy()


# -----------------------------
# TRANSPORT PROVIDER (BACKWARD COMPATIBLE)
# -----------------------------
def transport_provider(row):
    if row["category"] != "Transportation":
        return None
    return row["subcategory"]

data["transport_provider"] = data.apply(transport_provider, axis=1)

# -----------------------------
# METRICS
# -----------------------------
total_spend = data.amount.sum()
budget_diff = BUDGET - total_spend
pct_used = total_spend / BUDGET

# -----------------------------
# MONTHLY SNAPSHOT
# -----------------------------
st.subheader("📌 Monthly Snapshot")

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Spend", f"${total_spend:,.2f}")
k2.metric("Budget Target", f"${BUDGET:,.0f}")
k3.metric("Budget Used", f"{pct_used*100:.1f}%")
k4.metric("Budget Difference", f"${abs(budget_diff):,.2f}")
k5.metric("Status", "Under Budget ✅" if budget_diff >= 0 else "Over Budget ⚠️")

# -----------------------------
# BIG BUDGET BAROMETER
# -----------------------------
st.subheader("🎯 Budget Barometer")

gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=total_spend,
    number={"prefix": "$", "font": {"size": 48}},
    gauge={
        "axis": {"range": [0, BUDGET]},
        "bar": {"color": "#4C78A8", "thickness": 0.65},
        "steps": [
            {"range": [0, BUDGET * 0.7], "color": "#EAF2FB"},
            {"range": [BUDGET * 0.7, BUDGET], "color": "#FFF1E6"}
        ],
        "threshold": {
            "line": {"color": "red", "width": 6},
            "thickness": 0.85,
            "value": BUDGET
        }
    }
))
gauge.update_layout(height=420, margin=dict(l=40, r=40, t=40, b=20))
st.plotly_chart(gauge, use_container_width=True)

st.divider()

# -----------------------------
# CATEGORY TOTALS
# -----------------------------
category_totals = (
    data.groupby("category", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

# =========================================================
# ROW OF 3 SMALL CHARTS
# =========================================================
c1, c2, c3 = st.columns(3)

# -------- FOOD BREAKDOWN --------
with c1:
    food = category_totals[
        category_totals["category"].isin(["Groceries", "Dining", "Food Delivery"])
    ]
    if not food.empty:
        st.subheader("🍽️ Food")
        st.plotly_chart(
            px.bar(
                food,
                x="category",
                y="amount",
                height=260,
                color="category",
                color_discrete_map={
                    "Groceries": "#54A24B",
                    "Dining": "#F58518",
                    "Food Delivery": "#E45756"
                },
                labels={"amount": "$"},
                text_auto=".2f"
            ),
            use_container_width=True
        )

# -------- SHOPPING vs GROOMING --------
with c2:
    lifestyle = category_totals[
        category_totals["category"].isin(["Shopping", "Beauty / Grooming"])
    ]
    if not lifestyle.empty:
        st.subheader("🛍️ Lifestyle")
        st.plotly_chart(
            px.bar(
                lifestyle,
                x="category",
                y="amount",
                height=260,
                color="category",
                color_discrete_map={
                    "Shopping": "#B279A2",
                    "Beauty / Grooming": "#FF9DA6"
                },
                labels={"amount": "$"},
                text_auto=".2f"
            ),
            use_container_width=True
        )

# -------- TRANSPORT (FIXED + BIKES) --------
with c3:
    transport = data[data.category == "Transportation"]

    if not transport.empty:
        transport_summary = (
            transport
            .groupby("transport_provider", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )

        st.subheader("🚕 Transport")

        fig = px.bar(
            transport_summary,
            x="transport_provider",
            y="amount",
            height=260,
            color="transport_provider",
            color_discrete_map={
                "Uber": "#4C78A8",
                "Lyft": "#72B7B2",
                "Metro": "#9ECAE1",
                "Bikes": "#F58518"
            },
            labels={"amount": "$", "transport_provider": ""},
            text_auto=".2f"
        )

        fig.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=30, b=10)
        )

        st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------------
# DRILLDOWN
# -----------------------------
st.subheader("🔎 Transaction Drilldown")

# --- Filters ---
f1, f2 = st.columns(2)

with f1:
    selected_category = st.selectbox(
        "Filter by category",
        ["All"] + sorted(data.category.unique())
    )

with f2:
    selected_card = st.selectbox(
        "Filter by statement",
        ["All"] + sorted(data.card.unique())
    )

# --- Apply filters ---
filtered = data.copy()

if selected_category != "All":
    filtered = filtered[filtered.category == selected_category]

if selected_card != "All":
    filtered = filtered[filtered.card == selected_card]

# -------- Dynamic total metric --------
label_parts = []
if selected_category != "All":
    label_parts.append(selected_category)
if selected_card != "All":
    label_parts.append(selected_card)

# Only count real spend in totals
filtered_spend = filtered[filtered.transaction_type == "spend"]

st.metric(
    label=f"Total for {selected_category if selected_category != 'All' else 'All Categories'}",
    value=f"${filtered_spend.amount.sum():,.2f}"
)


# -------- Table --------
display_df = filtered.copy()
display_df["amount"] = display_df["amount"].map(lambda x: f"${x:,.2f}")

st.dataframe(
    display_df[
        ["date", "merchant", "category", "subcategory", "amount", "card"]
    ].sort_values("date", ascending=False),
    use_container_width=True,
    height=420
)


# -----------------------------
# EXPORT
# -----------------------------
st.download_button(
    "⬇️ Download Generated CSV",
    data.to_csv(index=False),
    "monthly_transactions.csv",
    "text/csv"
)

# -----------------------------
# PDF / CARD TOTALS SUMMARY
# -----------------------------
st.subheader("📂 Spend by Statement (PDF)")

pdf_summary = (
    data.groupby("card", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

# Optional: add % of total
pdf_summary["% of Total"] = (
    pdf_summary["amount"] / pdf_summary["amount"].sum() * 100
).round(1)

# Format for display
display_pdf_summary = pdf_summary.copy()
display_pdf_summary["amount"] = display_pdf_summary["amount"].map(lambda x: f"${x:,.2f}")
display_pdf_summary["% of Total"] = display_pdf_summary["% of Total"].map(lambda x: f"{x}%")

st.dataframe(
    display_pdf_summary.rename(columns={
        "card": "Statement / Card",
        "amount": "Total Balance"
    }),
    use_container_width=True,
    height=220
)

