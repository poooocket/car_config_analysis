import streamlit as st
from streamlit_echarts import st_echarts
import pandas as pd
from viz_utils import run_style, load_config
import numpy as np

    
#设置页面
st.set_page_config(page_title="数据分布", layout="wide")
st.markdown("##### 数据分布")
run_style()


# 读取数据
df = load_config()


missing_path = "data/missing_data.csv"
missing_data = pd.read_csv(missing_path)

with st.container(border=True): 
    cols = st.columns([3,5,1])
with cols[0]:
    filed = st.selectbox("选择列名探索", options=[col for col in df.columns], index=0, placeholder="选择列名探索", label_visibility="collapsed") 
   
with cols[2]:
    missing_data_holder = st.empty()

with st.container(border=True):    
    bar_container = st.empty()

with st.container(border=True):
    df_caption_holder = st.empty()
    df_holder = st.empty()
    rows_holder = st.empty()

if filed:
    col_data = df[filed].value_counts().sort_index()
    col_missing_percentage = missing_data.loc[missing_data["class"] == filed, 'missing_percentage'].iloc[0]
    col_missing_percentage = round(col_missing_percentage, 2)

    
    missing_data_holder.text(f"缺失值比例 \n{col_missing_percentage}%")

    # x_data为类别，y_data为频次
    x_data = col_data.index.tolist()
    y_data = col_data.values.tolist()

    # ECharts 数据格式
    option = {
        "xAxis": {
            "type": "category",
            "data": x_data,  # 类别名称
        },
        "yAxis": {
            "type": "value",
        },
        "series": [
            {
                "data": y_data,  # 每个类别的频次
                "type": "bar",
                "itemStyle": {
                    "color": "#8475F5",
                },
            }
        ],
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
                }
        } 
    }
    events = {
        "click": "function(params) { console.log(params.name); return params.name }"
    }

    with bar_container:
        value = st_echarts(option, events=events, height="326px")
    
    if value:
        if df[filed].dtype in ['int64', 'float64']:
            value = float(value)
        clicked_rows = df[df[filed].astype(str) == str(value)]
        df_caption_holder.markdown(f":violet-badge[{filed}：{value}]")
      
        basic_cols_to_show = ["厂商", "车型", "年款", "配置名称", "官方指导价(万)"]
        if filed in basic_cols_to_show:
            cols_to_show = basic_cols_to_show
        else:
            cols_to_show = basic_cols_to_show + [filed]
        df_holder.dataframe(clicked_rows[cols_to_show], hide_index=True, use_container_width=True)
        rows_holder.caption(f"共 {len(clicked_rows)} 条")

    else:
        df_caption_holder.caption("点击图表以筛选数据")

