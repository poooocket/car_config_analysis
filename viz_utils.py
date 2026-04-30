import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts



# def cut_range(df, bins, original_col, new_col):
#     df[new_col] = pd.cut(df[original_col], bins=bins) 
#     df[new_col] = df[new_col].apply(lambda x: f"{int(x.left)}-{int(x.right)}" if pd.notnull(x) else "Unknown")
#     df.insert(df.columns.get_loc(original_col) + 1, new_col, df.pop(new_col))
#     return df

def cut_range(df, bins, original_col, new_col):
    # 分箱（右闭区间）
    df[new_col] = pd.cut(
        df[original_col],
        bins=bins,
        right=False,  # 区间左闭右开 [)
        include_lowest=True
    )
    
    # 自定义 label：最后一个为“35以上”
    labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-2)] + [f"{int(bins[-2])}以上"]
    
    df[new_col] = pd.cut(
        df[original_col],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True
    )
    
    # 插入列位置
    df.insert(df.columns.get_loc(original_col) + 1, new_col, df.pop(new_col))
    return df

def calculate_sanky_data(df, *cols):
    """
    根据传入的列数量动态生成 source 和 target 节点。
    *cols：可变参数，使函数可以处理不同数量的列。
	使用动态索引来处理不同列之间的交叉表。
    """
    
    cross_tabs = [pd.crosstab(df[cols[i]], df[cols[i+1]]) for i in range(len(cols) - 1)] # 生成交叉表
    links = [ct.stack().reset_index() for ct in cross_tabs] # 重置索引并堆叠
    
    # 为每个链接分配列名
    for i, link in enumerate(links):
        link.columns = [cols[i], cols[i+1], 'value']
        # st.write(link)
        
    # 合并和处理 NaN 值
    for link in links:
        link.dropna(subset=[link.columns[1]], inplace=True)
        link[link.columns[1]] = link[link.columns[1]].astype(str)
    links = [link[link['value'] > 0] for link in links]

    # 获取唯一节点
    source_nodes = pd.Series(np.concatenate([links[i][cols[i]].astype(str) for i in range(len(cols) - 1)])).unique()
    target_nodes = pd.Series(np.concatenate([links[i][cols[i+1]].astype(str) for i in range(len(cols) - 1)])).unique()
    nodes = pd.DataFrame(np.unique(np.concatenate([source_nodes, target_nodes])), columns=['name'])
    
    # 创建链接字典，增加存在性检查，并包含所有必要的列
    links_dict = []
    for i, link_group in enumerate(links):
        for link in link_group.to_dict(orient='records'):
            if 'value' in link:
                links_dict.append({'source': link[cols[i]], 'target': link[cols[i+1]], 'value': link['value']})

    # 构造最终的 Sankey 数据
    sankey_data = {"nodes": nodes.to_dict(orient='records'), "links": links_dict}
    return sankey_data, links


def viz_sankey(sankey_data, colors, height):  
    """
    可视化桑基图
    sankey_data: 传入的桑基图数据
    colors: 颜色列表
    动态生成 levels，根据 colors 的长度决定深度
    """
    
    levels = [
        {
            "depth": i,
            "itemStyle": {"color": colors[i]},
            "lineStyle": {"color": "source", "opacity": 0.2},
        }
        for i in range(len(colors))
    ]
    
    option = { 
        "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
        "series": [
            {
                "type": "sankey",
                "data": sankey_data["nodes"],
                "links": sankey_data["links"],
                "emphasis": {"focus": "adjacency"},
                "levels": levels,  # 使用动态生成的 levels
                "lineStyle": {"curveness": 0.5},
                "label": {"color": "#5F6379", "fontSize": 12},
            }
        ],
    }
    
    events = {
        "click": "function(params) { console.log(params.name); return params.name }"
    }
    
    value = st_echarts(option, events=events, height=height)
    return value

    
def viz_legend(colors, *cols):
    """
    可视化图例
    colors: 颜色列表
    cols: 列名列表
    """
    # 创建一个存储每个颜色和列名的 HTML 片段列表
    legend_items = []
    for i, col in enumerate(cols):
        legend_items.append(f"""
            <div style='display: flex; align-items: center; margin-right: 20px;'>
                <div style="width: 16px; height: 16px; border-radius: 2%; background-color: {colors[i]}; margin-right: 8px;"></div>
                <span>{col}</span>
            </div>
        """.strip())
    
    # 将所有项目合并成一个字符串
    legend_html = "".join(legend_items)
    
    # 最终的 HTML 布局
    st.markdown(f"""
        <div style='text-align: center; font-size: 14px; display: flex; justify-content: center;'>
            {legend_html}
        </div>
    """.strip(), 
    unsafe_allow_html=True)


def build_tree_data(df, root_name, columns, value_column):   
    """
    递归构建JSON的函数
    df: 数据框
    root_name: 根节点名称
    columns: 列名列表
    value_column: 值列名称
    """ 
    def recursive_build(data, depth):
        if depth == len(columns) - 1:
            # 递归的最后一层，返回当前深度下的叶节点
            return [{"name": row[columns[depth]], "value": row[value_column]} for _, row in data.iterrows()]
        else:
            grouped = data.groupby(columns[depth])
            children = []
            for group_name, group_data in grouped:
                children.append({
                    "name": group_name,
                    "children": recursive_build(group_data, depth + 1)
                })
            return children

    # 初始化从第一层开始递归构建
    return {
        "name": root_name,
        "children": recursive_build(df, 0)
    }

def viz_tree(json_data, height="800px"):
    """
    可视化树形图
    json_data: JSON 数据
    height: 图表高度
    """

    # for idx, _ in enumerate(json_data["children"]):
    #     json_data["children"][idx]["collapsed"] = idx % 2 == 0

    option = {
        "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
        "series": [
            {
                "type": "tree",
                "data": [json_data],
                "top": "1%",
                "left": "7%",
                "bottom": "1%",
                "right": "20%",
                "symbolSize": 10,
                "label": {
                    "position": "left",
                    "verticalAlign": "middle",
                    "align": "right",
                    "fontSize": 12,
                },
                "leaves": {
                    "label": {
                        "position": "right",
                        "verticalAlign": "middle",
                        "align": "left",
                    }
                },
                "emphasis": {"focus": "descendant"},
                "expandAndCollapse": False,
                "animationDuration": 550,
                "animationDurationUpdate": 750,
            }
        ],
    }
    # events = {
    #     "click": "function(params) { console.log(params.name); return params.name }"
    # }
    
    # value = st_echarts(option, events=events, height=height)
    # return value
    st_echarts(option, height=height)



def plot_penetration_by_year(df, col_name, percentage_height, key="line_chart"):
    penetration_by_year = df.groupby("年款")[col_name].mean().reset_index()
    penetration_by_year["渗透率"] = (penetration_by_year[col_name] * 100).round(1)

    option = {
        
        "tooltip": {"trigger": "axis"},
        "legend": {"textStyle": {"fontSize": 12}},
        "xAxis": {
            "type": "category",
            "data": list(penetration_by_year["年款"]),
            "axisLabel": {"fontSize": 12}
        },
        "yAxis": {
            "type": "value",
            "name": "渗透率 (%)",
            "axisLabel": {"fontSize": 12}
        },
        "series": [{
            "data": list(penetration_by_year["渗透率"]),
            "type": "line",
            "smooth": True,
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}%",
                "fontSize": 12
            },
            "lineStyle": {"color": "#8475F5"},
            "itemStyle": {"color": "#8475F5"}
        }],
        "grid": {"top": 60, "bottom": 60, "left": 60, "right": 20},
    }

    event = st_echarts(option, height=f"{percentage_height}px", key=key, events={"click": "function(params) { console.log(params.name); return params.name }"})
    # if event and "name" in event:
    #     return event["name"]  # 返回点击的年份
    return event

def plot_penetration_by_price(df, col_name, percentage_height, key="bar_chart"):
    penetration_by_price = df.groupby("价格区间(万)")[col_name].mean().reset_index()
    penetration_by_price["渗透率"] = (penetration_by_price[col_name] * 100).round(1)

    option = {
        
        "tooltip": {"trigger": "axis"},
        "legend": {"textStyle": {"fontSize": 12}},
        "xAxis": {
            "type": "category",
            "data": list(penetration_by_price["价格区间(万)"]),
            "axisLabel": {"fontSize": 12}
        },
        "yAxis": {
            "type": "value",
            "name": "渗透率 (%)",
            "axisLabel": {"fontSize": 12}
        },
        "series": [{
            "data": list(penetration_by_price["渗透率"]),
            "type": "bar",
            "label": {
                "show": True,
                "position": "top",
                "formatter": "{c}%",
                "fontSize": 12
            },
            "itemStyle": {"color": "#8475F5"}
        }],
        "grid": {"top": 60, "bottom": 60, "left": 60, "right": 20},
    }


    event = st_echarts(option, height=f"{percentage_height}px", key=key, events={"click": "function(params) { console.log(params.name); return params.name }"})
    # if event and "name" in event:
    #     return event["name"]  # 返回点击的价格区间
    return event

@st.cache_data
def load_config():
    config_path = "data/configuration.csv"
    config = pd.read_csv(config_path)
    bins = [0, 5, 8, 12, 18, 25, 35, np.inf]
    config = cut_range(config, bins, "官方指导价(万)", "价格区间(万)")
    config = config[["厂商"] + [c for c in config.columns if c != "厂商"]]
    config["年款"] = config["年款"].str.replace("款", "", regex=False)
    return config

def run_style():
    st.markdown("""
    <style>
                
    .stApp {
        background-color: #F7F8F9;
    }            

                             
    # .st-emotion-cache-4uzi61 {
    #     border-radius: 8px; /* 可选，添加圆角 */
    #     border:0px solid #E2E7EF; /* 可选，添加边框 */
    #     background-color: white; /* 可选，确保背景不透明以显示阴影 */
    #     padding: 24px; /* 可选，增加内部间距 */
    # }
    
    .st-emotion-cache-1d8vwwt {
        border-radius: 8px; /* 可选，添加圆角 */
        border:0px solid #E2E7EF; /* 可选，添加边框 */
        background-color: white; /* 可选，确保背景不透明以显示阴影 */
        padding: 24px; /* 可选，增加内部间距 */
    }

    # .st-emotion-cache-8atqhb {
    #     border-radius: 8px; /* 可选，添加圆角 */
    #     border:0px solid #E2E7EF; /* 可选，添加边框 */
    #     background-color: white; /* 可选，确保背景不透明以显示阴影 */
    #     padding: 24px; /* 可选，增加内部间距 */
    
    # }            
    .stAppHeader {
        display:None;
    }
    
    /* 设置字体颜色*/
    .st-emotion-cache-2qp9ou {
        color: #5F6379;
        font-size: 14px          
    }
    
    .h5 {
        color: #5F6379;
    }
    
    .stMarkdown {
        color: #31333F
    }
                
    .stButton > button {
        border:0px solid #E2E7EF; /* 可选，添加边框 */
    }
    </style>
    """, 
    unsafe_allow_html=True
    )


