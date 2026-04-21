import streamlit as st
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from streamlit_echarts import st_echarts
from viz_utils import load_config

st.set_page_config(layout="wide")

def perform_clustering(df, cluster_cols, n_clusters=4):
    df_clean = df[cluster_cols].fillna("None").astype(str)
    encoder = OneHotEncoder(sparse_output=False)
    X_encoded = encoder.fit_transform(df_clean)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_encoded)

    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)

    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)

    # ✅ 保留原始配置列以供后续分析使用
    result_df = df[["车型", "厂商", "配置名称"] + cluster_cols].copy()
    result_df["cluster"] = clusters
    result_df["pca_x"] = X_pca[:, 0]
    result_df["pca_y"] = X_pca[:, 1]
    return result_df, kmeans

def analyze_cluster_compositions(cluster_result_df, cluster_cols):
    cluster_compositions = {}
    for cluster_label in cluster_result_df['cluster'].unique():
        # 当前聚类数据
        cluster_data = cluster_result_df[cluster_result_df['cluster'] == cluster_label]

        # 提取聚类所用的特征列
        cluster_configs = cluster_data[cluster_cols]

        # 如果该聚类为空，跳过
        if cluster_configs.empty:
            cluster_compositions[cluster_label] = ["无有效配置"]
            continue

        # 统计每种配置组合的频次
        config_combinations = cluster_configs.groupby(cluster_cols).size().reset_index(name='count')

        # 如果组合结果为空，跳过
        if config_combinations.empty:
            cluster_compositions[cluster_label] = ["无有效配置组合"]
            continue

        # 选出出现最多的组合
        most_common_config = config_combinations.sort_values(by='count', ascending=False).iloc[0]
        cluster_compositions[cluster_label] = most_common_config[cluster_cols].values.tolist()

    return cluster_compositions


def render_cluster_analysis(df):
    st.markdown("###### 配置组合聚类分析")
    cluster_cols = ["辅助驾驶芯片", "激光雷达品牌", "激光雷达数量(个)", "车外摄像头数量(个)", "毫米波雷达数量(个)", "亚米级高精定位系统"]
    cluster_result_df, _ = perform_clustering(df, cluster_cols, n_clusters=4)

    # 获取每个聚类的典型配置组合
    cluster_compositions = analyze_cluster_compositions(cluster_result_df, cluster_cols)

    # 输出每个聚类的典型配置组合
    for cluster_label, config_combination in cluster_compositions.items():
        st.markdown(f"**Cluster {cluster_label}:** 典型配置组合: {', '.join([str(x) for x in config_combination])}")
    series = []
    for c in cluster_result_df['cluster'].unique():
        points = cluster_result_df[cluster_result_df['cluster'] == c][['pca_x', 'pca_y']].values.tolist()
        series.append({
            "name": f"Cluster {c}",
            "type": "scatter",
            "data": points
        })

    option = {
        "tooltip": {"trigger": "item"},
        "xAxis": {},
        "yAxis": {},
        "series": series
    }
    st_echarts(option, height="400px")


st.title("智能驾驶硬件配置分析")
df = load_config()
df = df.dropna(subset=["辅助驾驶芯片"])
render_cluster_analysis(df)
