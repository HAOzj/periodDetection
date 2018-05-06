# -*- coding: utf-8 -*-
"""
Created on the 26th Apr 2018

@author : zhaojun HAO
"""

from jpype import *
import datetime
import sys
from dateutil.relativedelta import relativedelta
import re
from .langconv import Converter
import datetime
import jieba
from .patterns import chs_arabic_map, pattern_year, prefix_year, unit_year, indicator_day
from .patterns import pattern_month, prefix_month, unit_month
from .patterns import pattern_holiday, dateAndDuration_holiday, pattern_multi, chs_weekday, pattern_week
from LunarSolarConverter_module import LunarSolarConverter, Solar, Lunar

startJVM(getDefaultJVMPath(), "-ea", '-Djava.class.path=/home/xuht/source/Time-NLP/target/Time-NLP-1.0.0.jar')
JDClass = JClass("com.time.nlp.TimeNormalizer")
normalizer = JDClass('/home/xuht/source/Time-NLP/target/classes/TimeExp.m')


def t2s(sentence):
    ''' 
    将sentence中的繁体字转为简体字 
    :param 
        sentence: 待转换的句子 
    :return: 
        将句子中繁体字转换为简体字之后的句子 
    '''
    sentence = Converter('zh-hans').convert(sentence)
    return sentence

def chineseDigits2arabicWithin100(chinese_digits, encoding="utf-8"):
    result  = 0
    word_list = list(chinese_digits)
    inside = False
    for count in range(len(chinese_digits)):
        curr_char  = chinese_digits[count]
        if curr_char in chs_arabic_map.keys():
            
            word_list[count] =''
            curr_digit = chs_arabic_map[curr_char]
            # 10
            if curr_digit == 10:
                if not inside:
                    result = 10
                else :
                    result *=  curr_digit 
            # 0-9        
            else:
                result = result + curr_digit
            inside = True
                
        else :
            tmp = curr_char
            if inside :
                if count > 0:
                    word_list[count-1] = str(result) 
#                 print('列表变成  : ',word_list)
            inside = False
            result = 0
    if inside :
        word_list[-1] = str(result)
            

    return ''.join(word_list)

def chineseDigits2arabicWithin1000(chinese_digits, encoding="utf-8"):
    result  = 0
    word_list = list(chinese_digits)
    inside = False
    for count in range(len(chinese_digits)):
        curr_char  = chinese_digits[count]
        if curr_char in chs_arabic_map.keys():
            
            word_list[count] =''
            curr_digit = chs_arabic_map[curr_char]
            # 100
            if curr_digit == 100 :
                result *= 100
            # 10
            elif curr_digit == 10:
                if not inside:
                    result = 10
                elif '百' in chinese_digits[:count] or '佰' in chinese_digits[:count]:
                    result += result%100 * 9
                else:
                    result *=  curr_digit 
            # 0-9        
            else:
                result = result + curr_digit
            inside = True
                
        else :
            tmp = curr_char
            if inside :
                if count > 0:
                    word_list[count-1] = str(result) 
#                 print('列表变成  : ',word_list)
            inside = False
            result = 0
    if inside :
        word_list[-1] = str(result)
            

    return ''.join(word_list)


def parse_time(text):
    output_time = []
    try:
        t=normalizer.parse(text)
#         print(t.__dict__)
        for item in normalizer.getTimeUnit():
            output_time.append(datetime.datetime.fromtimestamp(item.getTime().getTime()/1000))
        return output_time
    except:
        return output_time

def timeDelay(base, number, unit, unit_str):
    '''
    在get_period_year中用，如果表示单位的字段属于['天', '日', '周', '星期', '礼拜']，则对应加减的单位为天
    '''
    if unit_str in indicator_day :
        return base + datetime.timedelta(days = number * unit)
    else :
        return base + relativedelta(months= number * unit)


# def get_period_year(string):
#     '''
#     识别一年中的某个时间段,包括 前/后/第n个 月/季度/半年/日/天/周/星期/礼拜
#     '''
#     string = t2s(string)
#     texts = re.findall( string= string, pattern= pattern_year)
#     times = []
#     bases = []
#     for text in texts :
#         [
#             year, period,  prefix, number, unit_str
#         ] = text
#         number = chineseDigits2arabicWithin1000(number)
#         prefix = prefix_year[prefix] if prefix in prefix_year.keys() else 'ordinal'
#         number = int(number) if number else 1
#         unit = unit_year[unit_str] if unit_str in unit_year.keys() else 12
        
#         base = parse_time(year)[0].date()
        
#         if prefix == 'first':
#             start = base
            
#             end = timeDelay(start, number, unit, unit_str)
#         elif prefix == 'last' :
#             end = base + relativedelta(months = 12) 
#             start = timeDelay(end, -number, unit, unit_str)

#         elif prefix == 'ordinal' :
#             end = base + relativedelta(months = number* unit)
#             start = timeDelay(end, -1, unit, unit_str)
#         elif prefix == 'theFirst' :
#             start = base
#             end = timeDelay(start, number, 1, unit_str)
#         elif prefix == 'theLast' :
#             end = base + relativedelta(months = 12) 
#             start = timeDelay(end, -1, unit, unit_str)
        
            
#         times.append(
#             {       'text' : year+period ,  'start' :start,'end' : end + datetime.timedelta(days = -1)}
#         )
#         bases.append(base)
#     return times, bases

def get_period_year(string):
    '''
    识别一年中的某个时间段,包括 前/后/第n个 月/季度/半年/日/天/周/星期/礼拜

    如果包含在可以提取出某月中时间段，则不识别
    '''
    string = t2s(string)
    times = []
    multi = re.search(pattern = pattern_multi, string = string)
    while multi is not None :
        multi_text  = multi.group()
        
        multi_time = parse_time(multi_text.replace('本年','今年').replace('这年','今年'))
        if len(multi_time) == 2:
            # print('字段为:',multi_text)
            # print('时间为:',multi_time)

            
            multi_start_month = multi_time[0].month
            # 没有明确年则是当前年
            if  multi.group('year1') is None:
                # print("第一个日期没明确的年")
                multi_start_day = multi_time[0].day
                multi_time[0] = datetime.datetime(
                    datetime.datetime.now().year,
                    multi_start_month,
                    multi_start_day,
                    1, 1 ,1 , 1
                )
            # else : 
            #     print(multi.group('year1'))

            # 第二个日期没有年，则继承第一个日期的年
            if multi.group('year2') is None :
                print("第二个日期没明确的年")
                multi_start_year = multi_time[0].year
                multi_end_month = multi_time[1].month
                multi_end_day = multi_time[1].day
                multi_time[1] = datetime.datetime(
                    multi_start_year,
                    multi_end_month,
                    multi_end_day,
                    1, 1 ,1 , 1
                )     

            # 第二个日期没有月，则继承第一个日期的月
            if multi.group('month2') is None :
                print("第二个日期没明确的月")
                multi_end_year = multi_time[1].year
                multi_end_day = multi_time[1].day
                multi_time[1] = datetime.datetime(
                    multi_end_year,
                    multi_time[0].month,
                    multi_end_day,
                    1, 1 ,1 , 1
                )                
            times.append(
                {   'text' :multi_text ,  'start_period' : multi_time[0].date(),'end_period' : multi_time[1].date()}
            )            
            string = string.replace(multi_text,'',1)
            multi = re.search(pattern = pattern_multi, string = string)

    indices_month =[ [m.start(0), m.end(0)] for m in re.finditer(pattern =  pattern_month, string = string)]
    indices_year =[ [m.start(0), m.end(0)] for m in re.finditer(pattern =  pattern_year, string = string)]
    
    indices_texts = []
    for [start_year, end_year] in indices_year:
        inside = False
        for [start_month, end_month] in indices_month:
            # year相关字段在month相关字段中,则用month方法
            if (start_month <= start_year and end_month> end_year) or (start_month < start_year and end_month>= end_year):
                inside = True
        if not inside:
            indices_texts.append( [ (start_year, end_year), re.findall(string = string[start_year:end_year], pattern= pattern_year)] )
        else :
            print("'{}'包含在月级时间段'{}'中".format( string[start_year:end_year],string[start_month:end_month] ))

#     texts = re.findall( string= string, pattern= pattern_year)
    
    
    for [  (start_year, end_year) , texts ] in indices_texts :
        for text in texts :
            [
                year, lunar_indicator, period,  prefix, number_ori, unit_str
            ] = text
            number = number_ori.replace('正','一').replace('腊','十二').replace('阴','').replace('农','').replace('历','')  
            number = chineseDigits2arabicWithin1000(number_ori)
            prefix = prefix_year[prefix] if prefix in prefix_year.keys() else 'ordinal' # 缺失为第，比如 三月表示第三月
            number = int(number) if number else 1 # 缺失为一个，比如首季度为首一个季度
            unit = unit_year[unit_str] if unit_str in unit_year.keys() else 12 # 缺失为年

            
            # 解决java包无法识别"本年"的bug
            if year in ['本年','这年']:
                year = '今年'
            # print('年为\n',year)
            base = parse_time(year)[0].date()
            # print(base)
            # print('时间段为\n',period)

            if period in ['底', '末'] :
                end = base + relativedelta(months = 12) 
                start = base + relativedelta(months = 11) 
            elif period in  ['初','首'] :
                end = base + relativedelta(months = 1) 
                start = base    
            elif len(period)<1 or period in ['全年','整年', '一整年']:
                end = base + relativedelta(months = 12) 
                start = base                            
            else :
                if prefix == 'first':
                    start = base
                    
                    end = timeDelay(start, number, unit, unit_str) 
                elif prefix == 'last' :
                    end = base + relativedelta(months = 12) 
                    start = timeDelay(end, -number, unit, unit_str)

                elif prefix == 'ordinal' :
                    end = base + relativedelta(months = number* unit)
                    start = timeDelay(end, -1, unit, unit_str)
            end = end  + datetime.timedelta(days = -1)
            # 农历
            if '农' in number_ori or '阴' in number_ori or '正' in number_ori or '腊' in number_ori or len(lunar_indicator)>0 :
                start = lunar2solar(start)
                end = lunar2solar(end)

            times.append(
                {  'baseTime' :  base ,  'start_text' : start_year, 'end_text' : end_year,   'text' : string[start_year: end_year] ,  'start_period' :start,'end_period' : end}
            )
    return times


def get_period_month(string):
    string = t2s(string)
    times = []
    multi = re.search(pattern = pattern_multi, string = string)
    while multi is not None :
        multi_text  = multi.group()
        
        multi_time = parse_time(multi_text.replace('本年','今年').replace('这年','今年'))
        if len(multi_time) == 2:
            print('字段为:',multi_text)
            print('时间为:',multi_time)
            times.append(
                {   'text' :multi_text ,  'start_period' : multi_time[0].date(),'end_period' : multi_time[1].date()}
            )            
            string = string.replace(multi_text,'',1)
            multi = re.search(pattern = pattern_multi, string = string)

    indices_month =[ [m.start(0), m.end(0)] for m in re.finditer(pattern =  pattern_month, string = string)]
    
    indices_texts = []
    for [start_month, end_month] in indices_month:
        indices_texts.append( [ (start_month, end_month), re.findall(string = string[start_month:end_month], pattern= pattern_month)] )

    for [  (start_month, end_month) , texts ] in indices_texts :
        for text in texts :
            [
                month_ori, suffix, prefix, number, unit_str
            ] = text

            month = month_ori.replace("本年","今年").replace("这年","今年").replace('正月','一月').replace('腊月','十二月').replace('阴','').replace('农','').replace('历','')
            
            prefix = prefix_month[prefix] if prefix in prefix_month.keys() else 'ordinal'
            number = int(chineseDigits2arabicWithin1000(number)) if number else 1
            unit = unit_month[unit_str] if unit_str in unit_month.keys() else 1
            # print('表示月份的字段为 : ',month)
            base = parse_time(month)[0].date()
            # print("基准日期为 :", base)

            # 没有年信息则默认今年
            if '年' not in month_ori:
                base = datetime.datetime(year = datetime.datetime.now().year, month = base.month, day = base.day).date()
            
            if suffix == '上旬':
                start = base
                end = base +  datetime.timedelta( days = 10)             
            elif suffix == '中旬' :
                start = base + datetime.timedelta( days = 10)   
                end = base +  datetime.timedelta( days = 20)               
            elif suffix == '下旬':
                end = base + relativedelta(months = 1 )     
                start = base +  datetime.timedelta( days = 20)   
            elif suffix in ['底', '末'] :
                end = base + relativedelta(months = 1 )     
                start = end +  datetime.timedelta( days = -7)                   
            elif suffix in ['初', '首']:
                start = base
                end = base +  datetime.timedelta( days = 7)                   
            elif len(suffix) <1  :
                start = base 
                end = start + relativedelta( months= 1)
            else :
            
                if prefix == 'first':
                    start = base
                    end = base +  datetime.timedelta( days = number* unit) 
                elif prefix == 'last' :
                    end = base +   relativedelta( months= 1)
                    start = end +  datetime.timedelta( days = -number* unit)
                elif prefix == 'ordinal' :
                    end = base +  datetime.timedelta( days = number* unit)
                    start = end +  datetime.timedelta( days = - unit)
            end = end + datetime.timedelta(days = -1)
            # 农历
            if '农' in month_ori or '阴' in month_ori or '正月' in month_ori or '腊月' in month_ori :
                start = lunar2solar(start)
                end = lunar2solar(end)
            times.append(
                { 'baseTime': base,   'start_text' : start_month, 'end_text' : end_month,   'text' : string[start_month: end_month] ,  'start_period' :start,'end_period' : end }
            )
    return times


def get_period_holiday(string):
    string = t2s(string)
    indices_holiday =[ [m.start(0), m.end(0)] for m in re.finditer(pattern =  pattern_holiday, string = string)]
    
    indices_texts = []
    for [start_holiday, end_holiday] in indices_holiday:
        indices_texts.append( [ (start_holiday, end_holiday), re.findall(string = string[start_holiday:end_holiday], pattern= pattern_holiday)] )

    times = []
    for [  (start_holiday, end_holiday) , texts ] in indices_texts :
        for text in texts :
            [
                year_str_ori, holiday_str
            ] = text

            year_str = year_str_ori.replace("本年","今年").replace("这年","今年")                
            base = parse_time(year_str)[0]
            year = base.year
            holiday = dateAndDuration_holiday[holiday_str]
            # print(holiday)
            duration = holiday['duration']
            calendar = holiday['calendar']
            [month, day] = holiday['date']

            # if calendar == 'lunar':
                # converter = LunarSolarConverter()
                # lunar = Lunar(year, month, day, isleap=False)
                # # print(vars(lunar) )
                # solar = converter.LunarToSolar(lunar)
                # # print(vars(solar))
                # year = solar.solarYear
                # month = solar.solarMonth        
                # day = solar.solarDay  
            date_holiday = datetime.datetime(year = year, month = month, day = day).date()
            if calendar == 'lunar':
                date_holiday = lunar2solar(date_holiday)
            elif calendar == 'variedWithinMonth' : 
                ordinal = day 

                # weekday 从0到6,而不是从1到7
                weekday = holiday['weekday']-1
                weekday_1st = datetime.datetime(year = year, month = month, day = 1).date().weekday()
                # 月一号所在周还没过那个weekday
                if weekday >= weekday_1st:
                    ordinal -= 1
                    
                date_holiday = datetime.datetime(year = year, month = month, day = 1).date() + datetime.timedelta( days = ordinal*7+ weekday - weekday_1st)
            elif calendar == 'other':
                y = year
                n = y-1900
                a = n%19
                q = n//4
                b = (7*a+1)// 19
                m = (11*a+4-b)% 29
                w = (n+q+31-m) % 7
                d = 25-m-w
                date_holiday = datetime.datetime(year = year, month = 3, day = 31).date() + datetime.timedelta( days = d)                  

            start = date_holiday - datetime.timedelta(days = duration-1)
            end = date_holiday + datetime.timedelta(days = duration)

            times.append(
                { 
                    'baseTime': base,   'start_text' : start_holiday, 'end_text' : end_holiday,   'text' : string[start_holiday: end_holiday] , 
                    'start_period' :start,'end_period' : end + datetime.timedelta(days = -1), ' holiday_period' : date_holiday
                }
            )
    return times

def lunar2solar(date):
    print('阴历日子是:',date)
    year = date.year
    month = date.month
    day = date.day
    converter = LunarSolarConverter()
    lunar = Lunar(year, month, day, isleap=False)
    # print(vars(lunar) )
    solar = converter.LunarToSolar(lunar)
    # print(vars(solar))
    return datetime.datetime(year = solar.solarYear, month = solar.solarMonth , day = solar.solarDay  ).date()



def get_period_week(string):
    string = t2s(string)
    times = []

    indices_week =[ [m.start(0), m.end(0)] for m in re.finditer(pattern =  pattern_week, string = string)]
    
    indices_texts = []
    for [start_week, end_week] in indices_week:
        indices_texts.append( [ (start_week, end_week), re.findall(string = string[start_week:end_week], pattern= pattern_week)] )

    for [  (start_week, end_week) , texts ] in indices_texts :
        for text in texts :
            [
                year_str_ori, week_str, relative1, number2_str, relative2, withinWeek, firstOrlastOrOrd, number3_str, number4_str, secondWeekday,  number5_str
            ] = text

            base = datetime.datetime.now().date()

            # 有年的信息
            if year_str_ori :
                year_str = year_str_ori.replace("本年","今年").replace("这年","今年")
                base_year = parse_time(year_str)[0].date().year
                base_month = base.month
                base_day = base.day
                base = datetime.datetime(base_year, base_month, base_day).date()
            
            base_weekday = base.weekday()
            base_monday = base - datetime.timedelta(days = base_weekday) # 周一of the week in question
            
            # 上上周， 下下周, 本周， 这周
            if relative1:
                count_shang = relative1.count('上')
                count_xia = relative1.count('下')
                base_monday = base_monday + datetime.timedelta( days = 7* (count_xia - count_shang ) )

            # 一周前 或 五周后
            else:
                number2 = chineseDigits2arabicWithin1000(number2_str)
                if relative2 == '前':
                    base_monday = base_monday + datetime.timedelta( days = - 7* number2 )
                else :
                    base_monday = base_monday + datetime.timedelta( days =  7* number2 )

            if withinWeek in ['整周',' 一整周'] :
                start = base_monday
                end = start  + datetime.timedelta( days =  6 )                  
            elif withinWeek == '周中' :
                start = base_monday
                end = start  + datetime.timedelta( days =  4 )               
            elif withinWeek == '周末' :
                start = base_monday + datetime.timedelta( days =  5 )
                end = start  + datetime.timedelta( days =  1 )   
            # 缺失则为整周
            elif not withinWeek :         
                start = base_monday
                end = start  + datetime.timedelta( days =  6 )    
          
            else :
                # 周/星期/礼拜 几
                if withinWeek[0] in ['周','星', '礼']:
                    number4 = chs_weekday[number4_str]
                    start = base_monday + datetime.timedelta( days =  number4-1 ) 
                    end = start      
                    if number5_str:
                        number5 = chs_weekday[number5_str]
                        end = end + datetime.timedelta( days =  number5- number4 ) 
                # 前/后/开始/开头几天这种 
                else:             
                    prefix = prefix_month[firstOrlastOrOrd]       
                    number3 = chineseDigits2arabicWithin1000(number3_str)
                    try :
                        number3 = int(number3)
                    except :
                        print(number3)
                        number3 = 1
                    
                    if prefix == 'first':
                        start = base_monday
                        end = base_monday +  datetime.timedelta( days = number3-1) 
                    elif prefix == 'last' :
                        end = base_monday +  datetime.timedelta( days = 6) 
                        start = end - datetime.timedelta(days = number3-1)
                    elif prefix == 'ordinal' :
                        end = base_monday +  datetime.timedelta( days = number3-1 ) 
                        start = end 

            times.append(
                { 'baseTime': base,   'start_text' : start_week, 'end_text' : end_week,   'text' : string[start_week: end_week] ,  'start_period' :start,'end_period' : end }
            )
    return times