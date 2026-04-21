import plotly.express as px
import streamlit as st
from viz_utils import run_style, load_config
import pandas as pd
from streamlit_echarts import st_echarts


# 页面设置
st.set_page_config(page_title="年款价格", layout="wide")
st.markdown("##### 年款价格")
run_style()

config = load_config()

df_grouped = config.groupby(['年款', '价格区间(万)']).size().reset_index(name='车型数量')

x_data = sorted(df_grouped["年款"].unique().tolist())
price_ranges = sorted(df_grouped["价格区间(万)"].unique().tolist())

# 构造 series 数据
series_data = {}
for price in price_ranges:
    counts = []
    for year in x_data:
        row = df_grouped[(df_grouped["年款"] == year) & (df_grouped["价格区间(万)"] == price)]
        count = int(row["车型数量"].values[0]) if not row.empty else 0
        counts.append(count)
    series_data[price] = counts

# 构建 series
series = [
    {
        "name": price,
        "type": "bar",
        "stack": "total",
        "emphasis": {"focus": "series"},
        "data": series_data[price],
    }
    for price in price_ranges
]


option = {
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "legend": {"data": price_ranges},
    "xAxis": {"type": "category", "data": x_data},
    "yAxis": {"type": "value"},
    "series": series
}

events = {
    "click": "function(params) { return {year: params.name, price: params.seriesName}; }"
}

selected = st_echarts(option, events=events, height="500px")
if selected and "year" in selected and "price" in selected:
    year = selected["year"]
    price = selected["price"]
    filtered_df = df[(df["年款"] == year) & (df["价格区间(万)"] == price)]
    st.text(f"{year}年，价格区间：{price}，共{len(filtered_df)}条")
    st.dataframe(filtered_df)
else:
    st.caption("点击图表以筛选数据")

