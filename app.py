import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
page_title="Canteen Food Waste Analyzer",
page_icon="🍽️",
layout="wide"
)

st.title("🍽️ College Canteen Food Waste Analyzer")
st.write("Analyze food preparation, consumption and waste.")

# Load CSV data

data_path = Path(__file__).parent / "data" / "canteen_food_waste.csv"
df = pd.read_csv(data_path)

# Convert quantity columns to numeric values

quantity_columns = [
"prepared_quantity",
"consumed_quantity",
"wasted_quantity"
]

for column in quantity_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = df.dropna(subset=quantity_columns)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["date", "food_item"])

# Sidebar filter

st.sidebar.header("Filters")
food_items = sorted(df["food_item"].unique())

selected_items = st.sidebar.multiselect(
"Choose food items",
food_items,
default=food_items
)

filtered_df = df[df["food_item"].isin(selected_items)]

if filtered_df.empty:
    st.warning("Please select at least one food item.")
    st.stop()

# Summary calculations

prepared = filtered_df["prepared_quantity"].sum()
consumed = filtered_df["consumed_quantity"].sum()
wasted = filtered_df["wasted_quantity"].sum()

waste_rate = wasted / prepared * 100 if prepared > 0 else 0

# Display metric cards

col1, col2, col3, col4 = st.columns(4)

col1.metric("Food Prepared", f"{prepared:,.0f}")
col2.metric("Food Consumed", f"{consumed:,.0f}")
col3.metric("Food Wasted", f"{wasted:,.0f}")
col4.metric("Waste Rate", f"{waste_rate:.1f}%")

# Chart 1: Waste by food item

st.subheader("📊 Food Waste by Item")

item_summary = filtered_df.groupby("food_item", as_index=False)[
["consumed_quantity", "wasted_quantity"]
].sum()

fig1 = px.bar(
item_summary,
x="food_item",
y=["consumed_quantity", "wasted_quantity"],
barmode="group",
title="Consumed vs Wasted Quantity"
)

st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Daily waste

st.subheader("📈 Daily Food Waste Trend")

daily_summary = filtered_df.groupby("date", as_index=False)[
"wasted_quantity"
].sum()

fig2 = px.line(
daily_summary,
x="date",
y="wasted_quantity",
markers=True,
title="Waste per Day"
)

st.plotly_chart(fig2, use_container_width=True)

# Records table

st.subheader("📋 Food Waste Records")
st.dataframe(filtered_df, use_container_width=True)

# Download report

csv_report = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
"Download CSV Report",
data=csv_report,
file_name="canteen_food_waste_report.csv",
mime="text/csv"
)

