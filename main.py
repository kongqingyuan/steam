from datetime import datetime, timedelta
import pandas as pd
import yaml
import argparse
import re
import os

# 加载配置文件
def load_config(config_path='config.yaml'):
    """
    目的：加载并解析配置文件
    输入: config.yaml 配置文件
    输出：配置文件的字典形式
    """
    with open(config_path, 'r',encoding='utf-8') as file:
        return yaml.safe_load(file)

# 验证日期范围是否有效
def validate_date_range(start_date, end_date, new_df, merged_df_new):
    """
    目的：验证用户输入的日期范围是否在数据范围内
    输入：
        - start_date: 想查询的开始日期
        - end_date: 想查询的结束日期
        - new_df: 处理后的排班数据
        - merged_df_new: 处理后的花费数据
    输出：
        - True: 日期范围有效
        - ValueError: 日期范围无效时抛出异常
    """
    new_df_min_date = new_df['上播时间'].min().date()
    new_df_max_date = new_df['下播时间'].max().date()
    merged_df_new_min_date = merged_df_new['小时'].min().date()
    merged_df_new_max_date = merged_df_new['小时'].max().date()

    overall_min_date = max(new_df_min_date, merged_df_new_min_date)
    overall_max_date = min(new_df_max_date, merged_df_new_max_date)

    if start_date.date() < overall_min_date or end_date.date() > overall_max_date+timedelta(days=1):
        raise ValueError(
            f"错误：输入的日期范围超出数据范围。\n"
            f"数据范围：{overall_min_date} 至 {overall_max_date}"
        )
    return True

# 定义提取主播和时间段的函数
def extract_anchors_and_time(s):
    """
    目的：从字符串中提取主播名称和时间段
    输入：包含主播信息的字符串，格式如："张三(9:00-10:00)"
    输出：主播和时间段的元组列表，如：[("张三", "9:00-10:00")]
    """
    pattern = re.compile(r"([^\(]+)\(([^)]+)\)")#创建一个正则表达式模式
    matches = re.findall(pattern, s)#在字符串中查找所有匹配正则表达式的子字符串
    return matches #[("张三", "9:00-10:00"), ("李四", "14:00-15:00")]

# 安全提取函数，处理非字符串数据
def extract_anchors_and_time_safe(s):
    """
    目的：安全地提取主播和时间信息，处理非字符串输入
    输入：任意类型的数据
    输出：主播和时间段的元组列表，或空列表
    """
    if isinstance(s, str):# 检查参数是否位字符串类型
        return extract_anchors_and_time(s)
    return []

# 处理排班时间，按不同方法将时间处理成整点
def round_to_nearest_hour(time_str, method="method1", is_end_time=False): 
    """
    目的：将时间舍入到整点
    输入：
        - time_str: 时间字符串，格式为 "HH:MM"(排班表中上播和下播时间)
        - method: 处理方法，可选 method1/method2/method3/method4
        - is_end_time: 是否是下播时间
    输出：处理后的整点时间字符串，格式为 "HH:MM"
    """
    # 特殊处理 23:59 和 24:00
    if time_str in ['23:59', '24:00']:
        return '00:00'
    
    time_obj = datetime.strptime(time_str, '%H:%M')

    # 定义时间处理规则[u2]
    rules = {
        "method1": lambda t, is_end: t + timedelta(hours=1) if not is_end and t.minute > 0 else t,
        "method2": lambda t, is_end: t + timedelta(hours=1) if t.minute > 0 else t,
        "method3": lambda t, is_end: t,
        "method4": lambda t, is_end: t + timedelta(hours=1) if is_end and t.minute > 0 else t
    }
    
    if method not in rules:
        raise ValueError(f"不支持的时间处理方法: {method}")
        
    time_obj = rules[method](time_obj, is_end_time)
    return time_obj.replace(minute=0, second=0).strftime('%H:%M')

# 处理排班表数据

def process_schedule_data(file_path, time_method):
    """
    目的：处理排班表数据
    输入：
        - file_path: Excel排班表文件路径（.xlsx）
        - time_method: 时间处理方法
    输出：处理后的DataFrame，包含列：
        - 日期、主播、上播时间、下播时间、主播人数
    """
    df0 = pd.read_excel(file_path)
    df0 = df0.replace({'（': '(', '）': ')'}, regex=True) #regex=True 允许你使用正则表达式进行更复杂的模式匹配和替换

    data = []
    # 遍历每行数据进行处理
    for i, row in df0.iterrows():
        date = row['Date']  # 获取日期
        for col in df0.columns[1:]:  # 从第二列开始遍历（第一个是日期列）
            anchors_and_times = extract_anchors_and_time_safe(row[col]) #[('张三',''),('','')]
            for anchor, time in anchors_and_times:
                # 拆分多个主播名字（如果有多个，通过'+'分隔）
                anchor_list = anchor.split('+') #以列表形式返回['张三', '李四']
                num_anchors = len(anchor_list)  #计算主播人数
                # 分割时间段并进行处理
                start_time, end_time = time.split('-') #['20:00', '24:00']
                # 分别处理开始时间和结束时间
                start_time_rounded = round_to_nearest_hour(start_time, 
                                                         time_method, 
                                                         is_end_time=False)
                end_time_rounded = round_to_nearest_hour(end_time, 
                                                       time_method, 
                                                       is_end_time=True)
                
                for single_anchor in anchor_list:
                    # 处理跨日期的时间段
                    start_datetime = datetime.combine(date, datetime.strptime(start_time_rounded, '%H:%M').time()) #2025-02-16 20:00:00
                    end_datetime = datetime.combine(date, datetime.strptime(end_time_rounded, '%H:%M').time()) #2025-02-16 00:00:00

                    # 如果结束时间小于开始时间，说明是跨日期的情况
                    if end_datetime < start_datetime:
                        end_datetime += timedelta(days=1)  # 将结束时间加一天
                    # 将处理后的数据添加到列表中
                    data.append([date, single_anchor.strip(), start_datetime, end_datetime, num_anchors])

    # 创建新的 DataFrame
    new_df = pd.DataFrame(data, columns=['日期', '主播', '上播时间', '下播时间', '主播人数'])
    # 将上播时间和下播时间转换为 datetime 类型
    new_df['上播时间'] = pd.to_datetime(new_df['上播时间'])
    new_df['下播时间'] = pd.to_datetime(new_df['下播时间'])
    # 返回处理后的数据
    return new_df

# 处理花费数据
def process_expense_data(file_path):
    """
    目的：处理花费数据，计算每小时累计花费
    输入：
        - file_path: CSV花费数据文件路径（.csv）
    输出：处理后的DataFrame，包含列：
        - 日期、小时、花费（上小时到这小时的花费）、累积花费（按日期分组，从零点开始累计）
    """
    df = pd.read_excel(file_path)#抖音为utf-8
    df['日期'] = pd.to_datetime(df['日期'])

    # 创建时间序列
    start_date = df['日期'].min().date() 
    end_date = df['日期'].max().date()+timedelta(days=1)    

    hourly_time_range = pd.date_range(
        start=start_date,
        end=end_date,
        freq='h'
    )

    # 将原始数据按小时分组并累计花费
    df['小时'] = df['日期'].dt.strftime('%Y-%m-%d %H:00') #2025-03-10 23:00
    hourly_expenses = df.groupby('小时')['花费'].sum().reset_index()

    # 创建一个新的 DataFrame，其中包含完整的时间序列
    full_time_df = pd.DataFrame({'日期': hourly_time_range})
    full_time_df['小时'] = full_time_df['日期'].dt.strftime('%Y-%m-%d %H:00')

    # 合并数据
    merged_df = pd.merge(full_time_df, hourly_expenses, on='小时', how='left')

    # 将缺失的花费值填充为 0
    merged_df['花费'] = merged_df['花费'].fillna(0)

    # 按天进行分组计算累计花费，并确保每天从零点开始累计
    merged_df['日期'] = merged_df['日期'].dt.date  # 提取日期部分，去除时间
    merged_df['累积花费'] = merged_df.groupby('日期')['花费'].cumsum()
    
    # 创建一个新的 DataFrame，将时间后移一小时
    merged_df_new = merged_df.copy()
    
    # 将时间后移一小时
    merged_df_new['小时'] = pd.to_datetime(merged_df_new['小时']) + pd.DateOffset(hours=1)

    # 返回处理后的数据  
    return merged_df_new

# 计算主播花费
def calculate_anchor_expenses(filtered_new_df, merged_df_new, start_date_input, end_date_input):
    """
    目的：计算每个主播在指定时间段内的花费
    输入：
        - filtered_new_df: 过滤后的排班数据(传入的开始日期-传入的结束日期)
        - merged_df_new: 处理后的花费数据
        - start_date_input: 开始日期字符串
        - end_date_input: 结束日期字符串
    输出：汇总DataFrame，包含列：
        - 主播、合计、数据起始时间、数据截止时间
    """
    # 合并 filtered_new_df 和 merged_df_new，根据上播时间匹配
    merged_up = pd.merge(filtered_new_df, merged_df_new, 
                        left_on='上播时间', right_on='小时', 
                        how='left', suffixes=('_f', '_上播'))

    # 合并 filtered_new_df 和 merged_df_new，根据下播时间匹配
    merged_all = pd.merge(merged_up, merged_df_new, 
                         left_on='下播时间', right_on='小时', 
                         how='left', suffixes=('_上播', '_下播'))

    # 计算合计
    merged_all['合计'] = (merged_all['累积花费_下播'] - merged_all['累积花费_上播']) / merged_all['主播人数']
    merged_all = merged_all[['日期', '主播', '上播时间', '下播时间', '累积花费_上播', '累积花费_下播', '合计']]

    # 按照 '主播' 对 '合计' 进行汇总
    summary = merged_all.groupby('主播', as_index=False)['合计'].sum()

    # 添加"数据起始时间"列
    summary['数据起始时间(含)'] = f"{start_date_input}"
    summary['数据截止时间(含)'] = f"{end_date_input}"

    # 返回处理后的数据
    return summary

# 处理输出文件
def process_output_file(output_file_path):
    """
    目的：处理输出文件，确保输出目录存在且文件可写
    输入：
        - output_file_path: 输出文件路径
    输出：
        - None: 成功时无返回
        - PermissionError: 文件无法删除时抛出异常
    """
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 尝试删除已存在的文件
    if os.path.exists(output_file_path):
        try:
            os.remove(output_file_path)
        except PermissionError:
            raise PermissionError(f"无法删除已存在的文件 {output_file_path}，请确保文件未被其他程序打开")

#处理数据主流程
def process_data(config,platform='tmall'):
    """
    目的：处理指定平台的数据主流程
    输入：
        - config: 配置文件字典
        - platform: 平台名称（'tmall'或'douyinshemei'或'douyinpy'）
    输出：主播花费汇总DataFrame
    """
    platform_config = config[platform]
    # 获取时间处理方法
    time_method = config.get('time_processing', {}).get('method', 'method1')
    start_date_input = platform_config['date_range']['start_date']
    end_date_input = platform_config['date_range']['end_date']

    # 获取排班数据
    schedule_file = platform_config['input_files']['schedule_file']
    new_df = process_schedule_data(schedule_file, time_method)
    
    # 获取花费数据
    expense_file = platform_config['input_files']['expense_file']
    merged_df_new = process_expense_data(expense_file)
    
    # 验证日期范围
    start_date = datetime.strptime(start_date_input, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_input, '%Y-%m-%d')
    # next_date=end_date+timedelta(days=1)
    validate_date_range(start_date, end_date, new_df, merged_df_new)
    next_date=end_date+timedelta(days=1)
    # 筛选在指定日期范围内的行
    filtered_new_df = new_df[(new_df['上播时间'] >= pd.to_datetime(start_date)) & 
                            (new_df['下播时间'] <= pd.to_datetime(next_date))]
    
    # 计算主播花费
    return calculate_anchor_expenses(filtered_new_df, merged_df_new, 
                                  start_date_input, end_date_input)

# 主函数
def main():
    """
    目的：程序主入口，处理命令行参数并执行数据处理流程
    输入：
        - 命令行参数：--platform [tmall/douyin]
        - config.yaml：配置文件
        - 排班表：Excel文件
        - 花费数据：CSV文件
    输出：
        - Excel文件：主播花费统计结果
        - 控制台信息：处理状态和错误信息
    """
    try:
        # 创建命令行参数解析器
        parser = argparse.ArgumentParser(description='计算主播花费')
        parser.add_argument('--platform', 
                          type=str,
                          choices=['tmall', 'douyinshemei', 'douyinpy'],
                          default='tmall',
                          help='选择平台：tmall 或 douyinshemei 或 douyinpy')
        args = parser.parse_args()
        
        # 加载配置
        config = load_config()
        
        # 处理数据
        summary = process_data(config,args.platform)
        
        # 获取输出文件路径并处理
        output_file_path = config[args.platform]['output_file']['filename']
        process_output_file(output_file_path)
        
        # 保存文件
        summary.to_excel(output_file_path, index=False)
        print(f"{args.platform}结果已保存到 {output_file_path}")
        
    except ValueError as e:
        print(f"日期范围错误：{str(e)}")
    except Exception as e:
        print(f"程序执行出错：{str(e)}")

if __name__ == "__main__":
    main()

# 终端运行：python main.py --platform douyinshemei