#-*- coding:utf8 -*-
from PAY.wxpay import settings as wx_settings
from PAY.alipay import settings as ali_settings
from django.conf import settings
from django.utils.timezone import now
from lxml import etree
import datetime
import qrcode
import json
import os
import uuid
from hashlib import md5
import base64

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256


def minutes_30_plus():
    return now() + datetime.timedelta(minutes=30)


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


def make_qrcode(source_data, version=5):
    """
    生成二维码图片
    """
    qr = qrcode.QRCode(version=version,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=10,
                       border=4)
    qr.add_data(source_data)
    qr.make(fit=True)
    fname = "%s.png" % uuid.uuid4()
    qrcode_dir = settings.PICTURE_DIRS['business']['qrcode']
    fname_path = os.path.join(qrcode_dir, fname)

    if not os.path.isdir(qrcode_dir):
        os.makedirs(qrcode_dir)
    image = qr.make_image()
    image.save(fname_path)
    return fname_path


def anaysize_xml_to_dict(source):
    """
    解析xml字符串
    """
    root = etree.fromstring(source)
    result = {article.tag: article.text for article in root}
    return result


def make_dict_to_xml(source_dict, use_cdata=True):
    """
    生成xml字符串
    """
    if not isinstance(source_dict, dict):
        raise ValueError('Parameter must be dict.')

    xml = etree.Element('xml')
    for _key, _value in source_dict.items():
        _key_xml = etree.SubElement(xml, _key)
        if _key == 'detail':
            _key_xml.text = etree.CDATA(_value)
        else:
            if not isinstance(_value, (bytes, unicode)):
                _value = unicode(_value)
            if use_cdata:
                _key_xml.text = etree.CDATA(_value)
            else:
                _key_xml.text = _value

    xml_string = etree.tostring(xml,
                                pretty_print=True,
                                encoding="UTF-8",
                                method="xml",
                                xml_declaration=True,
                                standalone=None)
    return xml_string.split('\n', 1)[1]


def make_sign_for_wxpay(source_dict):
    """
    生成签名（微信支付）
    """
    key_list = []
    for _key in source_dict:
        if not source_dict[_key] or _key == 'sign':
            continue
        key_list.append({'key': _key, 'value': source_dict[_key]})
    key_list.sort(key=lambda x: x['key'])

    string_param = ''
    for item in key_list:
        string_param += '%s=%s&' % (item['key'], item['value'])
    # 把密钥和其它参数组合起来
    string_param += 'key=%s' % wx_settings.KEY
    md5_string = md5(string_param.encode('utf8')).hexdigest()
    return md5_string.upper()


def verify_sign_for_alipay(params_str, source_sign):
    """
    支付宝支付验证签名（公钥验证签名）
    """
    pub_key = RSA.importKey(open(ali_settings.ALI_PUBLIC_KEY_FILE_PATH))
    source_sign = base64.b64decode(source_sign)
    _sign = SHA256.new(params_str)
    verifer = PKCS1_v1_5.new(pub_key)
    return verifer.verify(_sign, source_sign)


def make_dict_to_verify_string(params_dict):
    """
    将参数字典转换成待签名的字符串
    """
    params_list = []
    for key, value in params_dict.items():
        if not value or key == 'sign':
            continue
        params_list.append({'key': key, 'value': value})
    params_list.sort(key=lambda x: x['key'])
    params_str = ''
    for item in params_list:
        params_str += '%s=%s&' % (item['key'], (item['value']).encode('utf8'))
    else:
        params_str = params_str[:-1]
    return params_str
