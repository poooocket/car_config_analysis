import streamlit as st
import pandas as pd
from viz_utils import calculate_sanky_data, viz_sankey, load_config, plot_penetration_by_year, plot_penetration_by_price, run_style
import re
import numpy as np

def render_sanky(sankey_cols, df):   
    df = df.dropna(subset=sankey_cols[2])
    for col in sankey_cols:
        df[col] = df[col].fillna(f"暂无{col}")
        df[col] = df[col].astype(str).str.replace(r"\s+", "", regex=True).replace("nan", "None")
    sankey_data, _ = calculate_sanky_data(df, *sankey_cols)
    value = viz_sankey(sankey_data, colors, height=sankey_height)
    return value


st.set_page_config(page_title="激光雷达", layout="wide")
st.markdown("##### 激光雷达")
run_style()

percentage_height = 238
sankey_height = "542px"
colors = ["#8475F5"]*5



config = load_config()

def clean_text(text):
    if pd.isna(text):
        return text
    text = re.sub(r'NVIDIA DRIVE Orin[- ]?X', 'NVIDIA DRIVE Orin X', text)
    return text
config["辅助驾驶芯片"] = config["辅助驾驶芯片"].apply(clean_text)

def remove_price_part(text):
    if pd.isna(text):
        return text
    text = re.sub(r'\s*○?\d+.*?元.*$', '', text)
    return text.strip()
config["车外摄像头数量(个)"] = config["车外摄像头数量(个)"].apply(remove_price_part)
config["激光雷达品牌"] = config["激光雷达品牌"].replace("RoboSense速腾聚创", "速腾聚创").replace("HUAWEI华为", "华为")
config["激光雷达线数(线)"] = config["激光雷达线数(线)"].replace("○96", "96").replace("○128", "128").replace( "○120 ○128", "128")
config["激光雷达数量(个)"] = config["激光雷达数量(个)"].replace("○18000元", "1").replace("○2", "2").replace("○3", "3")

df = config[["厂商", "年款", "车型", "配置名称", "官方指导价(万)", "激光雷达品牌", "激光雷达数量(个)", "激光雷达线数(线)", "激光雷达点云数量(万/秒)", "价格区间(万)"]]
df["has_lidar"] = df["激光雷达品牌"].notna().astype(int)
pannels = st.columns([1,2])

# 年款渗透率折线图
with pannels[0]:
    with st.container(border=True):
        st.markdown("###### 激光雷达渗透率（按年款）")
        year = plot_penetration_by_year(df, "has_lidar", percentage_height=percentage_height, key="lidar_year")

    with st.container(border=True):
        st.markdown("###### 激光雷达渗透率（按价格区间）")
        price_range = plot_penetration_by_price(df, "has_lidar", percentage_height=percentage_height, key="lidar_price")
    
        
    
# 配置选型
with pannels[1]:  
    with st.container(border=True):
        cols = st.columns([4,1])
        cols[0].markdown("###### 厂商激光雷达选型")
        sankey_cols = ["激光雷达数量(个)", "厂商", "激光雷达品牌", "激光雷达线数(线)", "激光雷达点云数量(万/秒)"]
        sankey_caption = " ".join([f":grey-badge[{col_name}]" for col_name in sankey_cols])
        st.markdown(sankey_caption)
        sankey_holder = st.empty()
        with cols[1]:
            filter_holder = st.empty() 

filtered_df = df.copy()
filter_holder.markdown(f":violet-badge[所有车型]" )
with sankey_holder:
    value = render_sanky(sankey_cols, filtered_df)

if year is not None:
    filtered_df = df[df["年款"] == str(year)]
    filter_holder.markdown(f":violet-badge[年款：{year}]" )
    with sankey_holder:
        value = render_sanky(sankey_cols, filtered_df)

if price_range is not None:
    filtered_df = df[df["价格区间(万)"] == price_range]
    filter_holder.markdown(f":violet-badge[价格区间：{price_range}]" )
    with sankey_holder:
        value = render_sanky(sankey_cols, filtered_df)



