#-*- coding:utf8 -*-

from PAY.alipay import settings as ali_settings
import requests
import json
import base64
import urllib

from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5


FIELDS = ('out_trade_no',          # 商户订单号
          'seller_id',             # 卖家支付宝用户ID（可选）
          'total_amount',          # 订单总金额（单位为元）
          'discountable_amount',   # 可打折金额（可选）
          'undiscountable_amount ',  # 不可打折金额（可选）
          'buyer_logon_id',          # 买家支付宝账号（可选）
          'subject',               # 订单标题
          'body',                  # 对交易或商品的描述（可选）
          'goods_detail',          # 商品列表信息（可选）
          'operator_id',           # 商户操作员编号（可选）
          'store_id',              # 商户门店编号（可选）
          'terminal_id',           # 商户机具终端编号（可选）
          'extend_params',         # 业务扩展参数（可选）

          'timeout_express',       # 该笔订单允许的最晚付款时间（可选）
          # 取值范围：1m～15d。m-分钟，h-小时，d-天，1c-当天（1c-当天的情况下，无论交易何时创建，都在0点关闭）。
          # 该参数数值不接受小数点， 如 1.5h，可转换为 90m。

          'royalty_info',          # 描述分账信息（可选）
          'sub_merchant',          # 二级商户信息（可选）
          'alipay_store_id',       # 支付宝店铺的门店ID（可选）
          )

GOODS_DETAIL_FIELDS = ('goods_id',          # 商品的编号
                       'alipay_goods_id',   # 支付宝定义的统一商品编号 (可选)
                       'goods_name',        # 商品名称
                       'quantity',          # 商品数量
                       'price',             # 商品单价，单位为元
                       'goods_category',    # 商品类目 （可选）
                       'body',              # 商品描述信息（可选）
                       'show_url',          # 商品的展示地址（可选）
                       )


class AliPayPreCreate(object):
    def __init__(self, out_trade_no=None, total_amount=None, subject=None, **kwargs):
        if not (out_trade_no and total_amount and subject):
            raise Exception('fields [out_trade_no, total_amount, subject] must be not empty!')

        self.app_id = ali_settings.APPID
        self.method = ali_settings.PRECREATE_METHOD
        self.charset = ali_settings.CHARSET_UTF8
        self.sign_type = ali_settings.SIGN_TYPE_RSA2            # 签名类型
        self.timestamp = ali_settings.TIMESTAMP()               # 发送请求的时间
        self.version = ali_settings.VERSIOIN
        self.notify_url = ali_settings.NOTIFY_URL_PRE_CREATE    # 回调地址
        self.app_auth_token = None                              # 应用授权
        self.biz_content = self.get_biz_content(out_trade_no,
                                                total_amount,
                                                subject, **kwargs)
        self.sign = self.make_sign()                            # 签名

    class Meta:
        fields = ('app_id', 'method', 'charset', 'sign_type', 'timestamp',
                  'version', 'notify_url', 'app_auth_token', 'sign',
                  'biz_content')

    def get_biz_content(self, out_trade_no, total_amount, subject, **kwargs):
        content_dict = {'out_trade_no': out_trade_no,
                        'total_amount': float(total_amount),
                        'subject': subject}
        for _key in kwargs:
            if kwargs[_key] and _key in FIELDS:
                if _key == 'goods_detail':
                    goods_detail = self.get_goods_detail(kwargs[_key])
                    content_dict[_key] = goods_detail
                else:
                    content_dict[_key] = kwargs[_key]
        return json.dumps(content_dict)

    def get_goods_detail(self, detail_list):
        _detail_list = []
        for item in detail_list:
            detail_dict = {'goods_id': str(item['id']),
                           'goods_name': item['title'],
                           'quantity': item['count'],
                           'price': float(item['price'])}
            _detail_list.append(detail_dict)
        return _detail_list

    def make_sign(self):
        """
        生成签名（私钥签名）
        """
        key_list = []
        for _key in self.Meta.fields:
            if _key == 'sign':
                continue
            if getattr(self, _key, None):
                key_list.append({'key': _key, 'value': getattr(self, _key)})
        key_list.sort(key=lambda x: x['key'])

        string_param = ''
        for item in key_list:
            string_param += '%s=%s&' % (item['key'], item['value'])
        else:
            string_param = string_param[:-1]

        pri_key = RSA.importKey(open(ali_settings.APP_PRIVATE_KEY_FILE_PATH))
        hash_obj = SHA256.new(string_param)
        signer = PKCS1_v1_5.new(pri_key)
        sign_b64_str = base64.b64encode(signer.sign(hash_obj))
        return sign_b64_str

    @property
    def request_data(self):
        params_dict = {}
        for _key in self.Meta.fields:
            if getattr(self, _key, None):
                params_dict[_key] = getattr(self, _key)
        return params_dict

    def go_to_pay(self):
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
        request_url = '%s?%s' % (ali_settings.ALIPAY_URL, urllib.urlencode(self.request_data))
        results = requests.get(request_url,
                               headers=headers)
        return results
