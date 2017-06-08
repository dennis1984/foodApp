#-*- coding:utf8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
import os
from datetime import datetime as _datetime

# 网关地址
ALIPAY_URL = 'https://openapi.alipay.com/gateway.do'

# 应用ID
APPID = '2017032906465224'

# 扫码支付调用方法
PRECREATE_METHOD = 'alipay.trade.precreate'

# 编码格式
CHARSET_UTF8 = 'utf-8'

# 签名算法类型
SIGN_TYPE_RSA2 = 'RSA2'
SIGN_TYPE_RSA = 'RSA'

# 发送请求的时间
TIMESTAMP = lambda: _datetime.strftime(_datetime.now(), '%Y-%m-%d %H:%M:%S')

# 调用的接口版本
VERSIOIN = '1.0'

# 应用授权
APP_AUTH_TOKEN = None

# 回调地址
NOTIFY_URL_PRE_CREATE = os.path.join(settings.WEB_URL_FIX, 'alipay/precreate_callback/')
# NOTIFY_URL = reverse('WXPay:native_callback',
#                      current_app=self.request.resolver_match.namespace)

# 应用私钥
APP_PRIVATE_KEY_FILE_PATH = os.path.join(
    settings.BASE_DIR,
    'PAY',
    'alipay',
    'alipay_key',
    'app_private_key.pem'
)

# 支付宝公钥
ALI_PUBLIC_KEY_FILE_PATH = os.path.join(
    settings.BASE_DIR,
    'PAY',
    'alipay',
    'alipay_key',
    'alipay_public_key.pem'
)

