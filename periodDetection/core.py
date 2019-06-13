# -*- coding: utf-8 -*-
"""
Created on the 30th Apr 2018

@author : woshihaozhaojun@sina.com
"""
import re
import datetime
from termcolor import colored
import datetime
import sys
from dateutil.relativedelta import relativedelta
import re
from .Traditional2Simplified_module import Converter
import datetime
import jieba
from periodDetection.patterns import (
    CHS_ARABIC_MAP, 
    PATTERN, PATTERN2, 
    POS_AFFIX_DICT, UNIT_DICT, LEVEL_DICT
)
from .LunarSolarConverter_module import LunarSolarConverter, Solar, Lunar

def t2s(sentence):
    """繁体字转为简体字
    
    Args: 
        sentence(str) :- 待转换的句子 
    Return: 
        将句子中繁体字转换为简体字之后的句子 
    """
    sentence = Converter('zh-hans').convert(sentence)
    return sentence

def chineseDigits2arabicWithin10000(chineseDigit):
    """1000以内的中文数字转为阿拉伯数字
    
    Args:
        chineseDigit(str) :- 待转换的中文字符串
    Returns:
        阿拉伯数字, str
    """
    result  = 0
    word_list = list(chineseDigit)
    inside = False

    for count in range(len(chineseDigit)):
        curr_char  = chineseDigit[count]
        if chineseDigit[count:count+2] in ["零零", "00"]:
            word_list[count] = ""
            count += 1
            curr_char = "千"

        if curr_char in CHS_ARABIC_MAP:
            word_list[count] =""
            curr_digit = CHS_ARABIC_MAP[curr_char]
            # 遇到千
            if curr_digit == 1000:
                result *= 1000
            # 遇到百
            elif curr_digit == 100:
                result *= 100
            # 遇到十
            elif curr_digit == 10:
                if not inside:
                    result = 10
                elif result > 10:
                    result += result % 10 * 9
                else:
                    result *= curr_digit 
            # 0-9        
            else:
                result = result + curr_digit
            inside = True

        else:
            if inside:
                if count > 0:
                    word_list[count-1] = str(result) 
            inside = False
            result = 0
    if inside:
        word_list[-1] = str(result)
    return "".join(word_list)

def decalageDuTemp(base, number, unit_str):
    """得到与基础时间节点相差给定时间差距的时间节点

    Args:
        base(datetime.dateime) :- 基础时间节点
        number(int) :- 时间单位的数量
        unit_str(str) :- 表示时间单位的字符,
                        choices = {
                            'month', 'week', 'day'
                        }
    """
    if unit_str in ['month']:
        base = base + relativedelta(months = number)
    elif unit_str in ['week']:
        base = base + datetime.timedelta(days=7*number-base.weekday())
    elif unit_str in ['day']:
        base = base + datetime.timedelta(days=number)
    else :
        raise NameError("unit_str请在{month, week, day}中选")
    return base

def inheritHighOrderTime(previous_time, level_int, date_dict):
    """继承上次时间节点的高阶时间
    比如本次时间最高单位为日,则继承上次的年和月

    Args:
        previous_time(datetime.datetime) :- 上次时间节点
        level(int) :- 本次时间最高单位
        date_dict(dict) :- 记录日期的字典
    Returns:
        commands(iterables) :- 要执行的语句
    """
    date_dict = {}
    LEVEL_DICT_INVERSE = {
        "0" : "date_dict['year'] = {}".format(previous_time.year),
        "-1" : "date_dict['month'] = {}".format( previous_time.month),
        "-2" : "date_dict['day'] = {}".format(previous_time.day)
    }
    for i in range(level_int+1, 0):
        exec(LEVEL_DICT_INVERSE[str(i)])

def get_period(string_ori):
    """用递归的方式来检测中文文本中包含的时间段

    Args:
        string_ori(str) :- 可能包含时间段的中文文本
    """
    string = chineseDigits2arabicWithin10000(string_ori)
    print("原始句为 : {}\n转化中文数字后的句子为 : {}\n".format(
        string_ori, string
        )
    )
    date_dict =dict()
    match = re.search(pattern=PATTERN, string=string)
    now = datetime.datetime.now()
    start = now

    periods= []

    while match is not None:
        # print('\n新的一轮:')
        datum = dict()
        root = match.group('root')
        ordinal_root = match.group('ordinal_root')
        unit_root = match.group('unit_root')

        pos_affix_ori = match.group('pos_affix')
        unit_affix = match.group('unit_affix')
        number_affix_ori = match.group('number_affix')
        number_special = match.group("number_special")
        [number_unit_root, unit_unit_root] = UNIT_DICT[unit_root] if unit_root else [0, '']

        count_da = ordinal_root.count('大') if ordinal_root else 0
        count_shang = ordinal_root.count('上') if ordinal_root else 0
        count_xia = ordinal_root.count('下') if ordinal_root else 0
        
        if unit_affix in ["星期","礼拜","周"] and number_special is not None:
            datum["字段"] = match.group()
            # print('  pattern匹配到的字段 : ', colored(match.group(), 'green'))
        else :
            datum["字段"] = re.search(pattern = PATTERN2, string = string).group()
            # print('  pattern匹配到的字段 : ', colored(re.search(pattern = PATTERN2, string = string).group(), 'green'))

        ### 是否继承时间 ###
        ############ start
        for i in re.finditer(pattern = PATTERN, string = string):
            start_index = i.start(0)
            break
        # 离得太远则不继承
        if start_index > 10:
            # print("离得太远,不继承了")
            date_dict = {
                'year' : now.year,
                'month' : now.month,
                'day' : now.day
            }
            start = now
        ############# end

        # 改这里,root也能继承 level2inherit
        if root is not None:
            # print('匹配到root了 !')
            level_root = LEVEL_DICT[unit_unit_root]
            date_dict['level2inherit'] = level_root

            month = now.month
            year = now.year
            day = now.day
            weekday = now.weekday()

            # 继承之前高阶的时间,比如本次时间最高单位{level_root}为月,则继承之前的年
            if 'level2inherit' in date_dict:
                # print("继承上次时间", start)
                date_dict.update(
                    {
                    "year" : start.year,
                    "month" : start.month,
                    "day" : start.day
                    }
                )
                if level_root<0:
                    inheritHighOrderTime(start, level_int=level_root, date_dict=date_dict)
                year = date_dict["year"]
                month = date_dict['month']
                day = date_dict['day']  
                # print("root继承到的时间为", start)

            match_digit = re.search(pattern=r'\d+', string=ordinal_root)

            # 年,整年,全年
            if unit_unit_root == 'month' and number_unit_root ==12:
                year = now.year
                month = now.year 
                day = now.day 
                if match_digit is not None:
                    year = int(match_digit.group())
                elif '这'  in ordinal_root  or '本' in ordinal_root or '今' in ordinal_root:
                    year = year
                elif '去' in ordinal_root :
                    year = year-1
                elif '明' in ordinal_root:
                    year = year+1
                elif '前' in ordinal_root:
                    year = year-2 - count_da
                elif '后' in ordinal_root:
                    year = year+2+ count_da
                unit_unit_root = 'year'
                start = datetime.datetime(year, 1 ,1)
                end = datetime.datetime(year, 12 ,31)
            # 半年
            elif number_unit_root == 6 and unit_unit_root == 'month' :
                if match_digit is not None:
                    year = int(match_digit.group())
                    start = datetime.datetime(year=year, month=1, day=1)
                    end = datetime.datetime(year=year, month=12, day=31)
                # 上半年
                if count_shang > 0:
                    start = datetime.datetime(year=year, month=1, day=1)
                    end = datetime.datetime(year=year, month=6, day=30)
                # 下半年
                elif count_xia > 0:
                    start = datetime.datetime(year=year, month=7, day=1)
                    end = datetime.datetime(year=year, month=12, day=31)
                # else :
                #     print('半年级别没匹配到')
            # 月
            elif unit_unit_root == 'month':
                if match_digit is not None:
                    month = int(match_digit.group())
                    start = datetime.datetime(year=year, month=month, day=1)
                    end = datetime.datetime(year=year, month=month+1, day=1) - datetime.timedelta(days=1)
                elif count_shang > 0:
                    month = month - count_shang
                    start = datetime.datetime(year=year, month=month, day=1)
                    end = datetime.datetime(year=year, month=month+1, day=1) - datetime.timedelta(days=1)
                elif count_xia > 0:
                    month = month + count_xia
                    start = datetime.datetime(year=year, month=month, day=1)
                    end = datetime.datetime(year=year, month=month+1, day=1) - datetime.timedelta(days=1)
                # else:
                #     print('月级别没匹配到')
            # 周
            elif unit_unit_root == 'week':
                day = day - weekday
                if count_shang > 0:
                    start = now - datetime.timedelta(days=weekday+count_shang*7)
                    end = start + datetime.timedelta(days=6)
                elif count_xia > 0:
                    start = now + datetime.timedelta(days=-weekday+count_xia*7)
                    end = start + datetime.timedelta(days=6)     
                # else:
                #     print('周级别没匹配到')
            # print('  root字段 : ',colored(root, 'yellow'))    
            # print('  root开始的日子 : ', colored(start.date(), 'yellow'))
            # print('  root结束的日子 : ', colored(end.date(), 'yellow')  ) 
            # print('  level_root : ', colored(level_root, 'yellow')  ) 
        
        # 没有数量词则默认为1
        # 比如上周,表示上一周
        if not number_affix_ori:
            number_affix =  1
        else:
            number_affix = int(number_affix_ori)
        [number_unit_affix, unit_unit_affix] = UNIT_DICT[unit_affix] 

        if root is None:
            # 之前已经有时间了
            # 继承之前高阶的时间,比如本次时间最高单位{level_root}为月,则继承之前的年
            if "level_affix" in locals() and date_dict.get("level2inherit", 0) < 0:
                # print("继承上次时间", start)
                date_dict.update( 
                    {
                        "year" : start.year,
                        "month" : start.month,
                        "day" : start.day
                    }
                )
                inheritHighOrderTime(start, level_int=date_dict['level2inherit'], date_dict=date_dict)
                start = datetime.datetime(year=date_dict["year"], month=date_dict['month'], day=date_dict['day'])
                # print("affix继承到的时间为", start)

        level_affix = LEVEL_DICT[unit_unit_affix]

        # 没有表示相对位置的词则默认为第
        # 比如今年三月,表示今年第三月
        pos_affix = POS_AFFIX_DICT[pos_affix_ori] if pos_affix_ori else 'ordinal'


        """affix只匹配到一个时间单位或者时间单位+数字

        如果是(周|星期|礼拜)\d,且上次时间单位为周,则匹配

        否则用英文单词来代替时间单位,继续匹配.避免
        1.因为把时间单位词理解成第1个单位,比如因为缺省把"周"理解为第一周.
        2.没有意义的时间如年
        """
        if number_affix_ori is None and pos_affix_ori is None:
            # print("只匹配到一个时间单位或者时间单位+数字")
            # print("unit_affix : {}   number_special : {}  level2inhe : {}".format(
            #     unit_affix, number_special, date_dict["level2inherit"]
            # ))
            if unit_affix in ["星期","礼拜","周"] and number_special is not None and date_dict['level2inherit'] <= -2:
                # print("匹配到周几")
                # print(start)
                start = decalageDuTemp(start, int(number_special)-start.weekday()-1 , 'day')
                end = start
            else:
                string = re.sub(unit_affix, unit_unit_affix, string ,1)
                # print("没有意义的匹配\n  用{}取代{}\n".format(
                #     unit_unit_affix, unit_affix 
                # ))
                match = re.search(pattern=PATTERN, string=string)
                continue 

        elif pos_affix in ['first']:
            start = start
            end = decalageDuTemp(start, number_affix*number_unit_affix, unit_unit_affix) - datetime.timedelta(days=1)
        elif pos_affix in ['last']:
            start = decalageDuTemp(end, -number_affix*number_unit_affix, unit_unit_affix)
        # 第几
        else:
            inheritHighOrderTime(start, level_int=level_affix, date_dict=date_dict)

            if date_dict.get('level2inherit', 0) == 0: # 上次时间是年
                start = datetime.datetime(start.year, 1, 1)
                end = end
            elif date_dict['level2inherit'] == -1: # 上次时间是月
                start = datetime.datetime(start.year, start.month, 1)
            elif date_dict['level2inherit'] == -2: # 上次时间是周
                start = decalageDuTemp(start, 0 ,'week')

            start = decalageDuTemp(start, (number_affix-1)*number_unit_affix, unit_unit_affix)
            end = decalageDuTemp(start, number_unit_affix, unit_unit_affix) - datetime.timedelta(days=1)
        
        # 选取截取的文字
        if unit_affix in ["星期","礼拜","周"] and number_special is not None:
            for i in re.finditer(pattern=PATTERN, string=string):
                end_index = i.end(0)
                break
        else :
            for i in re.finditer(pattern=PATTERN2, string=string):
                end_index = i.end(0)
                break
        string = string.lstrip(string[:end_index])

        datum["开始日期"], datum["结束日期"] = start.date(), end.date()
        match = re.search(pattern=PATTERN, string=string)

        date_dict['level2inherit'] = level_affix
        date_dict['year'] = start.year 
        date_dict['month'] = start.month
        date_dict['day'] = start.day
        
        periods.append(datum)
    return periods

