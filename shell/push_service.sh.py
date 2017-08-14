# -*- coding:utf8 -*-

import MySQLdb
import http_request
import copy
import time
import datetime
import collections


DB_SETTINGS = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'yinShi',
    'USER': 'yinShi_project',
    'PASSWORD': 'Con!082%Trib',
    'HOST': '127.0.0.1',
    'PORT': 3306,
}

SQL_FILTER_DICT = {
    'gte': '>=',
    'gt': '>',
    'lte': '<=',
    'lt': '<',
    'equal': '='
}

WX_PUSH_RUL = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s'

WX_ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/cgi-bin/token'

WX_ACCESS_TOKEN_PARAMS = {
    'appid': 'wx55da5a50194f8c73',
    'secret': 'WWWWWWWWWW',
    'grant_type': 'client_credential',
}

PUSH_TEMPLATE_DICT = {
    'comment_push': {'template_id': 'LMOyfEKJQAMRI1fIVEjUJPyShG2VGe3vG8Z5AGg36HI',
                     'data': {'first': u'您好， 感谢您的用餐。',
                              'keyword1': u'',
                              'keyword2': u'',
                              'remark': u'点击详情反馈您的用餐体验， 将帮助我们更好提升服务。'},
                     'url': 'http://'
                     },
}

PUSH_LIST = [
    {
        'push_template_name': 'comment_push',
        'push_table': {
            'table_name': 'ys_push_detail',
            'sql': collections.OrderedDict(**{
                'push_start_time__lte': datetime.datetime.now,
                'status': 0}),
        },
    }
]

ACCESS_TOKEN_TABLE = {
    'table_name': 'ys_wx_access_token',
    'sql': {'select': {'expires__gt': datetime.datetime.now},
            'insert': collections.OrderedDict(**{
                'access_token': None,
                'expires': None,
                'created': datetime.datetime.now
            })},

}


class DB(object):
    def __init__(self):
        conn = MySQLdb.connect(host=DB_SETTINGS['HOST'],
                               user=DB_SETTINGS['USER'],
                               passwd=DB_SETTINGS['PASSWORD'],
                               db=DB_SETTINGS['NAME'],
                               port=DB_SETTINGS['PORT'],
                               charset="utf8")
        self.cursor = conn.cursor()

    def select(self, table, params):
        params_list = []
        for key, value in params.items():
            if '__' in key:
                key, _filter = key.split('__')
            else:
                _filter = 'equal'
            if callable(value):
                if value == datetime.datetime.now:
                    value = '"%s"' % timezoneStringTostring(str(value()))
                else:
                    value = value()
            params_list.append('%s %s %s' % (key, SQL_FILTER_DICT[_filter], value))

        sql = "select * from %s where %s;" % (table, ' and '.join(params_list))
        try:
            count = self.cursor.execute(sql)
        except Exception as e:
            return e
        if not count:
            return Exception('No data')
        db_description = self.cursor.description
        perfect_details = []
        for item in self.cursor.fetchall():
            tmp_dict = {}
            for index, value in enumerate(item):
                tmp_dict[db_description[index][0]] = value
            perfect_details.append(tmp_dict)
        return perfect_details

    def insert(self, table, initial_data):
        key_list = []
        value_list = []
        for key, value in initial_data.items():
            key_list.append(key)
            value_list.append(value)

        SQL = 'insert into %s values(%s) (%s)' % (table, key_list, value_list)
        try:
            self.cursor.execute(SQL)
        except Exception as e:
            return e
        return self.cursor.fetchall()


class WXPush(object):
    def __init__(self, out_open_id, template_name, data_dict):
        self.touser = out_open_id
        self.template_id = PUSH_TEMPLATE_DICT.get(template_name, {}).get('template_id')
        self.url = PUSH_TEMPLATE_DICT.get(template_name, {}).get('url', '%s') % self.access_token

        data_tmp = {}
        for key, value in PUSH_TEMPLATE_DICT[template_name]['data'].items():
            if key in data_dict:
                data_tmp[key] = {'value': data_dict[key]}
            else:
                data_tmp[key] = {'value': value}
        self.data = data_tmp

    def go_to_push(self):
        request_data = self.__dict__
        return http_request.send_http_request(WX_PUSH_RUL, request_data, method='post')

    @property
    def access_token(self):
        wx_access = WXAccessToken().get_access_token()
        if isinstance(wx_access, Exception):
            return None
        return wx_access['access_token']


class WXAccessToken(object):
    table = ACCESS_TOKEN_TABLE['table_name']

    def get_access_token(self):
        params = ACCESS_TOKEN_TABLE['sql']['select']

        instances = DB().select(table=self.table, params=params)
        if isinstance(instances, Exception):
            return instances
        if instances:
            return instances[0]
        else:
            token_data = self.go_to_get_token()
            self.insert_data(token_data)
            return token_data

    def insert_data(self, initial_data):
        params_dict = copy.deepcopy(ACCESS_TOKEN_TABLE['sql']['insert'])
        initial_data['expires'] = make_time_delta(seconds=initial_data.pop('expires_in'))
        params_dict.update(**initial_data)

        return DB().insert(table=self.table, initial_data=params_dict)

    def go_to_get_token(self):
        return http_request.send_http_request(WX_ACCESS_TOKEN_URL,
                                              WX_ACCESS_TOKEN_PARAMS,
                                              method='get')


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
        timezone = datetime.datetime.strptime(timezone_string, '%Y-%m-%d %H:%M:%S')
    except:
        return ""
    return str(timezone)


def make_time_delta(days=0, minutes=0, seconds=0):
    """
    设置时间增量
    """
    return datetime.datetime.now() + datetime.timedelta(days=days,
                                                        minutes=minutes,
                                                        seconds=seconds)


def push_service():
    for item in PUSH_LIST:
        template_name = item['push_template_name']
        push_table = item['push_table']['table_name']
        params_dict = item['push_table']['sql']

        push_details = DB().select(push_table, params_dict)
        if isinstance(push_details, Exception):
            return

        for detail in push_details:
            wx_instance = WXPush(out_open_id=detail['out_open_id'],
                                 template_name=template_name,
                                 data_dict={'keyword1': detail['business_name'],
                                            'keyword2': detail['created']})
            wx_instance.go_to_push()
            time.sleep(0.5)


if __name__ == '__main__':
    push_service()
