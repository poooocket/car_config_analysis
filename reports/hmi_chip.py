import streamlit as st
import pandas as pd
from viz_utils import calculate_sanky_data, viz_sankey, load_config, plot_penetration_by_year, plot_penetration_by_price, run_style
import numpy as np

def render_sanky(sankey_cols, df):   
    df = df.dropna(subset=sankey_cols[1])
    for col in sankey_cols:
        df[col] = df[col].astype(str).str.replace(r"\s+", "", regex=True).replace("nan", "None")
    sankey_data, _ = calculate_sanky_data(df, *sankey_cols)
    value = viz_sankey(sankey_data, colors, height=sankey_height)
    return value


# 页面设置
st.set_page_config(page_title="车载智能芯片", layout="wide")
st.markdown("##### 车载智能芯片")
run_style()

percentage_height = 238
sankey_height = "542px"
colors = ["#8475F5"]*5


# 读取数据
config = load_config()


config['语音分区域唤醒识别功能'] = config['语音分区域唤醒识别功能'].replace({"●第二排 ●主驾驶 ●副驾驶":"●主驾驶 ●副驾驶 ●第二排"})
config['中控台彩色屏幕分辨率'] = config['中控台彩色屏幕分辨率'].replace({"2k":"2K", "2.5":"2.5K", "3.5":"3.5K"})


df = config[["车型", "年款", "配置名称", "价格区间(万)", "厂商", "车载智能芯片", "车机系统内存(GB)", "车机系统存储(GB)"]]
df.loc[:, "has_hmi_chip"] = df["车载智能芯片"].notna().astype(int)

pannels = st.columns([1,2])
# 车载芯片渗透率
with pannels[0]:
    with st.container(border=True): 
        st.markdown("###### 车载智能芯片渗透率(按年款)")
        year = plot_penetration_by_year(df, "has_hmi_chip", percentage_height=percentage_height, key="hmi_chip_year")

    with st.container(border=True): 
        st.markdown("###### 车载智能芯片渗透率(按价格)")
        price_range = plot_penetration_by_price(df, "has_hmi_chip", percentage_height=percentage_height, key="hmi_chip_price")
    
# 配置选型
with pannels[1]:     
    with st.container(border=True):
        cols = st.columns([4,1])
        cols[0].markdown("###### 厂商车载智能芯片选型")
        sankey_cols = ["厂商", "车载智能芯片", "车机系统内存(GB)"]
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


