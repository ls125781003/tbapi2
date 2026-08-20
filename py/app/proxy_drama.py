# -*- coding: utf-8 -*-
# 本资源来源于互联网公开渠道，仅可用于个人学习爬虫技术。
# 严禁将其用于任何商业用途，下载后请于 24 小时内删除，搜索结果均来自源站，本人不承担任何责任。

import traceback
from base64 import b64encode
from base.spider import Spider
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
from urllib.parse import quote_plus, unquote_plus, urlencode
import sys,time,json,random,hashlib,urllib3
from Crypto.Cipher import AES, PKCS1_v1_5
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append('..')

class Spider(Spider):
    cache_host = {}
    def localProxy(self, params):
        if params.get('type') == 'drama':
            response = '获取域名失败'
            try:
                if params.get('from') == 'host':
                        url = params.get('url')
                        if url.startswith('http'):
                            response = self.cache_host.get(url)
                            if not(response and isinstance(response,str) and response.startswith('http')):
                                res = self.fetch(url,headers={'User-Agent': 'okhttp/3.12.1'}).json()
                                print('域名获取结果：',res)
                                if res['domain'].startswith('http'):
                                    response =  res['domain']
                                    self.cache_host[url] = response
                elif params.get('from') == 'paramsData':
                    data = self.params_data(params)
                    response = data
                return [200, 'text/text;charset=utf-8', response]
            except Exception as e:
                return [500, 'text/text;charset=utf-8', f'处理出错: {e}\n\n错误堆栈:\n{traceback.format_exc()}']
        return None

    def params_data(self,params):
        ver_name = params.get('verName')
        ver = params.get('ver',ver_name.replace('.',''))
        app_name = params.get('AppName')
        pkg = params.get('pkg')
        public_key = params.get('publicKey').replace(' ','+')
        if not(ver and ver_name and app_name and pkg and public_key): return '请按要求传参'

        # 设备信息
        android_id = '313c3eeeb2a098a1'
        mac = '02:00:00:00:00:00'  # 网卡MAC地址
        model = '23113RKC6C'  # 型号
        manufacturer = 'Xiaomi'  # 制造商

        # 计算UUID
        uuid = hashlib.md5(f"{android_id}{mac}{model}{manufacturer}".encode()).hexdigest().upper()

        timestamp = self.get_13_digit_timestamp()
        random_str = self.random_str_function()

        # AES加密生成sign
        aes_key = 'OC1A06E197EF10CF3F6058CA7A803B5E'.encode()
        cipher_aes = AES.new(aes_key, AES.MODE_ECB)
        sign_data = f"{timestamp}{random_str}".encode()
        sign_encrypted = cipher_aes.encrypt(pad(sign_data, AES.block_size))
        sign = b64encode(sign_encrypted).decode()

        # 构建设备信息
        device_info = {
            "country": "CN",
            "vName": ver_name,
            "cpuId": "",
            "young": 0,
            "facturer": manufacturer,
            "pkg": pkg,
            "uuid": uuid,
            "resolution": "900x1600",
            "mac": quote_plus(mac),
            "sig": self.rsa_encrypt(f"{timestamp}{random_str}{ver}", public_key),
            "abid": "6249",
            "model": model,
            "plat": "android",
            "udid": uuid,
            "dpi": "240",
            "net": "1",
            "lang": "zh",
            "random_str": random_str,
            "brand": "Redmi",  # 品牌
            "timestamp": timestamp,
            "density": "3.25",
            "appName": quote_plus(app_name),
            "cpu": "arm64-v8a",
            "chid": "10000",
            "carrier": quote_plus('移动'),  # 网络运营商
            "sig2": sign[:8],
            "sig3": sign[8:],
            "_vOsCode": "32",
            "vOs": "12",  # 安卓版本
            "vApp": ver,
            "device": "0",
            "androidID": android_id
        }

        # JSON序列化并AES加密
        dat = json.dumps(device_info, ensure_ascii=False, separators=(',', ':'))

        # AES-128-CBC加密
        aes_key2 = 'ed5fdsgucxumegqa'.encode()
        iv = 'ed5fdsgucxumegqa'.encode()
        cipher_aes2 = AES.new(aes_key2, AES.MODE_CBC, iv)
        dat_encrypted = cipher_aes2.encrypt(pad(dat.encode(), AES.block_size))
        dat_hex = dat_encrypted.hex()
        return dat_hex

    def rsa_encrypt(self,plaintext, public_key_str):
        """RSA加密"""
        # 构建PEM格式的公钥
        public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_str}\n-----END PUBLIC KEY-----"

        # 导入公钥
        rsa_key = RSA.import_key(public_key_pem)
        cipher_rsa = PKCS1_v1_5.new(rsa_key)

        # 加密
        encrypted = cipher_rsa.encrypt(plaintext.encode())

        # Base64编码
        return b64encode(encrypted).decode()

    def random_str_function(self,length=16):
        """生成随机字符串"""
        char_array = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        result_str = ''
        i = 0

        while i < length - 1:
            c = random.choice(char_array)
            if c not in result_str:
                result_str += c
                i += 1

        return result_str + "="

    def get_13_digit_timestamp(self):
        """获取13位时间戳"""
        return int(round(time.time() * 1000))

    def init(self, extend=''):
        pass

    def homeContent(self, filter):
        pass

    def homeVideoContent(self):
        pass

    def categoryContent(self, tid, pg, filter, extend):
        pass

    def searchContent(self, key, quick, pg='1'):
        pass

    def detailContent(self, ids):
        pass

    def playerContent(self, flag, id, vipflags):
        pass

    def getName(self):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

if __name__ == "__main__":
    sp = Spider()
    formatJo = None
    # formatJo = sp.localProxy({"type": "drama", "from": "host", "url":"https://1234-1349250429.cos.ap-hongkong.myqcloud.com/app.txt"})  # host
    formatJo = sp.localProxy({"type": "drama","from": "paramsData", "verName": "3.0.1.7", "AppName": "橘汁", "pkg": "com.tjjiangh.android", "publicKey": "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCp9Ek4wIlQAtwFnuBRlsFiow2tr%2B4UOciGeNKbY7nL74etUqUb6fvpOSOHhFEfaWlfwUpOB17x3JEL3No19nfjCeVYrYPjlJcgoqUWH%2FtfIfFAQWvtxBIBlKazkhw8d3ChysWmeWRikKqkBsVRY4oqNPuj4sjm6Zult0U4I4prRQIDAQAB"})  # paramsData
    print(formatJo)