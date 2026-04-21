import streamlit as st

data_overview = st.Page( "reports/data_overview.py", title="数据概览", icon=":material/dashboard:", default=True)
data_explore = st.Page( "reports/data_explore.py", title="数据分布", icon=":material/search:")

adas_chip = st.Page( "reports/adas_chip.py", title="辅助驾驶芯片", icon=":material/memory:")
lidar = st.Page("reports/lidar.py", title="激光雷达", icon=":material/sensors:")
adas_package= st.Page("reports/adas_package.py", title="智驾硬件套装", icon=":material/manufacturing:")
adas_price= st.Page("reports/adas_price.py", title="智驾包价格策略", icon=":material/strategy:")
# cluster= st.Page("reports/cluster.py", title="聚类分析", icon=":material/strategy:")

hmi_chip = st.Page("reports/hmi_chip.py", title="车载智能芯片", icon=":material/memory:")
hmi_screen = st.Page("reports/hmi_screen.py", title="中控屏", icon=":material/call_to_action:")
voice_interaction = st.Page("reports/voice_interaction.py", title="语音交互", icon=":material/mic:")
visual_recognition = st.Page("reports/visual_recognition.py", title="车内视觉识别", icon=":material/center_focus_weak:")


pg = st.navigation(
    {
        "数据概览":[data_overview, data_explore],
        "智驾域": [adas_chip, lidar, adas_package, adas_price],
        "座舱域": [hmi_chip, hmi_screen, voice_interaction, visual_recognition],
    }
)

pg.run()


