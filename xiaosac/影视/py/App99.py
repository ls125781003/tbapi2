# -*- coding: utf-8 -*-
from Crypto.Cipher import AES
from base.spider import Spider
from Crypto.Util.Padding import unpad, pad
from Crypto.Random import get_random_bytes
import re, os, sys, uuid, time, json, zlib, base64, urllib3, hashlib
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
sys.path.append('..')

class Spider(Spider):
    
    # 规范化类属性定义，避免单行过长和作用域混乱
    def_headers2 = {
        'User-Agent': '',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/json',
        'uuid': '',
        'client_type': 'android',
        'timestamp': '',
        'sign': '',
        'nonce': '',
        'version': '',
        'appkey': '',
        'api_version': 'v1'
    }
    config = {}
    host = ''
    token = ''
    req_uuid = str(uuid.uuid4())
    ua = ''
    enable_referer = 0
    api_prefix = ''
    parse_config = {}
    
    # ========== 新增：NSYS/YYNB解析相关配置 ==========
    nsys_host = ''
    nsys_port = ''
    nsys_handshake_key = ''
    nsys_enabled = False
    nsys_api_type = 'v2'  # 默认v2接口
    app_version = ''  # 保存App版本号，供detail等接口使用

    def init(self, extend=''):
        try:
            if not extend:
                return
            
            ext = json.loads(extend) if isinstance(extend, str) else extend
            
            host = ext.get('host', '')
            app_key = ext.get('appkey', '')
            app_name = ext.get('name', '')
            build_signature = ext.get('buildSignature', '')
            build_number = ext.get('buildNumber', '')
            version_name = ext.get('versionName', '')
            package = ext.get('package', '')
            
            self.ua = ext.get('ua', 'Mozilla/5.0 (Linux; Android 13; PGP110 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.196 Mobile Safari/537.36')
            self.def_headers2['User-Agent'] = self.ua
            
            self.enable_referer = int(ext.get('referer', 0))
            self.api_prefix = ext.get('api_prefix', '').strip()
            
            if self.api_prefix:
                prefix = self.api_prefix.strip('/')
                if prefix:
                    self.host = f"{host.rstrip('/')}/{prefix}"
                else:
                    self.host = host.rstrip('/')
            else:
                parsed = urlparse(host)
                if parsed.path and parsed.path != '/' and parsed.path != '':
                    self.host = host.rstrip('/')
                else:
                    self.host = f"{host.rstrip('/')}/api"
            
            self.parse_config = ext.get('parse', {})
            login_path = ext.get('LoginPath', '/app/userInfo')
            
            if not login_path.startswith('/'):
                login_path = '/' + login_path
            
            # ========== 新增：NSYS/YYNB解析配置初始化 ==========
            nsys_config = ext.get('nsys', {})
            if nsys_config:
                self.nsys_enabled = True
                self.nsys_host = nsys_config.get('host', '')
                self.nsys_port = str(nsys_config.get('port', '3737'))
                self.nsys_handshake_key = nsys_config.get('handshake_key', '')
                self.nsys_api_type = nsys_config.get('api_type', 'v2')
            
            if not (host and app_key and app_name and build_signature and build_number and version_name and package):
                self.host = ''
                return
            
            self.def_headers2['appkey'] = app_key
            self.def_headers2['version'] = ext.get('version', version_name)
            self.app_version = self.def_headers2['version']
            self.req_uuid = ext.get('uuid') or str(uuid.uuid4())
            self.def_headers2['api_version'] = ext.get('api_version', 'v1')
            
            nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
            init_data = f'{{"v":"{version_name}","n":"{app_name}","s":"{build_signature}","pl":"1","apiVersion":"v2","token":"","timestamp":"{timestamp}","nonce":"{nonce}"}}'
            
            payload = self.encrypt(init_data)
            headers = self.headers2(nonce, timestamp, payload)
            
            system_init_url = f'{self.host}/app/systemInit'
            response = self.post(system_init_url, data=payload, headers=headers, verify=False, timeout=30)
            
            if response.status_code != 200:
                self.host = ''
                return
            
            try:
                decrypted_data = self.decrypt(response.text, self.req_uuid)
                data = json.loads(decrypted_data)
                
                if 'player' in data:
                    self.config['player'] = data['player']
                if 'parser_api' in data:
                    self.config['parses'] = data['parser_api']
                if 'categorys' in data and 'data' in data['categorys']:
                    self.config['categories'] = data['categorys']['data']
                    
            except Exception:
                self.host = ''
                return
            
            if not self.token:
                device_info_cache_key = f'99app_device_info_{app_key}_mPjOv6fHcE'
                device_info = self.getCache(device_info_cache_key)
                
                if not device_info:
                    device_info = {
                        'did': str(uuid.uuid4()), 
                        'install_time': int(time.time() * 1000)
                    }
                    self.setCache(device_info_cache_key, device_info)
                
                install_time = device_info.get('install_time', int(time.time() * 1000))
                did = device_info.get('did', str(uuid.uuid4()))
                update_time = install_time
                
                nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
                
                login_data = f'{{"os":"android","name":"xiaomi","version":"15","sdkInt":32,"device":"xiaomi","brand":"xiaomi","manufacturer":"xiaomi","product":"b0q","hardware":"xiaomi","isPhysicalDevice":true,"androidId":"V417IR","bootloader":"unknown","display":"V417IR release-keys","host":"a11-gz01-test","tags":"release-keys","type":"user","finger":"xiaomi/b0q/b0q:15/V619IR/613:user/release-keys","app":{{"version":"{version_name}","name":"{app_name}","package":"{package}","buildNumber":"{build_number}","buildSignature":"{build_signature}","install":{install_time},"update":{update_time}}},"did":"{did}","apiVersion":"v2","channel":"","token":"","timestamp":"{timestamp}","nonce":"{nonce}"}}'
                
                payload = self.encrypt(login_data)
                headers = self.headers2(nonce, timestamp, payload)
                login_url = f"{host.rstrip('/')}{login_path}"
                    
                response2 = self.post(login_url, data=payload, headers=headers, verify=False).text
                
                try:
                    device_data = json.loads(self.decrypt(response2, self.req_uuid))
                    if 'userInfo' in device_data and 'user_token' in device_data['userInfo']:
                        self.token = device_data['userInfo']['user_token']
                except Exception:
                    pass
            
        except Exception:
            self.host = ''

    def homeContent(self, filter):
        if not self.host: 
            return None        
        classes = []
        filters = {}
        if 'categories' in self.config:
            for i in self.config['categories']:
                if isinstance(i, dict):
                    classes.append({'type_id': i['id'], 'type_name': i['name']})
                    
                    type_id = i['id']
                    type_extend = i['type_extend']
                    if not type_extend:
                      continue
                      
                    try:
                        ext = json.loads(type_extend)
                    except Exception:
                        continue
                        
                    # ----- 所有可能出现的筛选字段 -----
                    # 字段键 -> 展示名称
                    filter_fields = [
                        ('class',    '类型'),
                        ('area',     '地区'),
                        ('year',     '年份'),
                        ('lang',     '语言')
                    ]
                    
                    f_list = []
                    for field_key, field_name in filter_fields:
                        raw_value = ext.get(field_key, '')
                        if not raw_value or not raw_value.strip():
                            continue          # 字段不存在或为空（如动漫无演员）则跳过

                        # 构造 “全部 + 具体选项” 数组
                        values = [{'n': '全部', 'v': ''}]
                        for v in raw_value.split(','):
                            v = v.strip()
                            if v:
                                values.append({'n': v, 'v': v})

                        f_list.append({
                            'key': field_key,
                            'name': field_name,
                            'value': values
                        })   
                        
                    filters[type_id] = f_list
        return {'class': classes,'filters': filters}

    def homeVideoContent(self):
        if not self.host: 
            return None
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload_data = f'{{"kw":"","page":"1","limit":21,"pid":"1","orderBy":"time","isCategory":1,"token":"","timestamp":"{timestamp}","nonce":"{nonce}"}}'
        payload = self.encrypt(payload_data)
        try:
            response = self.post(f'{self.host}/vod/search', data=payload, headers=self.headers2(nonce, timestamp, payload), verify=False).text
            data = json.loads(self.decrypt(response, self.req_uuid))
            if 'data' in data:
                videos = self.arr2vods(data['data'])
                return {'list': videos}
            return {'list': []}
        except Exception:
            return {'list': []}

    def categoryContent(self, tid, pg, filter, extend):
        if not self.host:
            return {'list': [], 'pagecount': 1, 'page': pg}
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        # 基础参数
        payload_data = {
            "kw": "",
            "page": str(pg),
            "limit": "21",
            "pid": tid,
            "orderBy": "time",
            "isCategory": 1,
            "token": self.token,
            "timestamp": timestamp,
            "nonce": nonce
        }

        # 整合 extend 筛选条件，仅添加非空值
        if filter and extend:
            # 字段映射：extend中的key -> payload中的key
            field_map = {
                "area": "area",
                "year": "year",
                "lang": "lang",
                "class": "class"
            }
            for ext_key, payload_key in field_map.items():
                value = extend.get(ext_key)
                # 只有当值存在且不为空字符串时，才添加到payload
                if value is not None and value != "":
                    payload_data[payload_key] = value

        # 加密 payload
        payload_str = json.dumps(payload_data)
        payload = self.encrypt(payload_str)
        try:
            response = self.post(f'{self.host}/vod/search', data=payload, headers=self.headers2(nonce,timestamp,payload), verify=False).text
            data = json.loads(self.decrypt(response))
            if 'data' in data:
                videos = self.arr2vods(data['data'])
                pagecount = data.get('page_count', 1)
                return {'list': videos, 'pagecount': pagecount, 'page': pg}
            else:
                return {'list': [], 'pagecount': 1, 'page': pg}
        except Exception as e:
            return {'list': [], 'pagecount': 1, 'page': pg}

    def searchContent(self, key, quick, pg='1'):
        if not self.host: 
            return {'list': [], 'pagecount': 1, 'page': pg}
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload_data = f'{{"kw":"{key}","page":{int(pg)},"limit":21,"orderBy":"vod_hits_month","sort":"desc","token":"{self.token}","timestamp":"{timestamp}","nonce":"{nonce}"}}'
        payload = self.encrypt(payload_data)
        try:
            response = self.post(f'{self.host}/vod/search', data=payload, headers=self.headers2(nonce, timestamp, payload), verify=False).text
            data = json.loads(self.decrypt(response, self.req_uuid))
            if 'data' in data:
                videos = self.arr2vods(data['data'])
                pagecount = data.get('page_count', 1)
                return {'list': videos, 'pagecount': pagecount, 'page': pg}
            return {'list': [], 'pagecount': 1, 'page': pg}
        except Exception:
            return {'list': [], 'pagecount': 1, 'page': pg}

    def detailContent(self, ids):
        if not self.host or not ids: 
            return None
        nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
        payload_data = f'{{"id":"{ids[0]}","eps":"1","v":"{self.app_version}","pl":1,"token":"{self.token}","timestamp":"{timestamp}","nonce":"{nonce}"}}'
        payload = self.encrypt(payload_data)
        try:
            response = self.post(f'{self.host}/vod/detail', data=payload, headers=self.headers2(nonce, timestamp, payload), verify=False).text
            response_data = json.loads(self.decrypt(response))
            
            if 'data' in response_data:
                data = response_data['data']
                players = self.config.get('player', {})
                print(players)
                play_from_list = data.get('play_from', '').split('$$$')
                play_url_list = data.get('play_url', '').split('$$$')
                resources = dict(zip(play_from_list, play_url_list))
                
                player_sequence = sorted(
                    players.keys(),
                    key=lambda k: (
                        '4K' in players[k].get('code', ''),  # 包含4K则为True（1），否则False（0）
                        players[k].get('code', '')           # 同组内按code字符串排序
                    ),
                    reverse=True
                )
                show2 = []
                play_urls2 = []
                
                for key in player_sequence:
                    if key in resources:
                        player = players[key]
                        if player.get('name', key) != key:
                            show2.append(f"{player.get('name', key)}\u2005({key})")
                        else:
                            show2.append(key)
                        
                        urls = resources[key].split('#')
                        urls2 = []
                        for url_part in urls:
                            if '$' in url_part:
                                parts = url_part.split('$', 1)
                                if len(parts) > 1:
                                    urls2.append(f"{parts[0]}${key}@{parts[1]}")
                        play_urls2.append('#'.join(urls2))
                
                video = {
                    'vod_id': data.get('id', ''),
                    'vod_name': data.get('name', ''),
                    'vod_pic': data.get('pic', ''),
                    'vod_remarks': data.get('remarks', ''),
                    'vod_year': data.get('year', ''),
                    'vod_area': data.get('area', ''),
                    'vod_actor': data.get('actor', ''),
                    'vod_director': data.get('director', ''),
                    'vod_content': data.get('content', ''),
                    'vod_play_from': '$$$'.join(show2),
                    'vod_play_url': '$$$'.join(play_urls2),
                    'type_name': data.get('class', '')
                }
                return {'list': [video]}
            return {'list': []}
        except Exception:
            return {'list': []}

    def playerContent(self, flag, vid, vip_flags):
        jx, sniff, url, play_headers = 0, 0, '', {'User-Agent': self.ua}
        webview_headers = {
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        try:
            if '@' in vid:
                # 限制分割次数为1，防止真实URL内部带有@符号导致解包错误
                play_from, raw_url = vid.split('@', 1) 
            else:
                return {'jx': 0, 'parse': 0, 'url': vid, 'header': play_headers}
        except Exception:
            return {'jx': 0, 'parse': 0, 'url': vid, 'header': play_headers}
        
        players = self.config.get('player', {})
        parses = self.config.get('parses', [])

        def add_referer(target_url):
            if self.enable_referer == 1:
                try:
                    parsed = urlparse(target_url)
                    if parsed.netloc:
                        play_headers['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
                except Exception:
                    pass

        def try_all_parsers(raw_url_to_parse):
            for parser in parses:
                if parser.get('api_type') == 'json' and parser.get('is_server_parser') == 1:
                    parse_id = parser.get('id')
                    nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
                    payload_data = json.dumps({
                        "id": parse_id,
                        "url": raw_url_to_parse,
                        "token": self.token,
                        "timestamp": timestamp,
                        "nonce": nonce
                    })
                    payload = self.encrypt(payload_data)
                    headers = self.headers2(nonce, timestamp, payload)
                    try:
                        response = self.post(f'{self.host}/app/vodParser', data=payload, headers=headers, verify=False)
                        if response.status_code == 200:
                            decrypted = self.decrypt(response.text, self.req_uuid)
                            data = json.loads(decrypted)
                            if 'data' in data and data['data']:
                                parsed_url = data['data']
                                if isinstance(parsed_url, str) and parsed_url.startswith('http'):
                                    return parsed_url
                    except Exception:
                        continue
            return None

        # ========== 修改：兼容NSYS与YYNB解析逻辑 ==========
        # 如果raw_url是NSYS或YYNB格式，调用解析接口
        if (raw_url.startswith('NSYS-') or raw_url.startswith('YYNB-')) and self.nsys_enabled and self.nsys_host:
            nsys_result = self.nsys_parse(raw_url)
            if nsys_result:
                add_referer(nsys_result)
                return {'jx': 0, 'parse': 0, 'url': nsys_result, 'header': play_headers}

        if re.search(r'(?:mgtv\.com|v\.qq\.com|iqiyi\.com|youku\.com|bilibili\.com|le\.com|sohu\.com|pptv\.com|1905\.com|cntv\.cn|cctv\.com|miguvideo\.com)', raw_url):
            parsed_url = try_all_parsers(raw_url)
            if parsed_url:
                add_referer(parsed_url)
                return {'jx': 0, 'parse': 0, 'url': parsed_url, 'header': play_headers}
            jx = 1
            return {'jx': jx, 'parse': 0, 'url': raw_url, 'header': webview_headers}
        
        if '.m3u8' in raw_url or '.mp4' in raw_url:
            url = raw_url
            add_referer(url)
            if play_from in players:
                try:
                    server_headers = json.loads(players[play_from].get('headers', '{}'))
                    if isinstance(server_headers, dict):
                        play_headers.update(server_headers)
                except Exception:
                    pass
            return {'jx': 0, 'parse': 0, 'url': url, 'header': play_headers}
        
        if play_from in players:
            player = players[play_from]
            player_type = player.get('type', 0)
            
            parse_rule = []
            if player.get('parseUrl'):
                parse_rule = player['parseUrl'].split(',')
            
            if parse_rule and parses:
                for parse_id_str in parse_rule:
                    try:
                        parse_id = int(parse_id_str.strip())
                        for parser in parses:
                            if str(parser.get('id')) == str(parse_id) and parser.get('is_server_parser') == 1:
                                nonce, timestamp = self.nonce(), str(int(time.time() * 1000))
                                payload_data = json.dumps({
                                    "id": parse_id,
                                    "url": raw_url,
                                    "token": self.token,
                                    "timestamp": timestamp,
                                    "nonce": nonce
                                })
                                payload = self.encrypt(payload_data)
                                headers = self.headers2(nonce, timestamp, payload)
                                try:
                                    response = self.post(f'{self.host}/app/vodParser', data=payload, headers=headers, verify=False)
                                    if response.status_code == 200:
                                        decrypted = self.decrypt(response.text, self.req_uuid)
                                        data = json.loads(decrypted)
                                        if 'data' in data and data['data']:
                                            parsed_url = data['data']
                                            if isinstance(parsed_url, str) and parsed_url.startswith('http'):
                                                url = parsed_url
                                                add_referer(url)
                                                return {'jx': 0, 'parse': 0, 'url': url, 'header': play_headers}
                                except Exception:
                                    continue
                    except Exception:
                        continue
            
            if not url:
                parsed_url = try_all_parsers(raw_url)
                if parsed_url:
                    url = parsed_url
                    add_referer(url)
                    return {'jx': 0, 'parse': 0, 'url': url, 'header': play_headers}
            
            if player_type == 2:
                sniff = 1
                play_headers = webview_headers
                return {'jx': 0, 'parse': 1, 'url': raw_url, 'header': play_headers}
        
        if self.parse_config:
            for parse_keys, parse_urls in self.parse_config.items():
                if isinstance(parse_keys, str):
                    play_from_list = [k.strip() for k in parse_keys.split(',')]
                    if play_from in play_from_list:
                        if isinstance(parse_urls, list):
                            for parse_url in parse_urls:
                                try:
                                    full_url = f"{parse_url}{raw_url}"
                                    response = self.fetch(full_url, headers=play_headers, verify=False)
                                    if response and response.status_code == 200:
                                        try:
                                            data = response.json()
                                            play_url = data.get('url') or data.get('play_url') or data.get('data')
                                            if play_url and isinstance(play_url, str) and play_url.startswith('http'):
                                                return {'jx': 0, 'parse': 0, 'url': play_url, 'header': play_headers}
                                        except Exception:
                                            pass
                                except Exception:
                                    continue
                        if url:
                            return {'jx': 0, 'parse': 0, 'url': url, 'header': play_headers}
        
        url = raw_url
        add_referer(url)
        return {'jx': jx, 'parse': sniff, 'url': url, 'header': play_headers}

    # ========== 修改：兼容NSYS与YYNB解析方法 ==========
    def nsys_parse(self, raw_url):
        """
        NSYS/YYNB解析接口适配
        根据抓包数据：
        - 请求: GET http://{host}:{port}?url={加密后的URL}
        - 响应: JSON {"code": 200, "type": "单线程", "msg": "解析成功", "url": "真实m3u8地址"}
        """
        try:
            if not self.nsys_host or not self.nsys_port:
                return None
            
            # 构造解析请求URL
            # 抓包显示格式: http://114.66.41.137:3737?url=NSYS-xxx 或 YYNB-xxx
            nsys_api_url = f"http://{self.nsys_host}:{self.nsys_port}"
            
            # 对原始URL进行格式编码
            encoded_url = self.nsys_encode_url(raw_url)
            
            params = {'url': encoded_url}
            headers = {
                'User-Agent': self.ua,
                'Accept-Encoding': 'gzip'
            }
            
            response = self.fetch(nsys_api_url, params=params, headers=headers, verify=False, timeout=15)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('code') == 200 and data.get('url'):
                        parsed_url = data['url']
                        if isinstance(parsed_url, str) and parsed_url.startswith('http'):
                            return parsed_url
                except Exception:
                    pass
            
            return None
        except Exception:
            return None
    
    def nsys_encode_url(self, raw_url):
        """
        NSYS/YYNB URL编码方法
        根据抓包数据格式: NSYS-xxx 或 YYNB-xxx
        由于编码是App内部加密算法生成，此处无法实现完全相同的编码，
        因此采用透传策略：如果raw_url已经是指定格式则直接透传，否则返回None让上层处理
        """
        try:
            # 如果raw_url已经是支持的格式，直接透传
            if raw_url.startswith('NSYS-') or raw_url.startswith('YYNB-'):
                return raw_url
            # 非支持格式的URL无法编码，返回None
            return None
        except Exception:
            return None

    def decrypt(self, data, key=''):
        try:
            if not key: 
                key = self.req_uuid
            encrypted_bytes = base64.b64decode(data)
            if len(encrypted_bytes) < 16: 
                raise ValueError("数据太短")
            
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            key_bytes = key.replace('-', '').encode('utf-8')
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            decrypted_padded = cipher.decrypt(ciphertext)
            decrypted_raw = unpad(decrypted_padded, AES.block_size)
            
            try:
                deflated_data = zlib.decompress(decrypted_raw)
                return deflated_data.decode('utf-8')
            except zlib.error:
                try:
                    return decrypted_raw.decode('utf-8')
                except Exception:
                    raise ValueError("解密失败")
        except Exception:
            raise ValueError

    def encrypt(self, data, key=''):
        try:
            if not key: 
                key = self.req_uuid
            data_bytes = data.encode('utf-8')
            padded_data = pad(data_bytes, AES.block_size)
            iv = get_random_bytes(AES.block_size)
            key_bytes = key.replace('-', '').encode('utf-8')
            cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
            encrypted_bytes = cipher.encrypt(padded_data)
            result_bytes = iv + encrypted_bytes
            return base64.b64encode(result_bytes).decode('utf-8')
        except Exception:
            raise ValueError

    def arr2vods(self, arr):
        videos = []
        if not isinstance(arr, list):
            return videos
            
        for i in arr:
            if isinstance(i, dict):
                videos.append({
                    'vod_id': i.get('id', ''),
                    'vod_name': i.get('name', ''),
                    'vod_pic': i.get('pic', ''),
                    'vod_remarks': i.get('remarks', ''),
                    'vod_year': i.get('year', ''),
                    'vod_content': i.get('blurb', ''),
                    'type_name': i.get('class', ''),
                    'vod_area': i.get('area', ''),
                    'vod_actor': i.get('actor', ''),
                    'vod_director': i.get('director', '')
                })
        return videos

    def headers2(self, nonce, timestamp, payload=''):
        sign = self.sign(payload, timestamp, nonce, self.token, self.def_headers2.get('appkey', ''))
        headers = {
            **self.def_headers2,
            'uuid': self.req_uuid,
            'timestamp': timestamp,
            'sign': sign,
            'nonce': nonce
        }
        return headers

    def sign(self, body, timestamp, nonce, token, app_key):
        combined = f'{body}:{timestamp}:{nonce}:{token}:{app_key}'
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()

    def nonce(self):
        random_bytes = os.urandom(16)
        return base64.b64encode(random_bytes).decode('utf-8')

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

