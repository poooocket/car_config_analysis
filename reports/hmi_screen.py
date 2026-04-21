import streamlit as st
import pandas as pd
from viz_utils import calculate_sanky_data, viz_sankey, load_config, plot_penetration_by_year, plot_penetration_by_price, run_style
import numpy as np


def render_sanky(sankey_cols, df):   
    df = df.dropna(subset=sankey_cols[:2])
    for col in sankey_cols:
        df[col] = df[col].astype(str).str.replace(r"\s+", "", regex=True).replace("nan", "None")
    sankey_data, _ = calculate_sanky_data(df, *sankey_cols)
    value = viz_sankey(sankey_data, colors, height=sankey_height)
    return value


# 页面设置
st.set_page_config(page_title="中控屏", layout="wide")
st.markdown("##### 中控屏")
run_style()

percentage_height = 238
sankey_height = "542px"
colors = ["#8475F5"]*5


# 读取数据
config = load_config()

config['语音分区域唤醒识别功能'] = config['语音分区域唤醒识别功能'].replace({"●第二排 ●主驾驶 ●副驾驶":"●主驾驶 ●副驾驶 ●第二排"})
config['中控台彩色屏幕分辨率'] = config['中控台彩色屏幕分辨率'].replace({"2k":"2K", "2.5":"2.5K", "3.5":"3.5K"})

    
df = config[["车型", "年款", "配置名称", "价格区间(万)", "厂商", "中控屏尺寸(英寸)", "中控屏幕材质", "中控台彩色屏幕分辨率", "中控台彩色屏幕像素密度（PPI）"]]
df.loc[:, "has_screen"] = df["中控屏尺寸(英寸)"].notna().astype(int)
pannels = st.columns([1,2])
# 中控屏渗透率
with pannels[0]:
    with st.container(border=True): 
        st.markdown("###### 中控屏渗透率(按年款)")
        year = plot_penetration_by_year(df, "has_screen", percentage_height=percentage_height, key="screen_year")
        
    with st.container(border=True): 
        st.markdown("###### 中控屏渗透率(按价格)")
        price_range = plot_penetration_by_price(df, "has_screen", percentage_height=percentage_height, key="screen_price")

with pannels[1]:     
    with st.container(border=True):
        cols = st.columns([4,1])
        cols[0].markdown("###### 厂商中控屏选型")
        sankey_cols = ["厂商", "中控屏幕材质", "中控屏尺寸(英寸)", "中控台彩色屏幕分辨率"]
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



