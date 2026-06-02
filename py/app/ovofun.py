# -*- coding: utf-8 -*-
# 本资源来源于互联网公开渠道，仅可用于个人学习爬虫技术。
# 严禁将其用于任何商业用途，下载后请于 24 小时内删除，搜索结果均来自源站，本人不承担任何责任。

from Crypto.Cipher import AES
from base.spider import Spider
from Crypto.Util.Padding import unpad
import re,sys,json,base64,urllib3,hashlib
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append('..')

class Spider(Spider):
    headers,host = {
        'User-Agent': 'Dart/3.8 (dart:io)',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'x-appid': 'appidloliloli',
        'content-type': 'application/json'
    }, 'http://101.36.123.52'

    def homeContent(self, filter):
        return {'class': [{'type_id':20,'type_name':'番剧'},{'type_id':31,'type_name':'美漫'},{'type_id':32,'type_name':'国漫'}]}

    def homeVideoContent(self):
        response = self.fetch(f'{self.host}/api/v1/ranking?type=hot_play&limit=30', headers=self.headers, verify=False).json()
        data = self.decrypt(response['data'],response['timestamp'])
        videos = json.loads(data)['data']['list']
        for i in videos:
            if 'vod_blurb' in i: i['vod_content'] = i['vod_blurb']
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        response = self.fetch(f'{self.host}/api/v1/filter?page={pg}&page_size=18&type_id={tid}&type_id_1=all', headers=self.headers, verify=False).json()
        data = json.loads(self.decrypt(response['data'],response['timestamp']))['data']
        videos = data['list']
        for i in videos:
            if 'vod_blurb' in i: i['vod_content'] = i['vod_blurb']
        return {'list': videos, 'pagecount': data['pagecount'], 'page': pg}

    def searchContent(self, key, quick, pg='1'):
        response = self.fetch(f'{self.host}/api/v1/search?keyword={key}&page={pg}&page_size=20&fields=vod_id,vod_name,vod_pic,type_id,vod_blurb,vod_remarks,vod_lang,vod_year,vod_score,vod_total', headers=self.headers, verify=False).json()
        data = json.loads(self.decrypt(response['data'],response['timestamp']))['data']
        for i in data['list']:
            if 'vod_blurb' in i: i['vod_content'] = i['vod_blurb']
        return {'list': data['list'], 'pagecount': data['pagecount'], 'page': pg}

    def detailContent(self, ids):
        response = self.fetch(f'{self.host}/api/v1/video?vodid={ids[0]}', headers=self.headers, verify=False).json()
        data = json.loads(self.decrypt(response['data'],response['timestamp']))['data']
        return {'list': data['list']}

    def playerContent(self, flag, url, vipflags):
        jx = 0
        if re.search(r'(?:www\.iqiyi|v\.qq|v\.youku|www\.mgtv|www\.bilibili)\.com', url):
            jx = 1
        return {'jx': jx, 'parse': '0', 'url': url, 'header': {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}}

    def decrypt(self, ciphertext_b64, timestamp):
        iv = hashlib.sha256(str(timestamp)[:10].encode('utf-8')).digest()[:16]
        decoded_ciphertext = base64.b64decode(ciphertext_b64.encode('utf-8'))
        aes_cipher = AES.new(b'defaultkey123456', AES.MODE_CBC, iv)
        decrypted_with_zero_iv = aes_cipher.decrypt(decoded_ciphertext)
        unpadded_plaintext = unpad(decrypted_with_zero_iv, AES.block_size)
        return unpadded_plaintext.decode('utf-8')

    def init(self, extend=''):
        pass

    def getName(self):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    def localProxy(self, param):
        pass