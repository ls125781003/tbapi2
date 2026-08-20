# -*- coding: utf-8 -*-
# 本资源来源于互联网公开渠道，仅可用于个人学习爬虫技术。
# 严禁将其用于任何商业用途，下载后请于 24 小时内删除，搜索结果均来自源站，本人不承担任何责任。

import re,sys,json,urllib3
from base.spider import Spider
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append('..')

class Spider(Spider):
    headers,host,parse = {
        'User-Agent': "Dart/3.9 (dart:io)",
        'Accept': "application/json",
        'Accept-Encoding': "gzip",
        'x-api-key': "ETMy41jT5qtCFc61Le8rUpTk2MzWGyIP",
        'x-requested-with': "XMLHttpRequest",
        'content-type': "application/json"
    },'',{}

    def init(self, extend=''):
        ext = json.loads(extend)
        self.host = ext.get('host','https://app.247kan.com')
        x_api_key = ext.get('xapikey')
        if x_api_key: self.headers['x_api_key'] = x_api_key
        self.parse = ext.get('parse',{})

    def homeContent(self, filter):
        if not self.host: return None
        return {'class': [{'type_id': 1, 'type_name': '电影'}, {'type_id': 2, 'type_name': '连续剧'}, {'type_id': 3, 'type_name': '综艺'}, {'type_id': 4, 'type_name': '动漫'}, {'type_id': 5, 'type_name': '短剧'}, {'type_id': 6, 'type_name': '纪录片'}]}

    def homeVideoContent(self):
        if not self.host: return None
        response = self.fetch(f'{self.host}/api/home?featured_category_ids=14', headers=self.headers, verify=False).json()
        videos = []
        for i in response['data'].values():
            videos.extend(i)
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        if not self.host: return None
        response = self.fetch(f'{self.host}/api/categories/{tid}/videos?page={pg}&limit=21&sort=year&area=&language=&year=&actor=&director=&letter=&tag=&genre=&trending=false&top250=false&highscore=false', headers=self.headers, verify=False).json()
        return {'list': response['data']['videos'], 'page': pg}

    def searchContent(self, key, quick, pg='1'):
        if not self.host: return None
        response = self.fetch(f'{self.host}/api/videos/search?q={key}&page={pg}&limit=20', headers=self.headers, verify=False).json()
        data = response['data']
        return {'list': data['videos'], 'pagecount': data['total_pages'], 'page': pg}

    def detailContent(self, ids):
        if not self.host: return None
        response = self.fetch(f'{self.host}/api/videos/{ids[0]}', headers=self.headers, verify=False).json()
        data = response['data']
        video = {
            'vod_id': data['vod_id'],
            'vod_name': data['vod_name'],
            'vod_pic': data['vod_pic'],
            'vod_remarks': data['vod_remarks'],
            'vod_year': data['vod_year'],
            'vod_area': data['vod_area'],
            'vod_actor': ','.join(data['vod_actor']),
            'vod_director': ','.join(data['vod_director']),
            'vod_content': data['vod_content'],
            'vod_play_from': data['vod_play_from'],
            'vod_play_url': data['vod_play_url'],
            'type_name': ','.join(data['vod_class'])
        }
        return {'list': [video]}

    def playerContent(self, flag, id, vipflags):
        jx, url = 0, ''
        parse = self.parse
        if parse:
            for i, j in parse.items():
                if flag in i:
                    for k in j:
                        try:
                            response = self.fetch(f'{k}{id}', headers=self.headers, verify=False).json()
                            play_url = response['url']
                            if play_url.startswith('http'):
                                url, jx = play_url, 0
                                break
                        except (KeyError, ValueError, Exception):
                            continue
                    if url.startswith('http'):
                        break
        if not url:
            if re.match(r'https?:\/\/.*\.(m3u8|mp4|flv)', id):
                jx, url = 0, id
            else:
                jx, url = 1, id
        if url.startswith('NBY'):
            jx, url = 0, ''
        return {'jx': jx, 'parse': '0', 'url': url, 'header': {'User-Agent':'Mozilla/5.0 (Linux; Android 10; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36','Connection':'Keep-Alive','Accept-Encoding':'gzip'}}

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
