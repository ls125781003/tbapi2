# -*- coding: utf-8 -*-
# 本资源来源于互联网公开渠道，仅可用于个人学习爬虫技术。
# 严禁将其用于任何商业用途，下载后请于 24 小时内删除，搜索结果均来自源站，本人不承担任何责任。

from Crypto.Cipher import AES
from base.spider import Spider
from Crypto.Util.Padding import unpad,pad
from Crypto.Random import get_random_bytes
import re,os,sys,uuid,time,json,zlib,base64,urllib3,hashlib
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append('..')

class Spider(Spider):
    def_headers2,config,host,token,req_uuid = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6299.95 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json',
        'uuid': '',
        'client_type': 'android',
        'timestamp': '',
        'sign': '',
        'version': '',
        'appkey': '',
        'api_version': 'v1'
    },{},'','',str(uuid.uuid4())

    def init(self, extend=''):
        try:
            ext = json.loads(extend)
            host = ext['host']
            app_key = ext['appkey']
            app_name = ext['name']
            build_signature = ext['buildSignature']
            build_number = ext['buildNumber']
            version_name = ext['versionName']
            package = ext['package']
            login_path = ext.get('LoginPath', '/app/userInfo')
            self.token = ext.get('token')
            if not (host and app_key and app_key and app_name and build_signature and build_number and version_name and package): return
            self.host = f"{host}/api"
            self.def_headers2['appkey'] = app_key
            self.def_headers2['version'] = ext['version']
            nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
            payload = self.encrypt(f'{{"v":"{version_name}","n":"{app_name}","s":"{build_signature}","pl":"1","apiVersion":"v2","token":"","timestamp":"{timestamp}","nonce":"{nonce}"}}')
            response = self.post(f'{self.host}/app/systemInit',data=payload, headers=self.headers2(nonce,timestamp,payload), verify=False, timeout=30).text
            data = json.loads(self.decrypt(response, self.req_uuid))
            self.config['player'] = data['player']
            self.config['parses'] = data['parser_api']
            self.config['categories'] = data['categorys']['data']
            if not self.token:
                device_info_cache_key = f'99app_device_info_{app_key}_mPjOv6fHcE'
                device_info = self.getCache(device_info_cache_key)
                if not device_info:
                    device_info = {'did': str(uuid.uuid4()), 'install_time': int(time.time() * 1000)}
                    self.setCache(device_info_cache_key,device_info)
                install_time,did = device_info['install_time'],device_info['did']
                update_time = install_time
                nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
                self.encrypt(f'{{"os":"android","name":"xiaomi","version":"15","sdkInt":32,"device":"xiaomi","brand":"xiaomi","manufacturer":"xiaomi","product":"b0q","hardware":"xiaomi","isPhysicalDevice":true,"androidId":"V417IR","bootloader":"unknown","display":"V417IR release-keys","host":"a11-gz01-test","tags":"release-keys","type":"user","finger":"xiaomi/b0q/b0q:15/V619IR/613:user/release-keys","app":{{"version":"{version_name}","name":"{app_name}","package":"{package}","buildNumber":"{build_number}","buildSignature":"{build_signature}","install":{install_time},"update":{update_time}}},"did":"{did}","apiVersion":"v2","channel":"","token":"","timestamp":"{timestamp}","nonce":"{nonce}"}}')
                response2 = self.post(f'{self.host}{login_path}', data=payload, headers=self.headers2(nonce,timestamp,payload), verify=False).text
                device_data = json.loads(self.decrypt(response2, self.req_uuid))
                try:
                    self.token = device_data['userInfo']['user_token']
                except Exception:
                    self.token = uuid.uuid4().hex
        except Exception:
            self.host = ''

    def homeContent(self, filter):
        if not self.host: return None
        classes = []
        for i in self.config['categories']:
            if isinstance(i,dict):
                classes.append({'type_id': i['id'], 'type_name': i['name']})
        return {'class': classes}

    def homeVideoContent(self):
        if not self.host: return None
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload = self.encrypt(f'{{"kw":"","page":"1","limit":21,"pid":"1","orderBy":"time","isCategory":1,"token":"","timestamp":"{timestamp}","nonce":"{nonce}"}}')
        response = self.post(f'{self.host}/vod/search', data=payload, headers=self.headers2(nonce,timestamp,payload), verify=False).text
        data = json.loads(self.decrypt(response,self.req_uuid))
        videos = self.arr2vods(data['data'])
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload = self.encrypt(f'{{"kw":"","page":"{pg}","limit":21,"pid":"{tid}","orderBy":"time","isCategory":1,"token":"{self.token}","timestamp":"{timestamp}","nonce":"{nonce}"}}')
        response = self.post(f'{self.host}/vod/search', data=payload, headers=self.headers2(nonce,timestamp,payload), verify=False).text
        data = json.loads(self.decrypt(response))
        videos = self.arr2vods(data['data'])
        return {'list': videos, 'pagecount': data['page_count'], 'page': pg}

    def searchContent(self, key, quick, pg='1'):
        if not self.host: return None
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload = self.encrypt(f'{{"kw":"{key}","page":{int(pg)},"limit":21,"orderBy":"vod_hits_month","sort":"desc","token":"{self.token}","timestamp":"{timestamp}","nonce":"{nonce}"}}')
        response = self.post(f'{self.host}/vod/search', data=payload, headers=self.headers2(nonce,timestamp,payload),verify=False).text
        data = json.loads(self.decrypt(response, self.req_uuid))
        videos = self.arr2vods(data['data'])
        return {'list': videos, 'pagecount': data['page_count'], 'page': pg}

    def detailContent(self, ids):
        if not self.host: return None
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload = self.encrypt(f'{{"id":"{ids[0]}","eps":"1","v":"2.0.0","pl":1,"token":"{self.token}","timestamp":"{timestamp}","nonce":"{nonce}"}}')
        response = self.post(f'{self.host}/vod/detail', data=payload, headers=self.headers2(nonce,timestamp,payload), verify=False).text
        data = json.loads(self.decrypt(response))
        data = data['data']
        players = self.config['player']
        resources = dict(zip(data['play_from'].split('$$$'), data['play_url'].split('$$$')))
        player_sequence = sorted(players.keys(), key=lambda k: players[k]['sort'], reverse=True)
        show2 = []
        play_urls2 = []
        for key in player_sequence:
            if key in resources:
                player = players[key]
                if player['name'] != key:
                    show2.append(f"{player['name']}\u2005({key})")
                else:
                    show2.append(key)
                urls = resources[key].split('#')
                urls2 = [f"{parts[0]}${key}@{parts[1]}" for url_part in urls if '$' in url_part and len(parts := url_part.split('$', 1)) > 1]
                play_urls2.append('#'.join(urls2))
        video = {
            'vod_id': data['id'],
            'vod_name': data['name'],
            'vod_pic': data['pic'],
            'vod_remarks': data['remarks'],
            'vod_year': data['year'],
            'vod_area': data['area'],
            'vod_actor': data['actor'],
            'vod_director': data['director'],
            'vod_content': data['content'],
            'vod_play_from': '$$$'.join(show2),
            'vod_play_url': '$$$'.join(play_urls2),
            'type_name': data['class']
        }
        return {'list': [video]}

    def playerContent(self, flag, vid, vip_flags):
        jx,sniff,url,play_headers = 0,0,'',{'User-Agent':'Lavf/58.12.100'}
        webview_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'upgrade-insecure-requests': '1',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        play_from, raw_url = vid.split('@')
        try:
            player = self.config['player'][play_from]
            try:
                server_play_headers = json.loads(player['headers'])
                if isinstance(server_play_headers, dict):
                    play_headers.update(server_play_headers)
            except Exception:
                pass
            if player['type'] == 0:
                url = raw_url
            elif player['type'] == 1:
                if player['isParse'] == 1:
                    try:
                        parse_rule = player['parseUrl'].split(',')
                    except Exception:
                        parse_rule = []
                    webview_parses = []
                    for i in self.config['parses']:
                        try:
                            if parse_rule and not str(i['id']) in parse_rule:
                                continue
                            elif not(i['api_supports_code']) or i['api_supports_code'] and play_from in i['api_supports_code'].split(','):
                                if i['api_type'] == 'webview':
                                    if i['api_url']:
                                        webview_parses.append(i)
                                    continue
                                elif i['api_type'] == 'json' and i['is_server_parser'] == 1:
                                    parse_id = i['id']
                                    nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
                                    payload = self.encrypt(f'{{"id":{parse_id},"url":"{raw_url}","token":"{self.token}","timestamp":"{timestamp}","nonce":"{nonce}"}}')
                                    response = self.post(f'{self.host}/app/vodParser', data=payload, headers=self.headers2(nonce,timestamp,payload),verify=False).text
                                    data = json.loads(self.decrypt(response, self.req_uuid))
                                    play_url = data['data']
                                else:
                                    jx_headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6299.95 Safari/537.36'}
                                    response = self.fetch(f"{i['api_url']}{raw_url}", headers=jx_headers, verify=False).json()
                                    play_url = response[i['idx_play_url']]
                                if play_url.startswith('http'):
                                    url = play_url
                                    break
                        except Exception:
                            continue
                    if not url:
                        for k in webview_parses:
                            try:
                                if parse_rule and not str(k['id']) in parse_rule:
                                    continue
                                else:
                                    if k['api_url'] and k['api_url'].startswith('http'):
                                        return { 'jx': 0, 'parse': 1, 'url': f"{k['api_url']}{url}", 'header': play_headers}
                            except Exception:
                                continue
            elif player['type'] == 2:
                url, sniff = raw_url, 1
                play_headers = webview_headers
        except Exception:
            pass
        if not url:
            url = vid
            if re.search(r'(?:www\.iqiyi|v\.qq|v\.youku|www\.mgtv|www\.bilibili)\.com', url):
                jx = 1
        return { 'jx': jx, 'parse': sniff, 'url': url, 'header': play_headers}

    def decrypt(self, data, key=''):
        try:
            if not key: key = self.req_uuid
            encrypted_bytes = base64.b64decode(data)
            if len(encrypted_bytes) < 16: raise ValueError
            cipher = AES.new(key.replace('-', '').encode('utf-8'), AES.MODE_CBC, encrypted_bytes[:16])
            decrypted_padded = cipher.decrypt(encrypted_bytes[16:])
            decrypted_raw = unpad(decrypted_padded, AES.block_size)
            deflated_data = zlib.decompress(decrypted_raw)
            return deflated_data.decode('utf-8')
        except zlib.error:
            raise ValueError
        except Exception:
            raise ValueError

    def encrypt(self, data, key=''):
        try:
            if not key: key = self.req_uuid
            data_bytes = data.encode('utf-8')
            padded_data = pad(data_bytes, AES.block_size)
            iv = get_random_bytes(AES.block_size)
            key_bytes = key.replace('-', '').encode('utf-8')
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            encrypted_bytes = cipher.encrypt(padded_data)
            return base64.b64encode(iv + encrypted_bytes).decode('utf-8')
        except Exception:
            raise ValueError

    def arr2vods(self, arr):
        videos = []
        for i in arr:
            videos.append({
                'vod_id': i['id'],
                'vod_name': i['name'],
                'vod_pic': i['pic'],
                'vod_remarks': i['remarks'],
                'vod_year': i['year'],
                'vod_content': i.get('blurb'),
                'type_name': i.get('class'),
                'vod_area': i.get('area'),
                'vod_actor': i.get('actor'),
                'vod_director': i.get('director')
            })
        return videos

    def headers2(self,nonce, timestamp, payload=''):
        return {
            **self.def_headers2,
            'uuid': self.req_uuid,
            'timestamp': timestamp,
            'sign': self.sign(payload, timestamp, self.req_uuid,nonce, self.def_headers2['appkey']),
            'nonce': nonce
        }

    def sign(self, body, timestamp, nonce, req_uuid, app_key):
        combined = f'{body}:{timestamp}:{nonce}:{req_uuid}:{app_key}'
        sha256_hash = hashlib.sha256(combined.encode('utf-8'))
        return sha256_hash.hexdigest()

    def nonce(self):
        return base64.b64encode(os.urandom(16)).decode('utf-8')

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