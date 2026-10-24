import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="College Canteen Food Waste Analyzer",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f4fff8 0%, #eef6ff 100%);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
    }
    h1 {
        font-size: 3.3rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em;
        line-height: 1.1 !important;
        margin-bottom: 0.2rem !important;
    }
    @media (max-width: 1200px) {
        h1 {
            font-size: 2.5rem !important;
            white-space: normal;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1>🍽️ Smart College Canteen Food Waste Analyzer</h1>", unsafe_allow_html=True)

project_root = Path(__file__).resolve().parent.parent
data_path = project_root / "data" / "canteen_food_waste.csv"

if not data_path.exists():
    st.error(f"Dataset not found: {data_path}")
    st.stop()

@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    if "prepared_kg" in df.columns:
        df = df.rename(columns={
            "prepared_kg": "prepared_quantity",
            "served_kg": "consumed_quantity",
            "waste_kg": "wasted_quantity",
        })

    numeric_cols = ["prepared_quantity", "consumed_quantity", "wasted_quantity"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    if "food_item" in df.columns:
        df["food_item"] = df["food_item"].astype(str).str.strip()
        df["food_item"] = df["food_item"].str.replace(r"(.+?)\1+$", r"\1", regex=True)

    df = df.dropna(subset=["date", "food_item", *[c for c in numeric_cols if c in df.columns]])
    return df


df = load_data(data_path)

if df.empty:
    st.warning("No valid records were found in the dataset.")
    st.stop()

st.sidebar.header("🎯 Dashboard Controls")
food_items = sorted(df["food_item"].unique())
selected_items = st.sidebar.multiselect(
    "Select food items",
    options=food_items,
    default=food_items,
    help="Filter the analysis to the dishes you want to study.",
)

if not selected_items:
    st.warning("Please choose at least one food item to continue.")
    st.stop()

filtered_df = df[df["food_item"].isin(selected_items)].copy()
filtered_df["date_only"] = filtered_df["date"].dt.date

# Daily aggregation for viewing and date-specific insights

daily_report = (
    filtered_df.groupby("date", as_index=False)
    .agg(
        prepared_quantity=("prepared_quantity", "sum"),
        consumed_quantity=("consumed_quantity", "sum"),
        wasted_quantity=("wasted_quantity", "sum"),
    )
)

daily_report["waste_rate"] = (
    daily_report["wasted_quantity"] / daily_report["prepared_quantity"] * 100
).where(daily_report["prepared_quantity"] > 0, 0)
daily_report["consumed_rate"] = (
    daily_report["consumed_quantity"] / daily_report["prepared_quantity"] * 100
).where(daily_report["prepared_quantity"] > 0, 0)

daily_report = daily_report.sort_values("date").reset_index(drop=True)

selected_date = st.sidebar.selectbox(
    "Select date",
    options=daily_report["date"].tolist(),
    index=len(daily_report["date"]) - 1,
    help="Choose a date to see that day's prepared, consumed, wasted quantities and percentage rates.",
)

selected_day = daily_report[daily_report["date"] == selected_date].iloc[0]

prepared = selected_day["prepared_quantity"]
consumed = selected_day["consumed_quantity"]
wasted = selected_day["wasted_quantity"]
selected_waste_rate = selected_day["waste_rate"]
selected_consumed_rate = selected_day["consumed_rate"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("🍲 Prepared", f"{prepared:,.0f} kg")
col2.metric("🥗 Consumed", f"{consumed:,.0f} kg")
col3.metric("🚯 Wasted", f"{wasted:,.0f} kg")
col4.metric("📉 Waste Rate", f"{selected_waste_rate:.1f}%")

st.markdown("---")
st.subheader(f"📅 Daily Overview for {selected_date.strftime('%d %b %Y')}")

rate_df = pd.DataFrame({
    "Metric": ["Waste Rate", "Consumed Rate"],
    "Percentage": [selected_waste_rate, selected_consumed_rate],
})

rate_fig = px.bar(
    rate_df,
    x="Metric",
    y="Percentage",
    color="Metric",
    title="Waste and Consumption Rate for Selected Date",
    color_discrete_map={
        "Waste Rate": "#FF6B6B",
        "Consumed Rate": "#4CAF50",
    },
    text_auto='.1f',
)
rate_fig.update_layout(template="plotly_white", showlegend=False, xaxis_title="", yaxis_title="Percentage (%)")
st.plotly_chart(rate_fig, use_container_width=True)

st.subheader("📈 Daily Food Quantity Trend")
chart_df = daily_report.copy()
chart_df["date_label"] = chart_df["date"].dt.strftime("%d %b")

fig_daily = px.bar(
    chart_df,
    x="date_label",
    y=["prepared_quantity", "consumed_quantity", "wasted_quantity"],
    barmode="group",
    title="Prepared, Consumed, and Wasted Food by Date",
    color_discrete_sequence=["#5B8DEF", "#4CAF50", "#FF6B6B"],
    labels={"date_label": "Date", "value": "Quantity (kg)"},
)
fig_daily.update_layout(template="plotly_white", xaxis_tickangle=-30)
st.plotly_chart(fig_daily, use_container_width=True)

st.subheader("📌 Executive Summary")
summary_col1, summary_col2 = st.columns(2)
with summary_col1:
    st.info(
        f"On {selected_date.strftime('%d %b %Y')}, the canteen prepared {prepared:,.0f} kg of food, consumed {consumed:,.0f} kg, and discarded {wasted:,.0f} kg. "
        f"This resulted in a consumption rate of {selected_consumed_rate:.1f}% and a waste rate of {selected_waste_rate:.1f}%.")
with summary_col2:
    st.success(
        "Insight: Daily preparation should be adjusted to match actual demand, especially on days with higher waste percentages."
    )

st.subheader("📅 Daily Overview")
daily_view = (
    filtered_df.groupby("date", as_index=False)
    .agg(
        prepared_quantity=("prepared_quantity", "sum"),
        consumed_quantity=("consumed_quantity", "sum"),
        wasted_quantity=("wasted_quantity", "sum"),
    )
)

daily_view["waste_rate"] = (
    (daily_view["wasted_quantity"] / daily_view["prepared_quantity"] * 100)
    .where(daily_view["prepared_quantity"] > 0, 0)
)

daily_view["consumed_rate"] = (
    (daily_view["consumed_quantity"] / daily_view["prepared_quantity"] * 100)
    .where(daily_view["prepared_quantity"] > 0, 0)
)

daily_view = daily_view.sort_values("date").reset_index(drop=True)

fig_daily_overview = px.bar(
    daily_view,
    x="date",
    y=["prepared_quantity", "consumed_quantity", "wasted_quantity"],
    barmode="group",
    title="Daily Prepared, Consumed and Wasted Food",
    color_discrete_sequence=["#5B8DEF", "#4CAF50", "#FF6B6B"],
)
fig_daily_overview.update_layout(template="plotly_white", xaxis_tickangle=-30)
st.plotly_chart(fig_daily_overview, use_container_width=True)

st.subheader("📋 Daily Report Table")
report_table = daily_report.rename(columns={
    "date": "Date",
    "prepared_quantity": "Prepared (kg)",
    "consumed_quantity": "Consumed (kg)",
    "wasted_quantity": "Wasted (kg)",
    "waste_rate": "Waste Rate (%)",
    "consumed_rate": "Consumed Rate (%)",
})
st.dataframe(report_table, use_container_width=True)

st.subheader("📊 Food Waste by Item")
item_summary = (
    filtered_df.groupby("food_item", as_index=False)
    .agg(
        consumed_quantity=("consumed_quantity", "sum"),
        wasted_quantity=("wasted_quantity", "sum"),
    )
)

fig_item = px.bar(
    item_summary,
    x="food_item",
    y=["consumed_quantity", "wasted_quantity"],
    barmode="group",
    title="Consumed vs Wasted Quantity by Food Item",
    color_discrete_sequence=["#4CAF50", "#FF6B6B"],
)
fig_item.update_layout(template="plotly_white", xaxis_tickangle=-30)
st.plotly_chart(fig_item, use_container_width=True)

csv_report = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download Filtered Waste Report",
    data=csv_report,
    file_name="canteen_food_waste_report.csv",
    mime="text/csv",
)

st.markdown("---")
st.caption("Built for sustainable campus operations, data-driven planning, and smarter food management.")
