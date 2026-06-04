import streamlit as st
from viz_utils import run_style, load_config

#设置页面
st.set_page_config(page_title="车型配置", layout="wide")
st.markdown("##### 车型配置")
run_style()

# 读取数据
df = load_config()
df["车型信息"] = (
    df["车型"].fillna("").astype(str) + " " +
    df["年款"].fillna("").astype(str) + " " +
    df["配置名称"].fillna("").astype(str)
).str.strip()

model = st.selectbox("选择车型", options=df["车型信息"].drop_duplicates().tolist(), index=None, placeholder="选择车型", label_visibility="collapsed") 
if model:
    selected_row = df[df["车型信息"] == model].iloc[0]
    config_df = (
        selected_row
        .drop(["车型", "年款", "配置名称", "车型信息"])
        .reset_index()
    )
    
    config_df.columns = ["配置名称", "配置值"]
    config_df = config_df.dropna(subset=["配置值"])
    st.dataframe(config_df, height=600, hide_index=True, use_container_width=True)