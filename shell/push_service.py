# -*- coding:utf8 -*-

import MySQLdb
import http_request
import copy
import time
import datetime
import collections
import json
import logging
import os


DB_SETTINGS = {
    'business': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yinShi',
        'USER': 'yinShi_project',
        'PASSWORD': 'Con!082%Trib',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    },
    'consumer': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yinShi_CS',
        'USER': 'yinShi_project',
        'PASSWORD': 'Con!082%Trib',
        'HOST': '127.0.0.1',
        'PORT': 3306,
    },
}

ENVIRONMENT_DICT = {
    'DEV': 10,        # 开发环境
    'TEST': 20,       # 测试环境
    'PRODUCE': 30,    # 生产环境
}
ENVIRONMENT = ENVIRONMENT_DICT['PRODUCE']

SQL_FILTER_DICT = {
    'gte': '>=',
    'gt': '>',
    'lte': '<=',
    'lt': '<',
    'equal': '='
}

WX_PUSH_RUL = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=%s'

WX_ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/cgi-bin/token'

# 微信推送详情地址
if ENVIRONMENT == 10:    # 开发环境
    WX_DETAIL_URL = 'http://yinshi.weixin.city23.com/comment/?id=%s'
elif ENVIRONMENT == 20:  # 测试环境
    WX_DETAIL_URL = 'http://yinshi.weixin.city23.com/comment/?id=%s'
elif ENVIRONMENT == 30:  # 生产环境
    WX_DETAIL_URL = 'http://yinshin.net/comment/?id=%s'
else:
    WX_DETAIL_URL = 'http://yinshi.weixin.city23.com/comment/?id=%s'

WX_ACCESS_TOKEN_PARAMS = {
    'appid': None,
    'secret': None,
    'grant_type': 'client_credential',
}

PUSH_TEMPLATE_DICT = {
    'comment_push': {'template_id': 'LMOyfEKJQAMRI1fIVEjUJPyShG2VGe3vG8Z5AGg36HI',
                     'data': {'first': u'您好， 感谢您的用餐。',
                              'keyword1': u'',
                              'keyword2': u'',
                              'remark': u'点击详情反馈您的用餐体验， 将帮助我们更好提升服务。'},
                     'url': WX_DETAIL_URL,
                     },
}

PUSH_LIST = [
    {
        'push_template_name': 'comment_push',
        'push_table': {
            'table_name': 'ys_push_detail',
            'sql': {'select': collections.OrderedDict(**{'push_start_time__lte': datetime.datetime.now,
                                                         'status': 0}),
                    'update': {'status': 1},
                    },
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

WX_APP_INFO_TABLE = {
    'db_name': 'consumer',
    'table_name': 'ys_wx_app_information',
    'sql': {}
}
WX_APP_INFO_TABLE_COLUMN = {
    'app_id': 'appid',
    'app_secret': 'secret',
}

PUSH_SUCCESS_INFO = {"errcode": 0,
                     "errmsg": "ok",
                     "msgid": None}

LOG_FILE_PATH = '/var/www/static/log'


class PushLogger(object):
    def __init__(self, level='DEBUG', file_name=None):
        self.logger = logging.getLogger('WeiXin PUSH')
        self.formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s',
                                           '%Y-%m-%d %H:%M:%S', )
        self.level = level

        save_path = os.path.dirname(file_name)
        if not os.path.isdir(save_path):
            os.makedirs(save_path)

        self.file_name = file_name
        file_handler = logging.FileHandler(self.perfect_file_name)
        file_handler.setFormatter(self.formatter)
        self.file_handle = file_handler
        self.logger.addHandler(file_handler)
        self.logger.setLevel(level=level)

    def debug(self, message, *args, **kwargs):
        return self.perfect_logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        return self.perfect_logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        return self.perfect_logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        return self.perfect_logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        return self.perfect_logger.critical(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        return self.perfect_logger.exception(message, *args, **kwargs)

    def log(self, level, message, *args, **kwargs):
        return self.perfect_logger.log(level, message, *args, **kwargs)

    @property
    def date_of_today(self):
        return datetime.date.today().strftime('%Y%m%d')

    @property
    def perfect_file_name(self):
        if self.date_of_today not in self.file_name:
            file_name_list = self.file_name.split('.')
            if len(file_name_list) == 2:
                perfect_fname = '%s.%s.%s' % (file_name_list[0],
                                              self.date_of_today,
                                              file_name_list[1])
            else:
                file_name_list[2] = self.date_of_today
                perfect_fname = '.'.join(file_name_list)
            return perfect_fname
        else:
            return self.file_name

    @property
    def perfect_logger(self):
        if self.perfect_file_name != self.file_name:
            self.file_name = self.perfect_file_name
            self.logger.removeHandler(self.file_handle)
            self.file_handle = logging.FileHandler(self.perfect_file_name)
            self.file_handle.setLevel(level=self.level)
            self.file_handle.setFormatter(self.formatter)
            self.logger.addHandler(self.file_handle)
        return self.logger


class DB(object):
    def __init__(self, db_name='business'):
        db_info = DB_SETTINGS[db_name]
        conn = MySQLdb.connect(host=db_info['HOST'],
                               user=db_info['USER'],
                               passwd=db_info['PASSWORD'],
                               db=db_info['NAME'],
                               port=db_info['PORT'],
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

        if not params_list:
            sql = "select * from %s" % table
        else:
            sql = "select * from %s where %s;" % (table, ' and '.join(params_list))
        try:
            count = self.cursor.execute(sql)
        except Exception as e:
            return e

        perfect_details = []
        if not count:
            return perfect_details

        db_description = self.cursor.description
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

        perfect_values = []
        for item in value_list:
            if isinstance(item, datetime.datetime):
                item = timezoneStringTostring(str(item))
            if isinstance(item, (str, unicode)):
                perfect_values.append("'%s'" % item)
            else:
                perfect_values.append(item)

        SQL = 'insert into %s (%s) values(%s);' % (table,
                                                   ','.join(key_list),
                                                   ','.join(perfect_values))
        try:
            self.cursor.execute(SQL)
            self.cursor.execute('flush privileges;')
        except Exception as e:
            return e
        return self.cursor.fetchall()

    def update(self, table, params, validated_data):
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

        perfect_values = []
        for key, value in validated_data.items():
            if isinstance(value, datetime.datetime):
                value = timezoneStringTostring(str(value))
            perfect_values.append('%s=%s' % (key, value))

        SQL = 'update %s set %s where %s;' % (table,
                                              ','.join(perfect_values),
                                              ' and '.join(params_list))
        try:
            self.cursor.execute(SQL)
            self.cursor.execute('flush privileges;')
        except Exception as e:
            return e
        return self.cursor.fetchall()


class WXPush(object):
    def __init__(self, out_open_id, template_name, orders_id, data_dict):
        self.touser = out_open_id
        self.template_id = PUSH_TEMPLATE_DICT.get(template_name, {}).get('template_id')
        self.url = PUSH_TEMPLATE_DICT.get(template_name, {}).get('url', '%s') % orders_id

        data_tmp = {}
        for key, value in PUSH_TEMPLATE_DICT[template_name]['data'].items():
            if key in data_dict:
                if isinstance(data_dict[key], datetime.datetime):
                    value2 = timezoneStringTostring(str(data_dict[key]),
                                                    do_not_show='second')
                    data_tmp[key] = {'value': value2}
                else:
                    data_tmp[key] = {'value': data_dict[key]}
            else:
                data_tmp[key] = {'value': value}
        self.data = data_tmp

    def go_to_push(self):
        request_data = self.__dict__
        request_url = WX_PUSH_RUL % self.access_token
        return http_request.send_http_request(request_url, request_data, method='post')

    @property
    def access_token(self):
        wx_token = WXAccessToken().get_access_token()
        if isinstance(wx_token, Exception):
            return None
        return wx_token['access_token']


class WXAccessToken(object):
    table = ACCESS_TOKEN_TABLE['table_name']

    def get_access_token(self):
        params = ACCESS_TOKEN_TABLE['sql']['select']

        instances = DB().select(table=self.table, params=params)
        if instances:
            return instances[0]
        else:
            token_data = self.go_to_get_token()
            if isinstance(token_data, Exception):
                return token_data
            self.insert_data(token_data)
            return token_data

    def insert_data(self, initial_data):
        params_dict = copy.deepcopy(ACCESS_TOKEN_TABLE['sql']['insert'])
        for key in params_dict.keys():
            if callable(params_dict[key]):
                if params_dict[key] == datetime.datetime.now:
                    params_dict[key] = params_dict[key]()

        initial_data['expires'] = make_time_delta(seconds=initial_data.pop('expires_in'))
        params_dict.update(**initial_data)

        return DB().insert(table=self.table, initial_data=params_dict)

    def go_to_get_token(self):
        # 获取APPID和APPSECRET
        handle = DB(db_name=WX_APP_INFO_TABLE['db_name'])
        instances = handle.select(table=WX_APP_INFO_TABLE['table_name'],
                                  params=WX_APP_INFO_TABLE['sql'])
        if isinstance(instances, Exception):
            return Exception('Can not find APPID and APPSECRET')

        detail = instances[0]
        wx_access_token_dict = copy.deepcopy(WX_ACCESS_TOKEN_PARAMS)
        update_params = {}
        for key in detail:
            if key in WX_APP_INFO_TABLE_COLUMN:
                update_params[WX_APP_INFO_TABLE_COLUMN[key]] = detail[key]
        wx_access_token_dict.update(**update_params)
        response = http_request.send_http_request(WX_ACCESS_TOKEN_URL,
                                                  wx_access_token_dict,
                                                  method='get')
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            return Exception('Request Failed')


def timezoneStringTostring(timezone_string, do_not_show=None):
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
    datetime_format = '%Y-%m-%d %H:%M:%S'
    slice_dict = {
        'second': -3,
        'minute': -6,
        'hour': -9,
        'day': -12,
        'month': -15,
        None: None,
    }

    timezone_string = timezone_string.split('.')[0]
    timezone_string = timezone_string.split('Z')[0]
    try:
        timezone = datetime.datetime.strptime(timezone_string, datetime_format)
    except:
        return ""
    return str(timezone)[:slice_dict[do_not_show]]


def make_time_delta(days=0, minutes=0, seconds=0):
    """
    设置时间增量
    """
    return datetime.datetime.now() + datetime.timedelta(days=days,
                                                        minutes=minutes,
                                                        seconds=seconds)


def push_service():
    logger = PushLogger(level='DEBUG',
                        file_name=os.path.join(LOG_FILE_PATH, 'push_weixin_result.log'))
    logger.info('PUSH Start')

    for item in PUSH_LIST:
        template_name = item['push_template_name']
        push_table = item['push_table']['table_name']
        params_dict = item['push_table']['sql']['select']
        update_params_dict = item['push_table']['sql']['update']

        push_details = DB().select(push_table, params_dict)
        if isinstance(push_details, Exception):
            return

        for detail in push_details:
            wx_instance = WXPush(out_open_id=detail['out_open_id'],
                                 template_name=template_name,
                                 orders_id=detail['orders_id'],
                                 data_dict={'keyword1': detail['business_name'],
                                            'keyword2': detail['created']})
            result = wx_instance.go_to_push()
            # 推送完成，回写推送状态
            if result.status_code == 200:
                result_info = json.loads(result.text)
                keys = ('errcode', 'errmsg')
                push_success = False
                for key in keys:
                    if result_info[key] != PUSH_SUCCESS_INFO[key]:
                        break
                else:
                    push_success = True
                if push_success:
                    logger.info('SUCCESS %s' % detail['orders_id'])
                    DB().update(push_table,
                                params={'id': detail['id']},
                                validated_data=update_params_dict)
                else:
                    logger.info('FAILED %s' % detail['orders_id'])
            time.sleep(0.5)
    logger.info('PUSH End.')

if __name__ == '__main__':
    push_service()
