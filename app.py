import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Mock add_auth if st-paywall is broken with current streamlit version
try:
    from st_paywall import add_auth
except ImportError:
    def add_auth(required=False):
        pass

from parser import extract_transactions_from_pdf
from categorizer import categorize_transaction

st.set_page_config(
    page_title="Credit Card Spend Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Add paywall - users need to subscribe to access the app
# try:
#     add_auth(required=True)
# except Exception as e:
#     st.error(f"Paywall Error: {e}")
#     st.info("Please ensure you have configured your .streamlit/secrets.toml correctly.")
#     # Fallback for development if paywall fails
#     if st.secrets.get("testing_mode", False):
#         st.warning("Running in testing mode without paywall.")
#     else:
#         st.stop()

# Custom CSS for minimalist luxury styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap');
    
    [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #CDE8DD !important;
        font-family: 'Playfair Display', serif;
        color: #092E19;
    }
    
    .stMetric {
        background: #F1F8F6;
        padding: 20px;
        border-radius: 0px;
        box-shadow: none;
        border: none;
    }
    
    h1 {
        color: #092E19;
        font-family: 'Playfair Display', serif;
        font-weight: 900;
        letter-spacing: -1px;
        text-align: left;
        font-size: 3.5rem !important;
        margin-bottom: 2rem;
        text-transform: lowercase;
        font-style: italic;
    }
    
    h2 {
        color: #0F462D;
        font-family: 'Playfair Display', serif;
        font-weight: 700;
        margin-top: 3rem;
        font-size: 2.2rem !important;
        border-bottom: 1px solid #175C44;
        padding-bottom: 10px;
        display: inline-block;
    }
    
    h3 {
        color: #175C44;
        font-family: 'Playfair Display', serif;
        font-weight: 500;
        font-size: 1.1rem !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .stDataFrame {
        border-radius: 0px;
        overflow: hidden;
        box-shadow: none;
        border: 1px solid #80C1B2;
    }
    
    .stButton>button {
        background: #092E19;
        color: #FFFFFF;
        border-radius: 0px;
        border: 1px solid #092E19;
        padding: 15px 40px;
        font-weight: 400;
        font-family: 'Playfair Display', serif;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    }
    
    .stButton>button:hover {
        background: #369692;
        color: #FFFFFF;
        border-color: #369692;
        transform: none;
        box-shadow: none;
    }
    
    .stSelectbox, .stNumberInput {
        font-family: 'Playfair Display', serif;
    }

    /* Refined minimalist input and option boxes */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 2px solid #175C44 !important;
        border-radius: 0px !important;
        transition: all 0.3s ease;
    }

    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-bottom-color: #369692 !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
    }

    /* Style the file uploader to be more integrated */
    [data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid #175C44 !important;
        border-radius: 0px !important;
        padding: 1.5rem !important;
    }

    [data-testid="stFileUploader"] {
        border: none !important;
    }

    /* Style the dropdown menu items */
    div[data-baseweb="popover"] ul {
        background-color: #F1F8F6 !important;
        border: 1px solid #175C44 !important;
        border-radius: 0px !important;
    }

    div[data-baseweb="popover"] li {
        color: #092E19 !important;
        font-family: 'Playfair Display', serif !important;
    }

    div[data-baseweb="popover"] li:hover {
        background-color: #CDE8DD !important;
    }
    
    hr {
        border: none;
        height: 1px;
        background: #80C1B2;
        margin: 3rem 0;
    }

    /* Custom card styling for metrics */
    .metric-card {
        background: #F1F8F6;
        padding: 25px;
        border: none;
        text-align: left;
    }

    /* Remove the white outline/halo from Sankey labels */
    .js-plotly-plot .plotly text, 
    .js-plotly-plot .plotly tspan {
        text-shadow: none !important;
        stroke: none !important;
        stroke-width: 0 !important;
        paint-order: markers fill stroke !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("statements simplified ✨")

# -----------------------------
# FILE UPLOAD
# -----------------------------
st.markdown("### 📁 Upload Your Statements")
st.markdown("*Drop your credit card PDFs here*")
uploaded_files = st.file_uploader(
    "Choose your statement PDFs:",
    type=["pdf"],
    accept_multiple_files=True,
    help="✨ You can upload multiple PDF statements at once"
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
# TRANSPORT PROVIDER (BACKWARD COMPATIBLE)
# -----------------------------
def transport_provider(row):
    if row["category"] != "Transportation":
        return None
    return row["subcategory"]

data["transport_provider"] = data.apply(transport_provider, axis=1)

# Calculate total spend (positive amounts only) and total credits/payments (negative amounts)
total_balance = sum(v for v in statement_balances.values() if isinstance(v, (int, float)))

# -----------------------------
# BUDGET & BAROMETER
# -----------------------------
st.divider()
col_budget, col_gauge = st.columns([1, 2])

with col_budget:
    st.markdown("### 💰 Monthly Budget Goal")
    st.markdown("*Set your spending limit and track your progress*")
    BUDGET = st.number_input(
        "Your budget target:",
        min_value=0,
        value=2300,
        step=100,
        help="✨ Set your monthly spending goal"
    )
    
    budget_diff = BUDGET - total_balance
    pct_used = total_balance / BUDGET if BUDGET > 0 else 0
    
    status_text = "On Track" if budget_diff >= 0 else "Over Budget"
    status_color = "#175C44" if budget_diff >= 0 else "#092E19"
    
    st.markdown(f"""
    <div style='margin-top: 20px; padding: 20px; border: none; background: #F1F8F6;'>
        <div style='color: #369692; font-size: 11px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;'>Current Status</div>
        <div style='color: {status_color}; font-size: 24px; font-weight: 700; font-family: "Playfair Display", serif; font-style: italic;'>{status_text}</div>
        <div style='color: #092E19; font-size: 14px; margin-top: 5px;'>
            {"Remaining: $" + f"{budget_diff:,.2f}" if budget_diff >= 0 else "Over by: $" + f"{abs(budget_diff):,.2f}"}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_gauge:
    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_balance,
        number={"prefix": "$", "font": {"size": 48, "color": "#092E19", "family": "Playfair Display"}},
        gauge={
            "axis": {"range": [0, max(BUDGET, total_balance * 1.1)], "tickcolor": "#092E19"},
            "bar": {"color": "#175C44", "thickness": 0.2},
            "steps": [
                {"range": [0, BUDGET], "color": "#F1F8F6"}
            ],
            "threshold": {
                "line": {"color": "#369692", "width": 2},
                "thickness": 0.8,
                "value": BUDGET
            }
        }
    ))
    gauge.update_layout(
        height=300, 
        margin=dict(l=40, r=40, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'family': "Playfair Display"}
    )
    st.plotly_chart(gauge, width='stretch')

st.divider()

# Group by category and subcategory
category_subcategory_totals = (
    data[data.transaction_type == "spend"]
    .groupby(["category", "subcategory"], as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

# -----------------------------
# SANKEY CHART - SPENDING FLOW
# -----------------------------
st.markdown("## 🌊 Spending Flow")
st.markdown("*Visualize how your money flows across categories*")

# Prepare data for Sankey diagram (3 levels: Total -> Category -> Subcategory)
sankey_data = category_subcategory_totals[category_subcategory_totals["amount"] > 0].copy()

# Calculate total spending
total_spending = sankey_data["amount"].sum()

# Create labels list: ["Total Spending", Categories..., Subcategories...]
labels = ["Total Spending"]
unique_categories = sankey_data["category"].unique().tolist()
unique_subcategories = sankey_data["subcategory"].unique().tolist()
labels.extend(unique_categories)
labels.extend(unique_subcategories)

# Create source, target, and value lists for the flows
sources = []
targets = []
values = []

# Level 1: Total Spending -> Categories
category_totals = sankey_data.groupby("category")["amount"].sum()
for category in unique_categories:
    sources.append(0)  # Total Spending index
    targets.append(labels.index(category))
    values.append(category_totals[category])

# Level 2: Categories -> Subcategories
for _, row in sankey_data.iterrows():
    category = row["category"]
    subcategory = row["subcategory"]
    amount = row["amount"]
    
    source_idx = labels.index(category)
    target_idx = labels.index(subcategory)
    
    sources.append(source_idx)
    targets.append(target_idx)
    values.append(amount)

# Create color scheme
node_colors = ["#156161"]  # Total Spending - Dark Teal

# Category colors - New Blue/Teal palette
category_color_map = {
    "Food": "#247D96",
    "Groceries": "#3673CA",
    "Dining": "#4A56FE",
    "Food Delivery": "#6490FF",
    "Transportation": "#7EBFFF",
    "Shopping": "#98E3FF",
    "Beauty / Grooming": "#B3FCFF",
    "Grooming": "#247D96",
    "Health / Fitness": "#3673CA",
    "Subscriptions": "#4A56FE",
    "Other": "#6490FF",
    "Anomalies": "#156161"
}

# Add category colors
for cat in unique_categories:
    node_colors.append(category_color_map.get(cat, "#7EBFFF"))

# Add subcategory colors (slightly more opaque)
for subcat in unique_subcategories:
    node_colors.append("rgba(36, 125, 150, 0.8)")

# Create Sankey diagram
fig_sankey = go.Figure(data=[go.Sankey(
    arrangement='snap', 
    node=dict(
        pad=15, 
        thickness=80, 
        line=dict(color="#092E19", width=0),
        label=labels, 
        color=node_colors,
        customdata=[f"${total_spending:,.2f}"] + 
                   [f"${category_totals[cat]:,.2f}" for cat in unique_categories] +
                   [f"${sankey_data[sankey_data['subcategory'] == subcat]['amount'].sum():,.2f}" 
                    for subcat in unique_subcategories],
        hovertemplate='<b>%{label}</b><br>Total: %{customdata}<extra></extra>',
        hoverlabel=dict(
            font=dict(family="Playfair Display, serif", size=12),
            bordercolor="rgba(0,0,0,0)"
        )
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color="rgba(36, 125, 150, 0.2)",
        hovertemplate='%{source.label} → %{target.label}<br>$%{value:,.2f}<extra></extra>',
        hoverlabel=dict(
            font=dict(family="Playfair Display, serif", size=12),
            bordercolor="rgba(0,0,0,0)"
        )
    ),
    textfont=dict(family="Playfair Display, serif", size=12, color="#092E19") 
)])

fig_sankey.update_layout(
    title=dict(
        text=f"spending flow: ${total_spending:,.2f}",
        font=dict(size=28, color="#092E19", family="Playfair Display, serif")
    ),
    font=dict(size=14, family="Playfair Display, serif"),
    height=600, 
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=40, r=40, t=80, b=40) 
)

st.plotly_chart(fig_sankey, width='stretch')

st.divider()

# -----------------------------
# CATEGORY TOTALS
# -----------------------------
st.markdown("##  Spending Breakdown")
st.markdown("*Where did all my money go? Let's find out!*")

# =========================================================
# ROW OF 3 SMALL CHARTS - WITH SUBCATEGORIES
# =========================================================
c1, c2, c3 = st.columns(3)

# -------- FOOD BREAKDOWN (WITH SUBCATEGORIES) --------
with c1:
    food = category_subcategory_totals[
        category_subcategory_totals["category"].isin(["Groceries", "Food"])
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
                "Groceries": "#175C44",
                "Dining": "#2A8477",
                "Food Delivery": "#369692",
                "Food": "#092E19",
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
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': "Playfair Display", 'color': "#092E19"}
        )
        fig_food.update_traces(textposition='outside')
        st.plotly_chart(fig_food, width='stretch')
        
        # Add total
        food_total = food["amount"].sum()
        st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: 600; color: #175C44;'>Total: ${food_total:,.2f}</div>", unsafe_allow_html=True)

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
                "Shopping": "#175C44",
                "Beauty / Grooming": "#2A8477",
                "Grooming": "#369692"
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
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': "Playfair Display", 'color': "#092E19"}
        )
        fig_lifestyle.update_traces(textposition='outside')
        st.plotly_chart(fig_lifestyle, width='stretch')
        
        # Add total
        lifestyle_total = lifestyle["amount"].sum()
        st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: 600; color: #175C44;'>Total: ${lifestyle_total:,.2f}</div>", unsafe_allow_html=True)

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
                "Uber": "#175C44",
                "Lyft": "#2A8477",
                "Metro": "#369692",
                "Bikes": "#092E19"
            },
            labels={"amount": "Amount ($)", "subcategory": ""},
            text_auto=".2f",
            title="Breakdown by Provider"
        )

        fig_transport.update_layout(
            showlegend=False,
            margin=dict(l=10, r=10, t=60, b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'family': "Playfair Display", 'color': "#092E19"}
        )
        fig_transport.update_traces(textposition='outside')
        st.plotly_chart(fig_transport, width='stretch')
        
        # Add total
        transport_total = transport["amount"].sum()
        st.markdown(f"<div style='text-align: center; font-size: 18px; font-weight: 600; color: #175C44;'>Total: ${transport_total:,.2f}</div>", unsafe_allow_html=True)

st.divider()

# -----------------------------
# TRANSACTION SUMMARY METRICS
# -----------------------------
st.markdown("## 🎯 Transaction Insights")
st.markdown("*Your spending story in numbers*")

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

# Column 1: Total Transactions
with m1:
    st.markdown(f"""
    <div style='text-align: left; padding: 25px; background: #F1F8F6; border: none; height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: #369692; font-size: 10px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;'>Volume</div>
        <div>
            <div style='color: #092E19; font-size: 42px; font-weight: 400; font-family: "Playfair Display", serif;'>{total_transactions:,}</div>
            <div style='color: #175C44; font-size: 12px; text-transform: lowercase; font-style: italic;'>purchases</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Column 2: Total Spend
with m2:
    st.markdown(f"""
    <div style='text-align: left; padding: 25px; background: #F1F8F6; border: none; height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: #369692; font-size: 10px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;'>Expenditure</div>
        <div>
            <div style='color: #092E19; font-size: 42px; font-weight: 400; font-family: "Playfair Display", serif;'>${total_spend:,.0f}</div>
            <div style='color: #175C44; font-size: 12px; text-transform: lowercase; font-style: italic;'>total spent</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Column 3: Average Transaction
with m3:
    st.markdown(f"""
    <div style='text-align: left; padding: 25px; background: #F1F8F6; border: none; height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: #369692; font-size: 10px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;'>Average</div>
        <div>
            <div style='color: #092E19; font-size: 42px; font-weight: 400; font-family: "Playfair Display", serif;'>${avg_transaction:,.0f}</div>
            <div style='color: #175C44; font-size: 12px; text-transform: lowercase; font-style: italic;'>per purchase</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Column 4: Top Category
with m4:
    st.markdown(f"""
    <div style='text-align: left; padding: 25px; background: #F1F8F6; border: none; height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: #369692; font-size: 10px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;'>Focus</div>
        <div>
            <div style='color: #092E19; font-size: 42px; font-weight: 400; font-family: "Playfair Display", serif; line-height: 1.1;'>{top_category}</div>
            <div style='color: #175C44; font-size: 12px; text-transform: lowercase; font-style: italic;'>{top_category_count} transactions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Column 5: Highest Transaction
with m5:
    st.markdown(f"""
    <div style='text-align: left; padding: 25px; background: #F1F8F6; border: none; height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: #369692; font-size: 10px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase;'>Peak</div>
        <div>
            <div style='color: #092E19; font-size: 42px; font-weight: 400; font-family: "Playfair Display", serif;'>${max_amount:,.0f}</div>
            <div style='color: #175C44; font-size: 12px; text-transform: lowercase; font-style: italic;'>single splurge</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -----------------------------
# DRILLDOWN
# -----------------------------
st.markdown("## 🔍 Transaction Details")
st.markdown("*Explore your spending by category and card*")

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
    if st.button("🔄 Reset Filters", width='stretch'):
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
<div style='background: linear-gradient(135deg, #175C44 0%, #80C1B2 100%); padding: 30px; border-radius: 0px; margin: 20px 0; border: none;'>
    <div style='color: rgba(255,255,255,0.8); font-size: 12px; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 12px; font-weight: 500;'>{filter_label}</div>
    <div style='color: #FFFFFF; font-size: 52px; font-weight: 400; font-family: "Playfair Display", serif;'>${filtered_spend.amount.sum():,.2f}</div>
    <div style='color: rgba(255,255,255,0.7); font-size: 14px; margin-top: 10px; font-style: italic;'>{len(filtered_spend)} transactions</div>
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
    width='stretch',
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
        width='stretch',
        help="Export all transaction data to CSV format"
    )

st.divider()

# -----------------------------
# PDF / CARD TOTALS SUMMARY
# -----------------------------
st.markdown("## 📋 Statement Summaries")
st.markdown("*All your cards at a glance*")

st.markdown("### 💳 Your Card Balances")

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
    width='stretch',
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
    width='stretch',
    height=220
)


# -----------------------------
# TOTAL PURCHASES BY STATEMENT
# -----------------------------
st.subheader("💳 Total Purchases by Statement")

spend_rows = []

for card in all_uploaded_cards:
    # Calculate total spend (purchases) for this card
    card_spend = data[(data.card == card) & (data.transaction_type == "spend")]["amount"].sum()
    bank = bank_types.get(card)

    spend_rows.append({
        "Statement / Card": card,
        "Bank": bank,
        "Total Purchases": card_spend if isinstance(card_spend, (int, float)) else 0.0,
    })

spend_df = pd.DataFrame(spend_rows)

# Optional: sort highest spend first
spend_df = spend_df.sort_values("Total Purchases", ascending=False)

# Calculate total
total_spend_amount = spend_df["Total Purchases"].sum()

# Format for display
display_spend_df = spend_df.copy()
display_spend_df["Total Purchases"] = display_spend_df["Total Purchases"].map(
    lambda x: f"${x:,.2f}"
)

# Add total row
total_row_spend = pd.DataFrame([{
    "Statement / Card": "TOTAL",
    "Bank": "",
    "Total Purchases": f"${total_spend_amount:,.2f}"
}])
display_spend_df = pd.concat([display_spend_df, total_row_spend], ignore_index=True)

st.dataframe(
    display_spend_df,
    width='stretch',
    height=220
)