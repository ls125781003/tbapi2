# -*- coding: utf-8 -*-
# 本资源来源于互联网公开渠道，仅可用于个人学习爬虫技术。
# 严禁将其用于任何商业用途，下载后请于 24 小时内删除，搜索结果均来自源站，本人不承担任何责任。

from Crypto.Cipher import AES
from base.spider import Spider
from Crypto.Util.Padding import unpad
import re,sys,time,json,base64,hashlib,urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append('..')

class Spider(Spider):
    headers,player,host,name,data_key,data_iv,cms_host,jx_api = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.105 MUOUAPP/10.8.4506.400',
        'Accept-Encoding': 'gzip',
        'brand-model': 'xiaomi',
        'app-device': 'nodata',
        'app-time': '',
        'sys-version': '12',
        'device': '811397239bddf2e7',
        'os': 'Android',
        'app-version': ''
    },{},'', '', '', '', '', ''

    def init(self, extend=''):
        try:
            try:
                config = json.loads(extend)
            except (json.JSONDecodeError, TypeError):
                config = {}
            name = config.get('name', 'muou')
            self.headers['app-version'] = config.get('version', '4.2.0')
            self.host = config['host']
            if not re.match(r'^https?:\/\/[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(:\d+)?(\/)?$', self.host):
                self.host = self.fetch(self.host, headers=self.headers, timeout=10, verify=False).text.rstrip('/')
            timestamp = int(time.time())
            self.headers['app-time'] = str(timestamp)
            api = config.get('api', '/app_info.php')
            salt = ''
            if api.endswith('app_info.php'): salt = 'muouapp'
            inner_sha1 = hashlib.sha1(f"{timestamp}{name}".encode('utf-8')).hexdigest()
            outer_sha1 = hashlib.sha1(f"{timestamp}{inner_sha1}{salt}".encode('utf-8')).hexdigest()
            payload = {'t': timestamp, 'n': inner_sha1, 'm': outer_sha1}
            res = self.post(f'{self.host}{api}', data=payload, headers=self.headers, verify=False).json()
            data = res['data']
            a,e,s = res.get('a'),res.get('e'),res.get('s')
            if a and e and s:
                data = self.t(data, s, e)
            else:
                a = str(res['time'])
            key = hashlib.md5(a.encode('utf-8')).hexdigest()[:16]
            iv = hashlib.md5(outer_sha1.encode('utf-8')).hexdigest()[:16]
            dat3 = json.loads(self.decrypt(data, key, iv))
            self.data_key = hashlib.md5(dat3['key'].encode('utf-8')).hexdigest()[:16]
            self.data_iv = hashlib.md5(dat3['iv'].encode('utf-8')).hexdigest()[:16]
            self.cms_host = dat3['HBqq'].rstrip('/')
            jx_api = dat3.get('HBrjjg', '')
            if jx_api.startswith('http'):
                self.jx_api = jx_api
        except Exception:
            self.cms_host = ''

    def homeContent(self, filter):
        if not self.cms_host:
            return {'list': []}
        self.headers['app-time'] = str(int(time.time()))
        try:
            response = self.fetch(f'{self.cms_host}/api.php/v1.vod/types', headers=self.headers, verify=False).text
        except Exception as e:
            return {"class": [], "filters": {}}
        try:
            data = json.loads(response) or {}
        except json.JSONDecodeError:
            try:
                data = json.loads(self.decrypt(response))
            except (json.JSONDecodeError, TypeError):
                return {"class": [], "filters": {}}
        filter_keys = {"class", "area", "lang", "year", "letter", "by", "sort"}
        filters, classes = {}, []
        typelist = data.get('data', {}).get('typelist', [])
        for item in typelist:
            type_id = str(item["type_id"])
            classes.append({"type_name": item["type_name"], "type_id": type_id})
            extend = item.get("type_extend", {})
            type_filters = []
            for key, value_str in extend.items():
                if key not in filter_keys: continue
                stripped = value_str.strip()
                if not stripped: continue
                values = [v.strip() for v in stripped.split(",") if v.strip()]
                if not values: continue
                type_filters.append({"key": key, "name": key, "value": [{"n": v, "v": v} for v in values] })
            if type_filters:
                filters[type_id] = type_filters
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        if not self.cms_host:
            return {'list': []}
        self.headers['app-time'] = str(int(time.time()))
        response = self.fetch(f'{self.cms_host}/api.php/v1.vod/HomeIndex?page=&limit=6', headers=self.headers, verify=False).text
        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            data_ = self.decrypt(response)
            data = json.loads(data_)
        videos = []
        for i in data['data']:
            if i.get('vod_list'):
                vod_list = i['vod_list']
                for j in vod_list:
                    pic = j.get('vod_pic')
                    if pic:
                        if not pic.startswith('http'):
                            j['vod_pic'] = self.cms_host + pic
                videos.extend(vod_list)
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        if not self.cms_host:
            return {'list': []}
        self.headers['app-time'] = str(int(time.time()))
        response = self.fetch(f"{self.cms_host}/api.php/v1.vod?type={tid}&class={extend.get('class', '')}&area={extend.get('area', '')}&year={extend.get('year', '')}&by=time&page={pg}&limit=18", headers=self.headers, verify=False).text
        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            data_ = self.decrypt(response)
            data = json.loads(data_)
        videos = data['data']['list']
        for item in data['data']['list']:
            pic = item.get('vod_pic', '')
            if pic:
                if not pic.startswith('http'):
                    item['vod_pic'] = self.cms_host + pic
            item.pop('type', None)
        return {'list': videos, 'page': pg}

    def searchContent(self, key, quick, pg="1"):
        if not self.cms_host:
            return {'list': []}
        self.headers['app-time'] = str(int(time.time()))
        response = self.fetch(f'{self.cms_host}/api.php/v1.vod?wd={key}&limit=18&page={pg}', headers=self.headers, verify=False).text
        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            data_ = self.decrypt(response)
            data = json.loads(data_)
        videos = data['data']['list']
        for item in data['data']['list']:
            item.pop('type', None)
        return {'list': videos, 'page': pg}

    def detailContent(self, ids):
        self.headers['app-time'] = str(int(time.time()))
        response = self.fetch(f'{self.cms_host}/api.php/v1.vod/detail?vod_id={ids[0]}', headers=self.headers, verify=False).text
        try:
            data = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            data_ = self.decrypt(response)
            data = json.loads(data_)
        data = data['data']
        if data == '':
            return {'list': []}
        show, vod_play_url = [], []
        for i, j in data['vod_play_list'].items():
            show.append(j['player_info']['show'])
            urls = j.get('urls', {})
            play_url = []
            if isinstance(urls, dict):
                for i2, j2 in urls.items():
                    play_url.append(f"{j2['name']}${j2['from']}@{j2['url']}")
                vod_play_url.append('#'.join(play_url))
        data['vod_play_from'] = '$$$'.join(show)
        data['vod_play_url'] = '$$$'.join(vod_play_url)
        data.pop('vod_play_list')
        data.pop('type')
        return {'list': [data]}

    def playerContent(self, flag, vid, vip_flags):
        play_from, raw_url = vid.split('@')
        jx,url,playurl,play_headers = 1,raw_url,'',{'User-Agent': self.headers['User-Agent']}
        try:
            if not self.player:
                res = self.fetch(f'{self.host}/api.php?action=playerinfo',headers=self.headers, verify=False).text
                data = self.decrypt(res)
                self.player = json.loads(data).get('data',{})
            playerinfo = self.player.get('playerinfo', [])
            for i in playerinfo:
                play_jx = i.get('playerjiekou','')
                if i.get('playername') == play_from and play_jx.startswith('http'):
                    response = self.fetch(f'{play_jx}{raw_url}&playerkey={play_from}',headers=self.headers,verify=False).text
                    try:
                        data = json.loads(response)
                    except (json.JSONDecodeError, TypeError):
                        data_ = self.decrypt(response)
                        data = json.loads(data_)
                    if str(data.get('code','')) == '403':
                        playurl = ''
                    else:
                        playurl = data['url']
                        jx = 0
                playeruas = self.player.get('playerua', [])
                for j in playeruas:
                    try:
                        if j['player'] == play_from and re.search(j['matching'], playurl):
                            play_headers.update(self.playerua_to_dict(j['playerua']))
                            break
                    except Exception:
                        continue
        except Exception:
            playurl = ''

        if playurl.startswith('http'):
            url = playurl
        else:
            if re.search(r'^https?[^\s]*\.(m3u8|mp4|flv)', raw_url, re.I):
                url = raw_url
                jx = 0
            else:
                try:
                    response = self.fetch(self.jx_api + raw_url,headers=self.headers,verify=False).text
                    try:
                        data = json.loads(response)
                    except (json.JSONDecodeError, TypeError):
                        data_ = self.decrypt(response)
                        data = json.loads(data_)
                    playurl = data.get('url','')
                    if playurl.startswith('http'):
                        jx,url = 0,playurl
                    else:
                        jx,url = 1,raw_url
                except Exception as e:
                    jx,url = 1,raw_url
        if url.startswith('NBY-'):
            jx.url = 0,''
        return {'jx': jx,'parse': 0, 'url': url,'header': play_headers}

    def playerua_to_dict(self, playerua_str):
        headers = {}
        lines = playerua_str.replace("\r\n", "\n").split("\n")
        for line in lines:
            if not line.strip():
                continue
            if ':' in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                headers[key] = value
        return headers

    def decrypt(self,data, key='', iv=''):
        if not(key or iv):
            key = self.data_key
            iv = self.data_iv
        key_bytes = key.encode('utf-8')
        iv_bytes = iv.encode('utf-8')
        encrypted_data = base64.b64decode(data)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        decrypted_padded = cipher.decrypt(encrypted_data)
        decrypted = unpad(decrypted_padded, AES.block_size)
        return decrypted.decode('utf-8')

    def t(self, s, v, v1):
        if s is not None and s != '':
            n = len(s)
            if v < 0 or v1 < 0:
                raise ValueError("参数不能为负数")
            if v + v1 <= n:
                return s[v:n - v1]
            else:
                return ''
        return s

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