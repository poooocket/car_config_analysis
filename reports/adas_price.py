import streamlit as st
import pandas as pd
from viz_utils import calculate_sanky_data, viz_sankey, load_config, plot_penetration_by_year, plot_penetration_by_price, run_style
import re
    

def extract_price(text): 
    """
    从特色配置文本中提取价格
    """

    price_matches = re.findall(r'(\d+元/年|\d+/月|选配\d+元)', text)
    
    # 如果匹配到价格，返回价格，否则返回 '暂无价格' 或 NaN
    if price_matches:
        return ', '.join(price_matches)  # 提取价格数值部分并转成整数
    elif '选配暂无价格' in text:
        return None
    else:
        return None  # 对于没有价格的情况返回 NaN

def extract_integers(text):
# 只匹配整数部分
    if text:
        price = re.findall(r'\d+', text)
        if price:
            return re.findall(r'\d+', text)
        else:
            return None
    else:
        return None
    
def render_sanky(sankey_cols, df):   
    df = df.dropna(subset=sankey_cols[2])
    for col in sankey_cols:
        df[col] = df[col].astype(str).str.replace(r"\s+", "", regex=True).replace("nan", "None")
    sankey_data, _ = calculate_sanky_data(df, *sankey_cols)
    value = viz_sankey(sankey_data, colors, height=sankey_height)
    return value

######################################################################

st.set_page_config(page_title="智驾包价格策略", layout="wide")
st.markdown("##### 智驾包价格策略")
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
config["激光雷达品牌"] = config["激光雷达品牌"].replace("RoboSense速腾聚创", "速腾聚创")
config["激光雷达线数(线)"] = config["激光雷达线数(线)"].replace("○96", "96").replace("○128", "128").replace( "○120 ○128", "128")

unique_feature = pd.read_csv("data/unique_feature.csv")
unique_feature["特色功能"] =  unique_feature["特色功能"].replace("ZEEKR AD 完全智能驾驶辅助系统", "ZEEKR AD完全智能驾驶辅助系统")
unique_feature = unique_feature.dropna(subset=['功能内容'])
unique_feature["选配价格"] = unique_feature["功能内容"].apply(extract_price)
unique_feature["选配价格_2"] = unique_feature["特色功能"].apply(extract_price)
unique_feature["选配价格"] = unique_feature["选配价格"].combine_first(unique_feature["选配价格_2"])
unique_feature["价格提取"] = unique_feature["选配价格"].apply(extract_integers)

unique_feature = unique_feature.reindex(columns=['厂商','车型', '年款', '配置名称', '官方指导价(万)','特色功能','价格提取','选配价格','功能内容'])
unique_feature = unique_feature.rename(columns={"特色功能": "辅助驾驶套餐"})

keywords = ['辅助', "驾驶", "智驾", "领航", "ADAS", "Pilot", "安心", "自动泊车"]
pattern = "|".join(keywords)
adas_package_df = unique_feature[unique_feature["辅助驾驶套餐"].str.contains(pattern)]

df = config[["厂商", "年款", "车型", "配置名称", "官方指导价(万)", "价格区间(万)"]]
# 合并数据（只保留在adas_packege_df中存在的匹配项）
df = df.merge(
    adas_package_df[["车型", "配置名称", "辅助驾驶套餐", "价格提取", "选配价格", "功能内容"]],
    on=["车型", "配置名称"],
    how="left"
)

df.loc[:, "has_adas_package"] = df["辅助驾驶套餐"].notna().astype(int)

pannels = st.columns([1,2])
    
# 年款渗透率折线图
with pannels[0]:
    with st.container(border=True):
        st.markdown("###### 辅助驾驶套餐片渗透率（按年款）")
        year = plot_penetration_by_year(df, "has_adas_package", percentage_height=percentage_height, key="adas_chip_year")
    
    
    with st.container(border=True):
        st.markdown("###### 辅助驾驶套餐渗透率（按价格区间）") 
        price_range = plot_penetration_by_price(df, "has_adas_package", percentage_height=percentage_height, key="adas_chip_price")

# 配置选型
with pannels[1]:     
    with st.container(border=True):
        cols = st.columns([4,1])
        cols[0].markdown("###### 厂商辅助驾驶套餐价格策略")
        sankey_cols = ["厂商", "选配价格", "辅助驾驶套餐" ]
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
    filtered_df = df[df["价格区间(万)"] == price_range]
    with sankey_holder:
        value = render_sanky(sankey_cols, filtered_df)
        

if value and isinstance(value, str) and re.search(pattern, value, flags=re.IGNORECASE):
    matched_rows = filtered_df[filtered_df["辅助驾驶套餐"] == value]
    matched_contents = matched_rows["功能内容"].dropna().unique().tolist()
    if matched_contents:
        st.markdown(f"###### {value}")
        st.text("\n\n".join(matched_contents))
    else:
        st.text(value)
else:
    st.text(value)


