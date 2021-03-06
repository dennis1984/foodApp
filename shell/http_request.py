# -*- coding:utf8 -*-

import requests
import urllib
import json

http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']


def send_http_request(access_url, access_params, method='get',
                      content_type='application/json', charset='UTF-8', **kwargs):
    """
    发送http request请求
    """
    if method not in http_method_names:
        return TypeError("Http request cannot confirm the %s method!" % method)

    headers = {'Content-Type': '%s; %s' % (content_type, charset)}
    if 'add_header' in kwargs:
        for key, value in kwargs['add_header'].items():
            headers[key] = value

    kwargs = {}
    if method == 'get':
        if isinstance(access_params, dict):
            access_params = urllib.urlencode(access_params)
        request_url = '%s?%s' % (access_url, access_params)
    else:
        request_url = access_url
        if isinstance(access_params, dict):
            kwargs = {'data': json.dumps(access_params)}
        else:
            kwargs = {'data': access_params}

    handle = getattr(requests, method)
    try:
        results = handle(request_url, headers=headers, **kwargs)
    except Exception as e:
        return e
    return results
