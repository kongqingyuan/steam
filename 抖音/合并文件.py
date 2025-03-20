import pandas as pd
import os
import glob
from datetime import datetime

def merge_excel_files(files,output_file):
    """
    目的：合并指定目录下的所有抖音推广数据Excel文件
    输入：合并的文件，要输出的文件
    合并抖音店文件夹下的所有xlsx文件
    输出：合并后的Excel文件
    """
    # 获取当前目录下所有的xlsx文件
    excel_files = glob.glob(files)
    
    if not excel_files:
        print("未找到需要合并的Excel文件！")
        return
    
    dfs = []
    for file in excel_files:
        try:
            df = pd.read_excel(file)
            dfs.append(df)
            print(f"成功读取文件：{file}")
        except Exception as e:
            print(f"读取文件 {file} 时出错：{str(e)}")
    
    if not dfs:
        print("没有成功读取任何文件！")
        return
    
    # 合并所有DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)
    
    # 生成输出文件名（使用当前时间）
    current_time = datetime.now().strftime("%Y%m%d")
    
    # 保存合并后的文件
    try:
        merged_df.to_excel(output_file, index=False)
        print(f"\n合并完成！")
        print(f"总行数：{len(merged_df)}")
        print(f"输出文件：{output_file}")
    except Exception as e:
        print(f"保存合并文件时出错：{str(e)}")


def data_process(file_path, output_file):
    """
    目的：处理合并后的数据，主要进行以下转换：
    - 过滤掉'小时区间'为'全部'的行
    - 将日期和小时区间合并为完整的时间戳
    - 将'整体消耗'列重命名为'花费'并转换为浮点数

    输入文件：
    - file_path: 合并后的Excel文件（例如：'./抖音/抖音奢美店/合并数据.xlsx'）

    输出文件：
    - output_file: 处理后的Excel文件（例如：'./抖音/抖音奢美店/抖音奢美报表.xlsx'）
    """
    df=pd.read_excel(file_path)
    df = df[df['小时区间'] != '全部']
    df['日期'] = df['日期'] + ' ' + df['小时区间'].str.split(' ~ ').str[0]
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.rename(columns={'整体消耗': '花费'})
    df['花费'] = df['花费'].astype(float)
    df.to_excel(output_file, index=False)
    print(f"处理完成，保存文件：{output_file}")


path = ['./抖音/抖音奢美店', '/抖音/抖音PY旗舰店']
files = f'{path[0]}/全域推广-投后数据-*.xlsx'
output_file = f'{path[0]}/合并数据.xlsx'
merge_excel_files(files, output_file)


file_path = f'{path[0]}/合并数据.xlsx'
output_file = f'{path[0]}/抖音奢美报表.xlsx'
data_process(file_path,output_file)

