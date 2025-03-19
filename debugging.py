from datetime import datetime, timedelta

# def round_to_nearest_hour(time_str): #00:00
#     if time_str == '24:00':
#         # 将 24:00 转换为 23:59
#         time_str = '23:59'
#     time_obj = datetime.strptime(time_str, '%H:%M') #1900-01-01 23:59:00
#     if time_obj.minute > 30: #59
#         # 如果大于30分钟，则四舍五入到下一个整点
#         time_obj += timedelta(hours=1) #1900-01-02 00:59:00
#         return time_obj.replace(minute=0, second=0).strftime('%H:%M')
#     else:
#         # 如果小于等于30分钟，则四舍五入到当前整点
#         return time_obj.replace(minute=0, second=0).strftime('%H:%M')
    
# print(round_to_nearest_hour('23:30'))
# time_str='23:59'
# time_obj = datetime.strptime(time_str, '%H:%M')
# time_obj += timedelta(hours=1) #1900-01-02 00:59:00
# time_obj=time_obj.replace(minute=0, second=0).strftime('%H:%M')
# print(time_obj) 

# import re
# s = "张三(10:00-12:00) 李四"
# pattern = re.compile(r"([^\(]+)\(([^)]+)\)")#创建一个正则表达式模式
# matches = re.findall(pattern, s)
# print(matches) #[('张三', '10:00-12:00')]