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
    CHS_ARABIC_MAP, PATTERN, POS_AFFIX_DICT, UNIT_DICT, LEVEL_DICT
)
from .LunarSolarConverter_module import LunarSolarConverter, Solar, Lunar

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

def chineseDigits2arabicWithin10000(chineseDigit, encoding="utf-8"):
    result  = 0
    word_list = list(chineseDigit)
    inside = False

    for count in range(len(chineseDigit)):
        curr_char  = chineseDigit[count]
        if chineseDigit[count:count+2] in ['零零', '00']:
            word_list[count] = ''
            count += 1
            curr_char = '千'

        if curr_char in CHS_ARABIC_MAP.keys():
            word_list[count] =''
            curr_digit = CHS_ARABIC_MAP[curr_char]
            # 遇到千
            if curr_digit == 1000 :
                result *= 1000
            # 遇到百
            elif curr_digit == 100 :
                result *= 100
            # 遇到十
            elif curr_digit == 10:
                if not inside:
                    result = 10
                elif result > 10 :
                    result += result%10 * 9
                else:
                    result *=  curr_digit 
            # 0-9        
            else:
                result = result + curr_digit
            inside = True

        else :
            if inside :
                if count > 0:
                    word_list[count-1] = str(result) 
            inside = False
            result = 0
    if inside :
        word_list[-1] = str(result)
    return ''.join(word_list)

def get_period(string_ori):
    string = chineseDigits2arabicWithin10000(string_ori)
    match = re.search(pattern = PATTERN, string = string)
    while match is not None:
        print('\n新的一轮:')
        # print('  pattern所在的字段 : ',string)
        print('  pattern匹配到的字段 : ', colored(match.group(), 'green'))
        root = match.group('root')
        ordinal_root = match.group('ordinal_root')
        unit_root = match.group('unit_root')
        # print('unit_root : ', unit_root  )
        pos_affix = match.group('pos_affix')
        unit_affix = match.group('unit_affix')
        number_affix = match.group('number_affix')
        [number_unit_root, unit_unit_root] = UNIT_DICT[unit_root] if unit_root else [0, '']
        # print('number_unit_root : ', number_unit_root)
        # print('unit_unit_root : ', unit_unit_root)
        now = datetime.datetime.now()
        count_da  = ordinal_root.count('大') if ordinal_root else 0
        count_shang = ordinal_root.count('上') if ordinal_root else 0
        count_xia = ordinal_root.count('下') if ordinal_root else 0

        if root is not None :
            # print('匹配到root了 !')
            month = now.month
            year = now.year
            day = now.day
            match_digit = re.search(pattern = r'\d+', string = ordinal_root)
            weekday = now.weekday()
            # 年,整年,全年
            if unit_unit_root == 'month' and number_unit_root ==12:
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
                    start = datetime.datetime(year = year, month = 1, day = 1)
                    end = datetime.datetime(year = year, month = 12, day = 31)
                # 上半年
                if count_shang > 0:
                    start = datetime.datetime(year = year, month = 1, day = 1)
                    end = datetime.datetime(year = year, month = 6, day = 30)
                # 下半年
                elif count_xia > 0 :
                    start = datetime.datetime(year = year, month = 7, day = 1)
                    end = datetime.datetime(year = year, month = 12, day = 31)
                else :
                    print('半年级别没匹配到')
            # 月
            elif unit_unit_root == 'month':
                if match_digit is not None :
                    month = int(match_digit.group())
                    start = datetime.datetime(year = year, month = month, day = 1)
                    end = datetime.datetime(year = year, month = month+1, day = 1) - datetime.timedelta(days = 1)
                elif count_shang > 0 :
                    month = month - count_shang
                    start = datetime.datetime(year = year, month = month, day = 1)
                    end = datetime.datetime(year = year, month = month+1, day = 1) - datetime.timedelta(days = 1)
                elif count_xia > 0 :
                    month = month + count_xia
                    start = datetime.datetime(year = year, month = month, day = 1)
                    end = datetime.datetime(year = year, month = month+1, day = 1) - datetime.timedelta(days = 1)
                else :
                    print('月级别没匹配到')
            # 周
            elif unit_unit_root == 'week' :
                day = day - weekday
                if count_shang > 0 :
                    start = now - datetime.timedelta(days = weekday + count_shang*7)
                    end = start + datetime.timedelta(days = 6)
                elif count_xia > 0 :
                    start = now + datetime.timedelta(days = -weekday + count_xia*7)
                    end = start + datetime.timedelta(days = 6)     
                else :
                    print('周级别没匹配到')
            level_root = LEVEL_DICT[unit_unit_root]
            print('  root字段 : ',colored(root, 'yellow'))    
            print('  root开始的日子 : ', colored(start.date(), 'yellow'))
            print('  root结束的日子 : ', colored(end.date(), 'yellow')  ) 
 
        if not number_affix :
            number_affix =  1
        else :
            number_affix = int(number_affix)
        [number_unit_affix, unit_unit_affix] = UNIT_DICT[unit_affix] if unit_affix else [0,'']

        level_affix = LEVEL_DICT[unit_unit_affix]


        pos_affix = POS_AFFIX_DICT[pos_affix] if pos_affix else 'ordinal'
        # print('number_affix : ', number_affix)
        # print('pos_affix : ',pos_affix)
        # print('number_unit_affix : ', number_unit_affix)
        # print('unit_unit_affix : ', unit_unit_affix)
        if pos_affix in ['first']:
            end = decalageDuTemp(start, number_affix * number_unit_affix, unit_unit_affix ) - datetime.timedelta(days = 1)
        elif pos_affix in ['last']:
            start = decalageDuTemp(end,  -number_affix * number_unit_affix, unit_unit_affix)
        else :
            if level_affix < level_root :
                if level_root == 0:
                    start = datetime.datetime(start.year, 1, 1)
                elif level_root == -1: 
                    start = datetime.datetime(start.year, start.month, 1)
                elif level_root == -2 :
                    start = decalageDuTemp(start, 0 ,'week')
                # elif unit_unit_affix == 'day' :
                #     start = decalageDuTemp(start, 1 - start.day   , unit_unit_affix)
            start = decalageDuTemp(start, (number_affix-1) * number_unit_affix, unit_unit_affix )
            end = decalageDuTemp(start, number_unit_affix, unit_unit_affix ) - datetime.timedelta(days = 1)

        for i in re.finditer(pattern = PATTERN, string = string):
            end_index = i.end(0)
            break
        string = string.lstrip( string[:end_index])
        print('这轮匹配到的时间段 :')
        print('  start : ', colored(start.date(), 'red'))
        print('  end : ', colored(end.date(), 'red'))
        print('  这轮的level_root和level_affix : {}和{}'.format(level_root, level_affix) )
        match = re.search(pattern = PATTERN, string = string)
        print('  剩下的字段 : ',string)

def decalageDuTemp(base, number, unit_str):
    if unit_str in ['month'] :
        base = base + relativedelta(months = number)
    elif unit_str in ['week'] :
        base = base + datetime.timedelta(days = 7*number -base.weekday())
    elif unit_str in ['day']:
        base = base + datetime.timedelta(days = number )
    else :
        raise NameError('unit_str请在{month, week, day}中选')
    return base