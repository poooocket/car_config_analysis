import streamlit as st
from streamlit_echarts import st_echarts
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import os
import time
import re
import json
from viz_utils import run_style, cut_range, load_config

def scrape_sales_rank_dong(url):
    """
    采集车型SeriesId，从排行页返回的json数据里解析SeriesId，返回SeriesId和车型名称
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.dongchedi.com/sales"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        df = pd.DataFrame(columns=['series_id', 'series_name', 'image', 'min_price', 'max_price', 'count', 'price', 'dealer_price'])
        data = response.json() # 将获取到的JSON数据转换为字典
        car_list = data['data']['list']     
        
        # 遍历每个车型信息，提取相关字段并添加到DataFrame中
        for car in car_list:
            series_id = car['series_id']
            series_name = car['series_name']
            image = car['image']
            min_price = car['min_price']
            max_price = car['max_price']
            count = car['count']
            price = car['price']
            dealer_price = car['dealer_price']
            
            # 将提取的数据添加到DataFrame中
            row_data = [{'series_id': series_id, 
                         'series_name': series_name, 
                         'image': image, 
                         'min_price': min_price, 
                         'max_price': max_price, 
                         'count': count, 
                         'price': price, 
                         'dealer_price': dealer_price
                        }]
            df = pd.concat([df,pd.DataFrame(row_data)], ignore_index=True)
        return df
    else:
        print("请求失败:", response.status_code)
        return None
    

def scrape_table_data(url):
    """
    根据SeriesID采集车型配置，返回车型配置表格数据
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.dongchedi.com/sales"
    }
    
    response = requests.get(url, headers=headers)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # 查找表头
    cell_header = soup.find('div', class_='table_root__14vH_').find('div', class_='table_row__yVX1h').find_all('div', class_='cell_header-car__1Hrj6')
    cell_header_names = [cell.text.strip() for cell in cell_header]
    column_header = [cell_header_name for cell_header_name in cell_header_names if cell_header_name != ""]
    column_header.insert(0, 'Label Name')
    
    # 定义空列表用于存储所有表格的数据
    tables_data = [] 
    tables = soup.find_all('div', class_='table_root__14vH_') # 查找所有的表格根节点

    for table in tables:    
        # 获取所有子表格名称
        table_label = table.find('h3', class_='cell_title__1COfA')
        table_name = table_label.text.strip() if table_label is not None else ""
        table_data = []
        
        # 查找表格行
        rows = table.find_all('div', class_='table_row__yVX1h')  
        rows_data = []             
        for row in rows:
            rows_data.clear()
            label = row.find('label', class_='cell_label__ZtXlw') # 查找行标签
            label_name = label.text.strip() if label is not None else "" # 提取标签名    
            
            if row.find('div', class_='cell_official-price__1O2th'):
                cells = row.find_all('div', class_='cell_official-price__1O2th')# 查找价格单元格数据     
                row_data = [label_name] + [cell.text.strip() for cell in cells]
                rows_data.append(row_data)
            
            elif row.find('div', class_='table_row__yVX1h'):
                nested_rows = row.find_all('div', class_='table_row__yVX1h')
                for nested_row in nested_rows:
                    cells = nested_row.find_all('div', class_='cell_normal__37nRi')
                    row_data = [label_name] + [cell.text.strip() for cell in cells]
                    rows_data.append(row_data)
                    
            else:
                cells = row.find_all('div', class_='cell_normal__37nRi')
                row_data = [label_name] + [cell.text.strip() for cell in cells]
                if label_name != "":
                    rows_data.append(row_data)
                    
            # 将行数据添加到表格数据列表中
            table_data.extend(rows_data)
            # 将当前表格的数据转换为DataFrame
            df = pd.DataFrame(table_data, columns=column_header)
            df.insert(0, 'Table Name', table_name)
        
        # 将表格数据添加到总的表格数据列表中
        tables_data.append(df)
    combined_df = pd.concat(tables_data, ignore_index=True)    
    return combined_df

def merge_rows_by_label(df): 
    """
    根据Label Name列合并行数据
    """

    merged_df = pd.DataFrame(columns=df.columns) # 创建一个空的DataFrame用于存储合并后的数据
    label_names = df['Label Name'].unique()
    for label_name in label_names:
        # 提取具有相同label_name的行
        rows = df[df['Label Name'] == label_name]
        # 合并行数据
        merged_row = rows.iloc[0].copy()
        for column in df.columns:
            if column != 'Label Name' and column != 'Table Name':
                merged_row[column] = ' '.join(rows[column])
        
        # 将合并后的行添加到新的DataFrame中
        merged_df = pd.concat([merged_df, pd.DataFrame([merged_row])], ignore_index=True)
    merged_df = merged_df.drop(columns='Table Name') 
    return merged_df  
    
def incremental_save(df, file_path):
    # 如果文件已经存在，进行增量保存
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
    else:
        combined_df = df
    combined_df.to_csv(file_path, index=False)



def initial_clean(df):
    """
    基础数据清洗
    """
    df = df.drop_duplicates(keep='last')
    df.replace('None', value=np.nan, inplace=True) #填空   
    df['Label Name'] = df['Label Name'].replace(r'\+对比钉在左侧' , '', regex=True) # 去除车型名称里一些无用的文字 

    #使用正则表达式提取车型和年款
    # df_extracted = df['Label Name'].str.extract(r'(.*) (\d{4}.*)')
    df_extracted = df['Label Name'].str.extract(r'([^ ]+)\s(\d{4}款)\s(.*)')
    df_extracted.columns = ['车型', '年款', '配置名称']

    #在原有列的位置插入新列
    df.insert(loc=df.columns.get_loc('Label Name') + 1, column='车型', value=df_extracted['车型'])
    df.insert(loc=df.columns.get_loc('Label Name') + 2, column='年款', value=df_extracted['年款'])
    df.insert(loc=df.columns.get_loc('Label Name') + 3, column='配置名称', value=df_extracted['配置名称'])

    df.rename(columns={'官方指导价': '官方指导价(万)'}, inplace=True)# 重命名列名
    df['官方指导价(万)'] = df['官方指导价(万)'].str.replace('万', '').astype(float)# 将价格数据由字符串转换为数值
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x) # 去除空格
    df = df.applymap(lambda x: re.sub(r'\s*图示$', '', x) if isinstance(x, str) and re.search(r'\s*图示$', x) else x) # 去除“图示”字符
    df = df.drop(columns=['Label Name'])
    df = df.dropna(subset=['年款'])
  
    df["上市时间"] = df["上市时间"].astype(str) 
    
    # 在price_range列中展示具体区间范围而非(50000, 100000]这种格式
    bins = list(range(0, 200, 5))
    df["价格区间(万)"] = pd.cut(df["官方指导价(万)"], bins=bins) 
    df["价格区间(万)"] = df["价格区间(万)"].apply(lambda x: f"{int(x.left)}-{int(x.right)}" if pd.notnull(x) else "Unknown")
    df.insert(df.columns.get_loc("官方指导价(万)") + 1, "价格区间(万)", df.pop("价格区间(万)")) # 将 price_range 列插入到原价格列后面
    return df

def reorder_items(text):
    standard_order = ["充电管理", "服务预约", "远程控制", "车辆监控", "数字钥匙", "智能寻车助手"]
    if pd.isna(text):
        return text  # 保持 NaN 不动
    text = re.sub(r'[○]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    items = text.split()
    sorted_items = [item for item in standard_order if item in items]
    return ' '.join(sorted_items)

# 智能化配置数据清洗
def clean_intelligent_configuration_data(df):
    with open('data/feature_grouped.json', 'r', encoding='utf-8') as f:
        feature_grouped = json.load(f)
    
    for col in feature_grouped["智能化配置"]:
        # df[col] = [str(value).replace("●", "").strip() for value in df[col] if value != np.nan]
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace("●", "", regex=False).str.strip()
        
    if "辅助驾驶操作系统" in df.columns:
        df["辅助驾驶操作系统"] = df["辅助驾驶操作系统"].replace({"DiPilot智能辅助驾驶系统":"DiPilot"})

    if "辅助驾驶功能包" in df.columns:
        df["辅助驾驶芯片"] = df["辅助驾驶芯片"].replace({"Mobileye EyeQ5H x 2":"Mobileye EyeQ5H*2", 
                                                            "NVIDIA DRIVE Orin-X *2":"NVIDIA DRIVE Orin X*2", 
                                                            "NVIDIA DRIVE Orin-X*2":"NVIDIA DRIVE Orin X*2", 
                                                            "NVIDIA Orin-X":"NVIDIA DRIVE Orin X", 
                                                            "英伟达Orin-X":"NVIDIA DRIVE Orin X", 
                                                            "○双Mobileye EyeQ5H":"○Mobileye EyeQ5H*2"
                                                            })

    if "车载智能芯片" in df.columns:
        df["车载智能芯片"] = df["车载智能芯片"].replace({"骁龙8155":"高通骁龙8155", 
                                                            "高通8155":"高通骁龙815", 
                                                            "骁龙8295":"高通骁龙8295", 
                                                            "龍鷹一号":"龍鹰一号", 
                                                            "龍鷹一号*2":"龍鹰一号*2",
                                                            "○龍鷹一号":"○龍鹰一号",
                                                            "联发科MT8666":"联发科8666",
                                                            "MT8666":"联发科8666",
                                                            "MT8675":"联发科8675",
                                                            "高通骁龙SA8155P":"高通骁龙8155P",
                                                            "高通骁龙SA8295P":"高通骁龙8295P"
                                                            })

    if "车载智能系统" in df.columns:
        df["车载智能系统"] = df["车载智能系统"].replace({"eConnect智能互联":"eConnect", 
                                                            "斑马":"斑马智行", 
                                                            "雄狮Lion5.0":"Lion5.0", 
                                                            "DiLink智能网联系统":"DiLink"
                                                            })

    if "车机系统内存(GB)" in df.columns:
        df["车机系统内存(GB)"] = df["车机系统内存(GB)"].replace({"12GB":"12"})

    if "车机系统存储(GB)" in df.columns:
        df["车机系统存储(GB)"] = df["车机系统存储(GB)"].replace({"128GB":"128", 
                                                                    "128.0":"128", 
                                                                    "24.0":"24", 
                                                                    "256.0":"256", 
                                                                    "32.0":"32", 
                                                                    "64.0":"64", 
                                                                    "16.0":"16"
                                                                    })


    if "车外摄影头像素" in df.columns:
        df["车外摄影头像素"] = df["车外摄影头像素"].replace({"800W":"800万", 
                                                                    "800*1,300*4,250*1":"800万*1,300万*4,250万*1", 
                                                                    "800*7,200*4":"800万*7,200万*4", 
                                                                    "800W*2":"800万*2"
                                                                    })
    
    if "车机系统存储(GB)" in df.columns:
        df["车机系统存储(GB)"] = df["车机系统存储(GB)"].apply(lambda x: str(x) if pd.notnull(x) else x)
    
    if "车机系统存储(GB)" in df.columns:
        df["车机系统存储(GB)"] = df["车机系统存储(GB)"].replace({"128GB":"128", 
                                                 "128.0":"128", 
                                                 "24.0":"24", 
                                                 "256.0":"256", 
                                                 "32.0":"32", 
                                                 "64.0":"64", 
                                                 "16.0":"16"})

    
    if "手机App远程控制" in df.columns:
        df["手机App远程控制"] = df["手机App远程控制"].apply(reorder_items)
    return df

def check_missing_data(df):
    """
    检查缺失值
    """
    missing_values_count = df.isnull().sum()
    missing_percentage = (missing_values_count / len(df)) * 100
    missing_data = pd.DataFrame({
        'class': df.columns,
        'missing_values_count': missing_values_count.values,
        'missing_percentage': missing_percentage.values
    })
    missing_data = missing_data.sort_values(by='missing_percentage', ascending=False)
    return missing_data


def extract_unique_feature(configuration, missing_data, filter_percentage=98):
    """
    提取车型特色功能
    """
    columns = ["厂商", "车型", "年款", "配置名称", "官方指导价(万)", "特色功能", "功能内容"]
    data_to_add = []
    for i, row in missing_data.iterrows():
        missing_percentage = row['missing_percentage']
        if missing_percentage > filter_percentage:
            col_name = row['class'] 
            df = configuration.dropna(subset=col_name) 
            for j, row_sub in df.iterrows():
                brand = row_sub['厂商']
                model = row_sub['车型']
                year = row_sub['年款']
                config_name = row_sub['配置名称']
                price =  row_sub['官方指导价(万)']
                unique_feature_name = col_name
                unique_feature_value = str(row_sub[col_name]).replace("\n","").replace("包含：","")
                data_to_add.append([brand, model, year, config_name, price, unique_feature_name, unique_feature_value])
               
                
    unique_feature = pd.DataFrame(data_to_add, columns=columns)
    return unique_feature


def update_data():

    series_file = "data/series.csv"
    configuration_file = "data/configuration.csv"
    missing_data_file = "data/missing_data.csv"
    unique_feature_file = "data/unique_feature.csv"
    filter_percentage = 98
    
    # series_url = "https://www.dongchedi.com/motor/pc/car/rank_data?aid=1839&app_name=auto_web_pc&city_name=%E4%B8%8A%E6%B5%B7&count=1000&offset=0&month=1000&new_energy_type=1%2C2%2C3&rank_data_type=11&brand_id=&price=&manufacturer=&outter_detail_type=&nation=0"
    series_url = "https://www.dongchedi.com/motor/pc/car/rank_data?aid=1839&app_name=auto_web_pc&city_name=%E4%B8%8A%E6%B5%B7&count=1000&offset=0&month=1000&new_energy_type=1%2C2%2C3&rank_data_type=11&brand_id=&price=&manufacturer=&outter_detail_type=&nation=0"
    # === 1. 获取最新车型系列数据 ===
    latest_series = scrape_sales_rank_dong(series_url)
    latest_series_id_set = set(latest_series['series_id'])

    # === 2. 判断是否已有 series.csv，找出新增 series_id ===
    if os.path.exists(series_file):
        old_series = pd.read_csv(series_file)
        old_series_id_set = set(old_series['series_id'])
        new_series_id_set = latest_series_id_set - old_series_id_set
        combined_series = pd.concat([old_series, latest_series[latest_series['series_id'].isin(new_series_id_set)]], ignore_index=True)
    else:
        new_series_id_set = latest_series_id_set
        combined_series = latest_series

    # 保存更新后的系列数据
    combined_series.to_csv(series_file, index=False)
    series_id_list = list(new_series_id_set)

    # === 3. 若无新增车型，终止更新流程 ===
    if not series_id_list:
        none_update_info = st.info("暂无新增车型")
        time.sleep(1)
        none_update_info.empty()


    # === 4. 采集新增配置数据 ===
    progress_text = "正在采集新增车型配置"
    crawl_progress = st.progress(0, text=progress_text)
    new_configuration_database = []

    for index, series_id in enumerate(series_id_list):
        configuration_url = config_url_template.format(series_id)
        configuration_df = scrape_table_data(configuration_url)
            # 跳过空数据或异常页面
        if configuration_df is None or configuration_df.empty or 'Label Name' not in configuration_df.columns:
            continue
        configuration_df = merge_rows_by_label(configuration_df)
        configuration_df_transposed = configuration_df.set_index('Label Name').T.reset_index().rename(columns={'index': 'Label Name'})
        # st.write(configuration_df_transposed)
        new_configuration_database.append(configuration_df_transposed)

        progress_value = (index + 1) / len(series_id_list)
        crawl_progress.progress(progress_value, text=f"已采集 {round(progress_value * 100, 1)}%")

    crawl_progress.empty()
    
    if new_configuration_database:
        new_configuration = pd.concat(new_configuration_database, ignore_index=True)
        # st.write(new_configuration.shape)

        # === 5. 仅清洗新增数据 ===
        new_configuration = initial_clean(new_configuration)
        # st.write(new_configuration.shape)
        new_configuration = clean_intelligent_configuration_data(new_configuration)
        # st.write(new_configuration.shape)

        # === 6. 合并老数据 + 保存 ===
        if os.path.exists(configuration_file):
            old_configuration = pd.read_csv(configuration_file,low_memory=False)
            configuration = pd.concat([old_configuration, new_configuration], ignore_index=True)
        else:
            configuration = new_configuration

        configuration.to_csv(configuration_file, index=False)
        # st.write(configuration.shape)

        # === 7. 缺失值检查 ===
        missing_data = check_missing_data(configuration)
        missing_data.to_csv(missing_data_file, index=False)

        # === 8. 提取特征列 ===
        unique_feature = extract_unique_feature(configuration, missing_data, filter_percentage=filter_percentage)
        unique_feature.to_csv(unique_feature_file, index=False)

        success_info = st.success("数据采集与更新完成 ✅")
        time.sleep(1)  
        success_info.empty()



##########################################################################################

def build_sunburst_data(df):
    result = []
    for brand in df["厂商"].unique():
        brand_node = {"name": brand, "children": []}
        brand_df = df[df["厂商"] == brand]
        for model in brand_df["车型"].unique():
            brand_node["children"].append({"name": model, "value": 1})
        result.append(brand_node)
    return result

#设置页面
st.set_page_config(page_title="基础统计", layout="wide")
st.markdown("##### 基础统计")
run_style()

# update_button = st.button("更新数据 :material/refresh:",  type="tertiary")
# if update_button:
#     update_data()
#     st.rerun()

stack_colors = ["#DCD7FF", "#C9C3FC", "#B6AEFA", "#A399F7", "#9085F4", "#7E70F2", "#7060E0"]

# 读取数据
df = load_config()


# 数据描述
brand_count = len(set(df['厂商'].tolist()))
model_count = len(set(df['车型'].tolist()))
config_count = len(df)

cards = [
("厂商", brand_count, "家"),
("车型", model_count, "款"),
("配置", config_count, "个"),
]

cols = st.columns(len(cards))
for col, (label, count, unit) in zip(cols, cards):
    with col:
        st.markdown(
            f"""
            <div style="background-color:white; padding:16px 20px; border-radius:8px; text-align:left;">
                <div style="font-size:28px; color:#8474F5;">{count}
                    <span style="font-size:14px;">{unit}</span>
                </div>
                <div style="font-size:14px; color:#666;">{label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )


st.write("")


df_grouped = df.groupby(['年款', '价格区间(万)']).size().reset_index(name='车型数量')
x_data = sorted(df_grouped["年款"].unique().tolist())
labels = ["0-5", "5-8", "8-12", "12-18", "18-25", "25-35", "35以上"]
price_ranges = [label for label in labels if label in df["价格区间(万)"].unique()]

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
    "color": stack_colors,
    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    "legend": {"data": price_ranges},
    "xAxis": {"type": "category", "data": x_data},
    "yAxis": {"type": "value"},
    "series": series
}

events = {
    "click": "function(params) { return {year: params.name, price: params.seriesName}; }"
}

cols = st.columns([2,1])
with cols[0]:
    with st.container(border=True):
        st.markdown("###### 各年款车型在不同价格区间的分布情况")
        st.caption("价格单位：万")
        stack_holder = st.empty()
        

with cols[1]:
    with st.container(border=True):
        st.markdown("###### 厂商与车型分布")
        sunburst_caption_holder = st.empty()
        sunburst_holder = st.empty()
        sunburst_rows_holder = st.empty()


with st.container(border=True): 
    df_caption_holder = st.empty()
    df_holder = st.empty()
    df_rows_holder = st.empty()

with stack_holder:
    stack_selected = st_echarts(option, events=events, height="326px")  

if stack_selected and "year" in stack_selected and "price" in stack_selected:
    year = stack_selected["year"]
    price = stack_selected["price"]
    filtered_df = df[(df["年款"] == year) & (df["价格区间(万)"] == price)]

else:
    filtered_df = df.head(200)
    year = "前200条数据"
    price = "前200条数据"


df_caption_holder.markdown(f":violet-badge[ 年款：{year} ] :violet-badge[ 价格区间：{price} ]")
df_holder.dataframe(filtered_df, height=500)
df_rows_holder.text(f"共 {len(filtered_df)} 条")

sunburst_caption_holder.markdown(f":violet-badge[ 年款：{year} ] :violet-badge[ 价格区间：{price} ]")
sunburst_data = build_sunburst_data(filtered_df)

option = {
    "series": {
        "color": stack_colors,
        "type": "sunburst",
        "data": sunburst_data,
        "radius": [0, "90%"],
        "sort": None,
        "emphasis": {"focus": "ancestor"},
        "label":{"fontSize": 9},
    }
}

events = {
    "click": "function(params) { return params.name; }"
}

with sunburst_holder:
    sunburst_selected = st_echarts(option, events=events, height="284px")
sunburst_rows_holder.text(f"共 {len(filtered_df)} 款车型配置")

if sunburst_selected:
    cols_to_check = ["厂商","车型"]
    sunburst_filtered_df = filtered_df[filtered_df[cols_to_check].apply(lambda row: sunburst_selected in row.values, axis=1)]
    df_caption_holder.markdown(f":violet-badge[ 年款：{year} ] :violet-badge[ 价格区间：{price} ] :violet-badge[ {sunburst_selected} ]")
    df_holder.dataframe(sunburst_filtered_df, height=460)
    df_rows_holder.text(f"共 {len(sunburst_filtered_df)} 条")


            



# # 旭日图，数据概览可视化
# fig = px.sunburst(config, path=['厂商','年款','车型'])
# fig.update_layout(height=800)
# st.plotly_chart(fig, use_container_width=True)
