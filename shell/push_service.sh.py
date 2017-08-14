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

WX_PUSH_RUL = 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=ACCESS_TOKEN'

PUSH_TEMPLATE_DICT = {
    'comment_push': {'template_id': 'LMOyfEKJQAMRI1fIVEjUJPyShG2VGe3vG8Z5AGg36HI',
                     'data': {'first': u'您好， 感谢您的用餐。',
                              'keyword1': u'',
                              'keyword2': u'',
                              'remark': u'点击详情反馈您的用餐体验， 将帮助我们更好提升服务。'},
                     'url': 'http://'
                     },
}

PUSH_LIST = [{'push_template_name': 'comment_push',
              'push_table': {'table_name': 'ys_push_detail',
                             'sql': collections.OrderedDict(**{
                                 'push_start_time__gte': datetime.datetime.now,
                                 'status': 0}),
                             },
              }]


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
                key = key.split('__')
                _filter = 'equal'
            if callable(value):
                value = value()
            params_list.append('%s%s%s' % (key, _filter, value))

        sql = "select * from %s where %s" % (table, 'and'.join(params_list))
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


class WXPush(object):
    def __init__(self, out_open_id, template_name, data_dict):
        self.touser = out_open_id
        self.template_id = PUSH_TEMPLATE_DICT.get(template_name, {}).get('template_id')
        self.url = PUSH_TEMPLATE_DICT.get(template_name, {}).get('url')

        data_tmp = {}
        for key, value in PUSH_TEMPLATE_DICT[template_name]['data'].items():
            if key in data_dict:
                data_tmp[key] = {'value': data_tmp[key]}
            else:
                data_tmp[key] = {'value': value}
        self.data = data_tmp

    def go_to_push(self):
        request_data = self.__dict__
        return http_request.send_http_request(WX_PUSH_RUL, request_data, method='post')


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
