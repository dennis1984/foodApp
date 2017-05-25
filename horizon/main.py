#-*- coding:utf8 -*-
from django.conf import settings
import datetime


def timezoneStringTostring(timezone_string):
    """
    rest framework用JSONRender方法格式化datetime.datetime格式的数据时，
    生成数据样式为：2017-05-19T09:40:37.227692Z 或 2017-05-19T09:40:37Z
    此方法将数据样式改为："2017-05-19 09:40:37"，
    返回类型：string
    """
    if not isinstance(timezone_string, (str, unicode)):
        return ""
    if not timezone_string:
        return ""
    timezone_string = timezone_string.split('.')[0]
    timezone_string = timezone_string.split('Z')[0]
    try:
        timezone = datetime.datetime.strptime(timezone_string, '%Y-%m-%dT%H:%M:%S')
    except:
        return ""
    return str(timezone)

