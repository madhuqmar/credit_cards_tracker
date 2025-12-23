import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from parser import extract_transactions_from_pdf
from categorizer import categorize_transaction

st.set_page_config(
    page_title="Credit Card Spend Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .main {
        background: linear-gradient(to bottom right, #f8f9fa 0%, #e9ecef 100%);
    }
    .stMetric {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -1px;
    }
    h2 {
        color: #2c3e50;
        font-weight: 700;
        margin-top: 2rem;
    }
    h3 {
        color: #34495e;
        font-weight: 600;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("💳 Monthly Credit Card Spend Dashboard")

# -----------------------------
# BUDGET INPUT
# -----------------------------
st.markdown("### 🎯 Set Your Budget")
BUDGET = st.number_input(
    "Enter your monthly budget target:",
    min_value=0,
    value=2300,
    step=100,
    help="Set your monthly spending target to track against"
)

st.divider()

# -----------------------------
# FILE UPLOAD
# -----------------------------
st.markdown("### 📁 Upload Statements")
uploaded_files = st.file_uploader(
    "Drop your credit card statement PDFs here",
    type=["pdf"],
    accept_multiple_files=True,
    help="You can upload multiple PDF statements at once"
)

if not uploaded_files:
    st.info("👆 Upload one or more PDFs to begin your financial journey!")
    
    # Add helpful tips
    with st.expander("💡 Tips for Getting Started"):
        st.markdown("""
        - **Multiple Statements**: Upload all your credit card PDFs at once
        - **Budget Tracking**: Set a realistic budget to monitor your spending
        - **Categories**: Transactions are automatically categorized for easy analysis
        - **Export**: Download your data as CSV for further analysis
        """)
    st.stop()

# -----------------------------
# PARSE PDFs
# -----------------------------
frames = []
all_uploaded_cards = []  # Track all uploaded PDFs

statement_balances = {}
payments_credits_totals = {}
bank_types = {}


for pdf in uploaded_files:
    card_name = pdf.name.replace(".pdf", "")
    all_uploaded_cards.append(card_name)
    df = extract_transactions_from_pdf(pdf, card_name)

    statement_balances[card_name] = df.attrs.get("statement_balance", 0.0)
    payments_credits_totals[card_name] = df.attrs.get("payments_credits_total", 0.0)
    bank_types[card_name] = df.attrs.get("bank_type", "unknown")

    if not df.empty:
        # 🔹 UPDATED: category + subcategory
        df[["category", "subcategory"]] = df["merchant"].apply(
            lambda x: pd.Series(categorize_transaction(x))
        )
        frames.append(df)
    else:
        # Even if empty, create a placeholder row to track the statement
        empty_df = pd.DataFrame([{
            "date": None,
            "card": card_name,
            "merchant": "No transactions found",
            "amount": 0.0,
            "transaction_type": "spend",
            "category": "Other",
            "subcategory": "Other"
        }])
        frames.append(empty_df)

data = pd.concat(frames, ignore_index=True)

# -----------------------------
# DEBUG: Show uploaded files
# -----------------------------
with st.expander(f"📋 Uploaded Files ({len(all_uploaded_cards)})"):
    st.write(all_uploaded_cards)
    st.write(f"Unique cards in data: {sorted(data['card'].unique().tolist())}")

# Note: We now keep payments in the data! They're marked as transaction_type="credit"
# and will be separated in the display tables below.


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
# Calculate total spend (positive amounts only) and total credits/payments (negative amounts)
total_balance = sum(v for v in statement_balances.values() if isinstance(v, (int, float)))
budget_diff = BUDGET - total_balance
pct_used = total_balance / BUDGET if BUDGET > 0 else 0

# -----------------------------
# MONTHLY SNAPSHOT
# -----------------------------
st.markdown("## 📌 Monthly Snapshot")
st.markdown("*Your spending overview at a glance*")

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div style='text-align: center; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid #667eea;'>
        <div style='color: #667eea; font-size: 14px; font-weight: 600; margin-bottom: 8px;'>TOTAL BALANCE</div>
        <div style='color: #2c3e50; font-size: 32px; font-weight: 700;'>${total_balance:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div style='text-align: center; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid #f093fb;'>
        <div style='color: #f093fb; font-size: 14px; font-weight: 600; margin-bottom: 8px;'>BUDGET TARGET</div>
        <div style='color: #2c3e50; font-size: 32px; font-weight: 700;'>${BUDGET:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    color = '#43e97b' if pct_used <= 0.7 else '#f5576c' if pct_used > 1 else '#f093fb'
    st.markdown(f"""
    <div style='text-align: center; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {color};'>
        <div style='color: {color}; font-size: 14px; font-weight: 600; margin-bottom: 8px;'>BUDGET USED</div>
        <div style='color: #2c3e50; font-size: 32px; font-weight: 700;'>{pct_used*100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    diff_color = '#43e97b' if budget_diff >= 0 else '#f5576c'
    diff_icon = '✅' if budget_diff >= 0 else '⚠️'
    st.markdown(f"""
    <div style='text-align: center; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {diff_color};'>
        <div style='color: {diff_color}; font-size: 14px; font-weight: 600; margin-bottom: 8px;'>BUDGET DIFFERENCE {diff_icon}</div>
        <div style='color: {diff_color}; font-size: 32px; font-weight: 700;'>{"$" + f"{budget_diff:,.2f}" if budget_diff >= 0 else "-$" + f"{abs(budget_diff):,.2f}"}</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    status_text = "Under Budget" if budget_diff >= 0 else "Over Budget"
    status_color = '#43e97b' if budget_diff >= 0 else '#f5576c'
    status_icon = '🎉' if budget_diff >= 0 else '💸'
    st.markdown(f"""
    <div style='text-align: center; padding: 15px; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-left: 4px solid {status_color};'>
        <div style='color: {status_color}; font-size: 14px; font-weight: 600; margin-bottom: 8px;'>STATUS</div>
        <div style='color: #2c3e50; font-size: 18px; font-weight: 700;'>{status_icon}<br/>{status_text}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# BIG BUDGET BAROMETER
# -----------------------------
st.subheader("🎯 Budget Barometer")

gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=total_balance,
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
st.markdown("## 📊 Spending Breakdown by Category")
st.markdown("*Detailed analysis of where your money goes*")

# Group by category and subcategory
category_subcategory_totals = (
    data[data.transaction_type == "spend"]
    .groupby(["category", "subcategory"], as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

# =========================================================
# ROW OF 3 SMALL CHARTS - WITH SUBCATEGORIES
# =========================================================
c1, c2, c3 = st.columns(3)

# -------- FOOD BREAKDOWN (WITH SUBCATEGORIES) --------
with c1:
    food = category_subcategory_totals[
        category_subcategory_totals["category"].isin(["Groceries", "Dining", "Food Delivery", "Food"])
    ]
    if not food.empty:
        st.markdown("### 🍽️ Food & Dining")
        fig_food = px.bar(
            food,
            x="subcategory",
            y="amount",
            height=300,
            color="category",
            color_discrete_map={
                "Groceries": "#54A24B",
                "Dining": "#F58518",
                "Food Delivery": "#E45756",
                "Food": "#EECA3B"
            },
            labels={"amount": "Amount ($)", "subcategory": ""},
            text_auto=".2f",
            title="Breakdown by Type"
        )
        fig_food.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=60, b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig_food.update_traces(textposition='outside')
        st.plotly_chart(fig_food, use_container_width=True)
        
        # Add total
        food_total = food["amount"].sum()
        st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: 600; color: #54A24B;'>Total: ${food_total:,.2f}</div>", unsafe_allow_html=True)

# -------- SHOPPING & GROOMING (WITH SUBCATEGORIES) --------
with c2:
    lifestyle = category_subcategory_totals[
        category_subcategory_totals["category"].isin(["Shopping", "Beauty / Grooming", "Grooming"])
    ]
    if not lifestyle.empty:
        st.markdown("### 🛍️ Lifestyle & Beauty")
        fig_lifestyle = px.bar(
            lifestyle,
            x="subcategory",
            y="amount",
            height=300,
            color="category",
            color_discrete_map={
                "Shopping": "#B279A2",
                "Beauty / Grooming": "#FF9DA6",
                "Grooming": "#FFB6C1"
            },
            labels={"amount": "Amount ($)", "subcategory": ""},
            text_auto=".2f",
            title="Breakdown by Type"
        )
        fig_lifestyle.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=60, b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig_lifestyle.update_traces(textposition='outside')
        st.plotly_chart(fig_lifestyle, use_container_width=True)
        
        # Add total
        lifestyle_total = lifestyle["amount"].sum()
        st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: 600; color: #B279A2;'>Total: ${lifestyle_total:,.2f}</div>", unsafe_allow_html=True)

# -------- TRANSPORT (WITH SUBCATEGORIES) --------
with c3:
    transport = category_subcategory_totals[
        category_subcategory_totals["category"] == "Transportation"
    ]

    if not transport.empty:
        st.markdown("### 🚕 Transportation")
        fig_transport = px.bar(
            transport,
            x="subcategory",
            y="amount",
            height=300,
            color="subcategory",
            color_discrete_map={
                "Uber": "#4C78A8",
                "Lyft": "#72B7B2",
                "Metro": "#9ECAE1",
                "Bikes": "#F58518"
            },
            labels={"amount": "Amount ($)", "subcategory": ""},
            text_auto=".2f",
            title="Breakdown by Provider"
        )

        fig_transport.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=60, b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        fig_transport.update_traces(textposition='outside')
        st.plotly_chart(fig_transport, use_container_width=True)
        
        # Add total
        transport_total = transport["amount"].sum()
        st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: 600; color: #4C78A8;'>Total: ${transport_total:,.2f}</div>", unsafe_allow_html=True)

st.divider()

# -----------------------------
# TRANSACTION SUMMARY METRICS
# -----------------------------
st.markdown("## 📊 Transaction Insights")
st.markdown("*Deep dive into your spending patterns*")

spend_data = data[data.transaction_type == "spend"]
total_transactions = len(spend_data)
total_spend = spend_data["amount"].sum()
avg_transaction = total_spend / total_transactions if total_transactions > 0 else 0

# Calculate category with most transactions
category_counts = spend_data.groupby("category").size().sort_values(ascending=False)
top_category = category_counts.index[0] if len(category_counts) > 0 else "N/A"
top_category_count = category_counts.iloc[0] if len(category_counts) > 0 else 0

# Calculate highest single transaction
if len(spend_data) > 0:
    max_transaction = spend_data.loc[spend_data["amount"].idxmax()]
    max_amount = max_transaction["amount"]
    max_merchant = max_transaction["merchant"]
else:
    max_amount = 0
    max_merchant = "N/A"

# Fun emoji mappings
category_emojis = {
    "Food": "🍽️",
    "Groceries": "🛒",
    "Dining": "🍴",
    "Food Delivery": "🚚",
    "Transportation": "🚕",
    "Shopping": "🛍️",
    "Beauty / Grooming": "💅",
    "Grooming": "✨",
    "Health / Fitness": "💪",
    "Subscriptions": "📱",
    "Other": "📦"
}

top_emoji = category_emojis.get(top_category, "🎯")

m1, m2, m3, m4, m5 = st.columns(5)

# Column 1: Total Transactions with fun styling
with m1:
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; box-shadow: 0 8px 16px rgba(102,126,234,0.4); transition: transform 0.3s;'>
        <div style='font-size: 56px; margin-bottom: 10px; animation: bounce 2s infinite;'>🔢</div>
        <div style='color: white; font-size: 42px; font-weight: 800; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>{total_transactions:,}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 13px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;'>Transactions</div>
    </div>
    """, unsafe_allow_html=True)

# Column 2: Total Spend with gradient
with m2:
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 15px; box-shadow: 0 8px 16px rgba(240,147,251,0.4);'>
        <div style='font-size: 56px; margin-bottom: 10px;'>💰</div>
        <div style='color: white; font-size: 42px; font-weight: 800; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>${total_spend:,.0f}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 13px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;'>Total Spent</div>
    </div>
    """, unsafe_allow_html=True)

# Column 3: Average Transaction
with m3:
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); border-radius: 15px; box-shadow: 0 8px 16px rgba(79,172,254,0.4);'>
        <div style='font-size: 56px; margin-bottom: 10px;'>📊</div>
        <div style='color: white; font-size: 42px; font-weight: 800; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>${avg_transaction:,.0f}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 13px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;'>Avg Purchase</div>
    </div>
    """, unsafe_allow_html=True)

# Column 4: Top Category
with m4:
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 15px; box-shadow: 0 8px 16px rgba(67,233,123,0.4);'>
        <div style='font-size: 56px; margin-bottom: 10px;'>{top_emoji}</div>
        <div style='color: white; font-size: 26px; font-weight: 800; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>{top_category}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 13px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;'>{top_category_count} purchases</div>
    </div>
    """, unsafe_allow_html=True)

# Column 5: Highest Transaction
with m5:
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); border-radius: 15px; box-shadow: 0 8px 16px rgba(250,112,154,0.4);'>
        <div style='font-size: 56px; margin-bottom: 10px;'>🏆</div>
        <div style='color: white; font-size: 42px; font-weight: 800; margin-bottom: 8px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>${max_amount:,.0f}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 13px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;'>Biggest Purchase</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -----------------------------
# DRILLDOWN
# -----------------------------
st.markdown("## 🔎 Transaction Drilldown")
st.markdown("*Filter and explore your transaction details*")

# --- Filters ---
f1, f2, f3 = st.columns([2, 2, 1])

with f1:
    selected_category = st.selectbox(
        "📂 Filter by category",
        ["All"] + sorted(data.category.unique()),
        help="Select a category to filter transactions"
    )

with f2:
    selected_card = st.selectbox(
        "💳 Filter by statement",
        ["All"] + sorted(data.card.unique()),
        help="Select a specific credit card statement"
    )

with f3:
    st.markdown("<br/>", unsafe_allow_html=True)  # Spacer
    if st.button("🔄 Reset Filters", use_container_width=True):
        st.rerun()

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

# Display filtered total with nice styling
filter_label = selected_category if selected_category != 'All' else 'All Categories'
if selected_card != 'All':
    filter_label += f" • {selected_card}"

st.markdown(f"""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 12px rgba(102,126,234,0.3);'>
    <div style='color: rgba(255,255,255,0.9); font-size: 14px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px;'>{filter_label}</div>
    <div style='color: white; font-size: 48px; font-weight: 800; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);'>${filtered_spend.amount.sum():,.2f}</div>
    <div style='color: rgba(255,255,255,0.85); font-size: 16px; margin-top: 8px;'>{len(filtered_spend)} transactions</div>
</div>
""", unsafe_allow_html=True)


# -------- Table --------
display_df = filtered.copy()

# Calculate total before formatting
total_amount = filtered_spend.amount.sum()

# Format amounts
display_df["amount"] = display_df["amount"].map(lambda x: f"${x:,.2f}")

# Sort by date
display_df = display_df[
    ["date", "merchant", "category", "subcategory", "amount", "card"]
].sort_values("date", ascending=False)

# Add total row
total_row = pd.DataFrame([{
    "date": None,
    "merchant": "TOTAL",
    "category": "",
    "subcategory": "",
    "amount": f"${total_amount:,.2f}",
    "card": ""
}])
display_df = pd.concat([display_df, total_row], ignore_index=True)

st.dataframe(
    display_df,
    use_container_width=True,
    height=420
)

# -----------------------------
# EXPORT
# -----------------------------
st.markdown("---")
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.download_button(
        "📥 Download Transaction Data (CSV)",
        data.to_csv(index=False),
        "monthly_transactions.csv",
        "text/csv",
        use_container_width=True,
        help="Export all transaction data to CSV format"
    )

st.divider()

# -----------------------------
# PDF / CARD TOTALS SUMMARY
# -----------------------------
st.markdown("## 📂 Statement Summaries")
st.markdown("*Overview of all uploaded credit card statements*")

st.markdown("### 💳 Statement Balances")

balance_rows = []

for card in all_uploaded_cards:
    balance = statement_balances.get(card)
    bank = bank_types.get(card)

    balance_rows.append({
        "Statement / Card": card,
        "Bank": bank,
        "Statement Balance": balance if isinstance(balance, (int, float)) else 0.0,
    })

balance_df = pd.DataFrame(balance_rows)

# Optional: sort highest balance first
balance_df = balance_df.sort_values("Statement Balance", ascending=False)

# Calculate total
total_balances = balance_df["Statement Balance"].sum()

# Format for display
display_balance_df = balance_df.copy()
display_balance_df["Statement Balance"] = display_balance_df["Statement Balance"].map(
    lambda x: f"${x:,.2f}"
)

# Add total row
total_row = pd.DataFrame([{
    "Statement / Card": "TOTAL",
    "Bank": "",
    "Statement Balance": f"${total_balances:,.2f}"
}])
display_balance_df = pd.concat([display_balance_df, total_row], ignore_index=True)

st.dataframe(
    display_balance_df,
    use_container_width=True,
    height=220,
    hide_index=True
)

st.markdown("<br/>", unsafe_allow_html=True)

# -----------------------------
# PAYMENTS, CREDITS & ADJUSTMENTS BY STATEMENT
# -----------------------------
st.markdown("### 💵 Payments & Credits")

payments_rows = []

for card in all_uploaded_cards:
    payment = payments_credits_totals.get(card)
    bank = bank_types.get(card)

    payments_rows.append({
        "Statement / Card": card,
        "Bank": bank,
        "Payments/Credits": payment if isinstance(payment, (int, float)) else 0.0,
        
    })

payments_df = pd.DataFrame(payments_rows)

# Optional: sort highest balance first
payments_df = payments_df.sort_values("Payments/Credits", ascending=False)

# Calculate total
total_payments = payments_df["Payments/Credits"].sum()

# Format for display
display_payments_df = payments_df.copy()
display_payments_df["Payments/Credits"] = display_payments_df["Payments/Credits"].map(
    lambda x: f"${x:,.2f}"
)

# Add total row
total_row_payments = pd.DataFrame([{
    "Statement / Card": "TOTAL",
    "Bank": "",
    "Payments/Credits": f"${total_payments:,.2f}"
}])
display_payments_df = pd.concat([display_payments_df, total_row_payments], ignore_index=True)

st.dataframe(
    display_payments_df,
    use_container_width=True,
    height=220
)


# -----------------------------
# TOTAL PURCHASES BY STATEMENT
# -----------------------------
st.subheader("💵 Total Purchases by Statement")

spend_rows = []

for card in all_uploaded_cards:
    payment = payments_credits_totals.get(card)
    bank = bank_types.get(card)

    payments_rows.append({
        "Statement / Card": card,
        "Bank": bank,
        "Payments/Credits": payment if isinstance(payment, (int, float)) else 0.0,
        
    })

payments_df = pd.DataFrame(payments_rows)

# Optional: sort highest balance first
payments_df = payments_df.sort_values("Payments/Credits", ascending=False)

# Calculate total
total_payments = payments_df["Payments/Credits"].sum()

# Format for display
display_payments_df = payments_df.copy()
display_payments_df["Payments/Credits"] = display_payments_df["Payments/Credits"].map(
    lambda x: f"${x:,.2f}"
)

# Add total row
total_row_payments = pd.DataFrame([{
    "Statement / Card": "TOTAL",
    "Bank": "",
    "Payments/Credits": f"${total_payments:,.2f}"
}])
display_payments_df = pd.concat([display_payments_df, total_row_payments], ignore_index=True)

st.dataframe(
    display_payments_df,
    use_container_width=True,
    height=220
)