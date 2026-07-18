# -*- coding: utf-8 -*-
# 本资源来源于互联网公开渠道，仅可用于个人学习爬虫技术。
# 严禁将其用于任何商业用途，下载后请于 24 小时内删除，搜索结果均来自源站，本人不承担任何责任。

import re,time,json,urllib3
from base.spider import Spider
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Spider(Spider):
    def __init__(self):
        super().__init__()
        self.base_url = self.device_material = self.base_headers = None
        self.jx_prefix = []  # 初始化存放解析前缀列表

    def init(self, extend=''):
        try:
            ext = json.loads(extend.rstrip())
            doh, pkg, ver, md5 = ext['doh'], ext['pkg'], ext['ver'], ext['md5']
            if not (doh and pkg and ver and bool(re.fullmatch(r'[0-9A-F]{32}', md5))): raise ValueError
            self.device_material = f"{pkg}|{ver}|{md5}"
            jx_prefix_ext = ext.get('jxPrefix', '')
            self.jx_prefix = [p.strip() for p in jx_prefix_ext.split(',') if p.strip()]
            self.base_headers = {
                'User-Agent': f"Dalvik/2.1.0 (Linux; U; Android 17; Pixel 10 Build/TQ3A.260701.001); cycdm-android/{ver}",
                'Accept': "application/json,application/protobuf",
                'Accept-Encoding': "gzip",
                'accept-charset': "UTF-8"
            }

            # 通过 DoH 获取最新域名，并进行多域名 Ping 优选
            # 1. 发起 DoH 请求获取动态域名
            data = self.fetch('https://doh.pub/dns-query', params={'name':doh,'type':"txt"}, headers={'User-Agent':'okhttp/5.1.0','Accept':'application/dns-json'}, verify=False, timeout=5).json()

            domains = []
            if 'Answer' in data:
                for answer in data['Answer']:
                    # 16 代表 TXT 记录
                    if answer.get('type') == 16:
                        # 提取 data 数据并去除首尾的转义引号
                        txt_data = answer.get('data', '').strip('"').strip("'")

                        # 兼容多域名存在的情况 (处理可能的逗号或空格分隔)
                        for d in txt_data.replace(',', ' ').split():
                            if d.startswith('http'):
                                domains.append(d)

            # 去除重复域名，保持列表唯一性
            domains = list(set(domains))

            # 2. 检查是否存在多域名，并进行 Ping 优选
            if domains:
                for domain in domains:
                    # 如果该域名 Ping 测试通过，则将其设为基准 URL 并跳出循环
                    if self._ping_domain(domain):
                        self.base_url = domain
                        # print(f"初始化成功，当前优选域名: {self.base_url}")
                        break
        except Exception:
            self.base_url = ''
            # print(f"Init 获取或校验域名失败")

    def _ping_domain(self, domain):
        # 域名连通性测试方法 (带有动态签名)
        try:
            # Ping 根域名，由于无需特定 path，传入空字符串即可
            path = ""
            clean_params = {}

            # 调用原类自带的签名方法，生成时间戳参数与 Auth Header
            final_params, auth_header = self.get_signature_headers(path, clean_params)

            headers = {**self.base_headers, 'x-cyc-auth': auth_header }

            # 设置 3 秒短超时，用于快速筛除失效节点
            res = self.fetch(domain, params=final_params, headers=headers, verify=False, timeout=3)

            # 如果请求响应正常，说明域名存活且签名算法匹配
            if res.status_code == 200:
                return True
        except Exception:
            pass

        return False

    def homeContent(self, filter):
        if not self.base_url: return None
        data_dict = self.request_api("/index/nav")
        classes, filters = [], {}

        categories = self._ensure_list(data_dict.get(3, []))
        for cat in categories:
            if not isinstance(cat, dict): continue

            type_id = str(cat.get(1, ''))
            raw_type_name = cat.get(2, '')
            if isinstance(raw_type_name, dict) or not raw_type_name: continue

            type_name = str(raw_type_name)
            if not type_id: continue

            classes.append({'type_id': type_id, 'type_name': type_name})

            # 解析筛选条件
            filter_configs = []
            raw_filters = cat.get(3, {})
            if isinstance(raw_filters, dict):
                field_map = {1: ('class', '类型'), 2: ('area', '地区'), 3: ('lang', '语言'), 4: ('year', '年份')}
                for f_num, (f_key, f_name) in field_map.items():
                    val_str = raw_filters.get(f_num, '')
                    if not val_str or not isinstance(val_str, str): continue

                    values_list = [{"n": "全部", "v": ""}]
                    for item in val_str.split(','):
                        if item.strip(): values_list.append({"n": item.strip(), "v": item.strip()})
                    filter_configs.append({"key": f_key, "name": f_name, "init": "", "value": values_list})

            # 固定排序筛选
            filter_configs.append({
                "key": "order", "name": "排序", "init": "time",
                "value": [{"n": "最新", "v": "time"}, {"n": "热度最高", "v": "hits"}, {"n": "好评", "v": "score"}]
            })
            filters[type_id] = filter_configs

        return {'class': classes, 'filters': filters}

    def homeVideoContent(self):
        if not self.base_url: return None
        data_dict = self.request_api("/index/video")
        videos = []

        categories = self._ensure_list(data_dict.get(3, []))
        for cat in categories:
            if not isinstance(cat, dict): continue
            cat_videos = self._ensure_list(cat.get(5, []))
            for v in cat_videos:
                if not isinstance(v, dict): continue
                videos.append({
                    'vod_id': str(v.get(1, '')), 'vod_name': str(v.get(2, '')),
                    'vod_pic': str(v.get(3, '')), 'vod_remarks': str(v.get(5, '')),
                    'vod_year': str(v.get(7, '')), 'type_name': str(v.get(9, ''))
                })
        return {'list': videos}

    def categoryContent(self, tid, pg, filter, extend):
        if not self.base_url: return None
        params = {'tid': str(tid), 'page': str(pg), 'limit': "20", 'order': "time"}
        if extend: params.update({k: str(v) for k, v in extend.items()})

        data_dict = self.request_api("/v2/video/query", params=params)
        videos, raw_list, total = [], [], 0

        # 兼容 JSON 与 PB 数据体
        data_body = data_dict.get('data') or data_dict.get(3) or {}

        if isinstance(data_body, dict):
            total = data_body.get('total') or data_body.get(1) or 0
            raw_list = data_body.get('list') or data_body.get(2) or []
        elif isinstance(data_body, list):
            for item in data_body:
                if isinstance(item, dict):
                    raw_list.extend(self._ensure_list(item.get('list') or item.get(5) or []))

        for v in self._ensure_list(raw_list):
            if not isinstance(v, dict): continue

            vod_id = v.get('vod_id') or v.get(1) or ''
            vod_name = v.get('name') or v.get(2) or ''
            if vod_id and vod_name:
                videos.append({
                    'vod_id': str(vod_id),
                    'vod_name': str(vod_name),
                    'vod_pic': str(v.get('pic') or v.get(3) or ''),
                    'vod_remarks': str(v.get('remarks') or v.get(8) or v.get(5) or '')
                })

        try:
            total_int = int(total)
        except Exception:
            total_int = 0
        page_count = (total_int + 19) // 20 if total_int > 0 else 1

        return {'list': videos, 'page': pg, 'pagecount': page_count, 'limit': 20, 'total': total_int}

    def searchContent(self, key, quick, pg='1'):
        if not self.base_url: return None
        params = {'text': str(key), 'pg': str(pg), 'type_id': "0", 'limit': "20"}
        data_dict = self.request_api("/v2/video/search", params=params)
        videos = []

        data_body = data_dict.get('data') or data_dict.get(4) or data_dict.get(3) or []
        for v in self._ensure_list(data_body):
            if not isinstance(v, dict): continue

            vod_id = v.get('vod_id') or v.get(1) or ''
            vod_name = v.get('name') or v.get(2) or ''
            if vod_id and vod_name:
                videos.append({
                    'vod_id': str(vod_id),
                    'vod_name': str(vod_name),
                    'vod_pic': str(v.get('pic') or v.get(3) or v.get(4) or ''),
                    'vod_remarks': str(v.get('remarks') or v.get(8) or v.get(5) or '')
                })

        total = data_dict.get('total') or data_dict.get(3) or data_dict.get(1) or 0
        try:
            total_int = int(total)
        except Exception:
            total_int = 0
        page_count = (total_int + 19) // 20 if total_int > 0 else 1

        return {'list': videos, 'page': pg, 'pagecount': page_count}

    def detailContent(self, ids):
        if not self.base_url: return None
        vod_id = ids[0]
        data_dict = self.request_api(f"/v2/video/info/{vod_id}")
        data = data_dict.get('data') or data_dict.get(3) or {}

        shows, play_urls = [], []
        play_from_list = self._ensure_list(data.get('vod_play_from') or data.get(24) or data.get(20) or [])

        for pf in play_from_list:
            if not isinstance(pf, dict): continue
            source_code = pf.get('code') or pf.get(1)
            source_name = pf.get('name') or pf.get(2) or source_code
            if not source_code: continue

            # 【修改处】在详情页直接拉取所有的剧集内容，固定 index='-1'
            params = {'id': str(vod_id), 'from': str(source_code), 'index': '-1'}
            play_data_dict = self.request_api("/video/play_url", params=params)

            # 取出列表数据，对应 JSON 里的 "3"
            raw_play_list = play_data_dict.get('data') or play_data_dict.get(3) or []

            eps = []
            for ep in self._ensure_list(raw_play_list):
                if not isinstance(ep, dict): continue

                ep_name = ep.get('name') or ep.get(1) or '未知'
                ep_url = ep.get('url') or ep.get('play_url') or ep.get(2) or ''
                # 获取新增加的值 3，表示是否 json 解析
                ep_parse = ep.get('parse') or ep.get(3) or 0

                if ep_url:
                    # 用 @@ 分隔传递 URL 和 Parse 标识到 playerContent
                    eps.append(f"{ep_name}${ep_url}@@{ep_parse}")

            if eps:
                shows.append(str(source_name))
                play_urls.append('#'.join(eps))

        video = {
            'vod_id': str(vod_id),
            'vod_name': str(data.get('vod_name') or data.get(3) or data.get(2) or ''),
            'vod_pic': str(data.get('vod_pic') or data.get(7) or data.get(4) or ''),
            'vod_remarks': str(data.get('vod_remarks') or data.get(12) or data.get(5) or ''),
            'vod_year': str(data.get('vod_year') or data.get(14) or data.get(15) or ''),
            'vod_area': str(data.get('vod_area') or data.get(13) or data.get(14) or ''),
            'vod_actor': str(data.get('vod_actor') or data.get(8) or ''),
            'vod_director': str(data.get('vod_director') or data.get(9) or ''),
            'vod_content': str(data.get('vod_content') or data.get(23) or data.get(15) or ''),
            'type_name': str(data.get('vod_class') or data.get(6) or ''),
            'vod_play_from': '$$$'.join(shows),
            'vod_play_url': '$$$'.join(play_urls)
        }
        return {'list': [video]}

    def playerContent(self, flag, vid, vip_flags):
        # 【修改处】分离从详情页传递过来的 url 与 parse_flag
        parts = vid.split('@@')
        url = parts[0]
        parse_flag = parts[1] if len(parts) > 1 else '0'

        # 匹配配置里的多规则解析前缀
        matched_prefix = None
        for prefix in self.jx_prefix:
            if url.startswith(prefix):
                matched_prefix = prefix
                break

        # 如果获取标识值为 1，或者匹配到了 jx_prefix 前缀，执行 json 解析
        if str(parse_flag) == '1' or matched_prefix:
            try:
                res = self.fetch(url, verify=False, headers={'User-Agent': 'okhttp/4.12.0'})
                json_res = res.json()
                # 尝试获取 json 里的 url 键值，失败则抹除前缀进行直连兜底
                url = json_res.get('url') or (url.replace(matched_prefix, '', 1) if matched_prefix else url)
            except Exception:
                # 解析失败时的兜底逻辑
                url = url.replace(matched_prefix, '', 1) if matched_prefix else url

        return {'parse': 0, 'url': url, 'header': {'User-Agent': 'libmpv'}}

    def _ensure_list(self, obj):
        """确保对象返回列表格式"""
        if not obj: return []
        return obj if isinstance(obj, list) else [obj]

        # 纯 Python 实现 XXHash64
    def xxh64_hexdigest(self, data, seed=0):
        MASK64 = 0xFFFFFFFFFFFFFFFF
        PRIME64_1 = 0x9E3779B185EBCA87
        PRIME64_2 = 0xC2B2AE3D27D4EB4F
        PRIME64_3 = 0x165667B19E3779F9
        PRIME64_4 = 0x85EBCA77C2B2AE63
        PRIME64_5 = 0x27D4EB2F165667C5

        def rotl64(x, r):
            return ((x << r) | (x >> (64 - r))) & MASK64

        def round_calc(acc, input_val):
            acc = (acc + (input_val * PRIME64_2) & MASK64) & MASK64
            acc = rotl64(acc, 31)
            return (acc * PRIME64_1) & MASK64

        def merge_round(acc, val):
            val = round_calc(0, val)
            acc = (acc ^ val) & MASK64
            return (acc * PRIME64_1 + PRIME64_4) & MASK64

        b = data if isinstance(data, bytes) else data.encode('utf-8')
        l = len(b)

        if l >= 32:
            v1 = (seed + PRIME64_1 + PRIME64_2) & MASK64
            v2 = (seed + PRIME64_2) & MASK64
            v3 = seed & MASK64
            v4 = (seed - PRIME64_1) & MASK64

            p = 0
            limit = l - 32
            while p <= limit:
                v1 = round_calc(v1, int.from_bytes(b[p:p + 8], 'little'))
                p += 8
                v2 = round_calc(v2, int.from_bytes(b[p:p + 8], 'little'))
                p += 8
                v3 = round_calc(v3, int.from_bytes(b[p:p + 8], 'little'))
                p += 8
                v4 = round_calc(v4, int.from_bytes(b[p:p + 8], 'little'))
                p += 8

            h64 = (rotl64(v1, 1) + rotl64(v2, 7) + rotl64(v3, 12) + rotl64(v4, 18)) & MASK64
            h64 = merge_round(h64, v1)
            h64 = merge_round(h64, v2)
            h64 = merge_round(h64, v3)
            h64 = merge_round(h64, v4)
        else:
            h64 = (seed + PRIME64_5) & MASK64

        h64 = (h64 + l) & MASK64
        p = l - (l % 32) if l >= 32 else 0

        while p + 8 <= l:
            k1 = round_calc(0, int.from_bytes(b[p:p + 8], 'little'))
            h64 = (h64 ^ k1) & MASK64
            h64 = rotl64(h64, 27)
            h64 = (h64 * PRIME64_1 + PRIME64_4) & MASK64
            p += 8

        if p + 4 <= l:
            h64 = (h64 ^ ((int.from_bytes(b[p:p + 4], 'little') * PRIME64_1) & MASK64)) & MASK64
            h64 = rotl64(h64, 23)
            h64 = (h64 * PRIME64_2 + PRIME64_3) & MASK64
            p += 4

        while p < l:
            h64 = (h64 ^ ((b[p] * PRIME64_5) & MASK64)) & MASK64
            h64 = rotl64(h64, 11)
            h64 = (h64 * PRIME64_1) & MASK64
            p += 1

        h64 = (h64 ^ (h64 >> 33)) & MASK64
        h64 = (h64 * PRIME64_2) & MASK64
        h64 = (h64 ^ (h64 >> 29)) & MASK64
        h64 = (h64 * PRIME64_3) & MASK64
        h64 = (h64 ^ (h64 >> 32)) & MASK64

        return f"{h64:016x}"

    def parse_pb_varint(self, stream, pos):
        result, shift = 0, 0
        while pos < len(stream):
            byte = stream[pos]
            pos += 1
            result |= (byte & 0x7F) << shift
            shift += 7
            if not (byte & 0x80): break
        return result, pos

    def is_valid_pb_message(self, b):
        p = 0
        while p < len(b):
            try:
                tag_wire, p = self.parse_pb_varint(b, p)
                if p > len(b) or tag_wire == 0: return False
                wt = tag_wire & 0x07
                fn = tag_wire >> 3
                if fn == 0: return False
                if wt == 0:
                    _, p = self.parse_pb_varint(b, p)
                elif wt == 1:
                    p += 8
                elif wt == 2:
                    length, p = self.parse_pb_varint(b, p)
                    p += length
                elif wt == 5:
                    p += 4
                else:
                    return False
            except Exception:
                return False
        return p == len(b) and len(b) > 0

    def decode_length_delimited(self, data):
        if not data: return ""

        # 1. 优先尝试解析为 UTF-8 字符串
        try:
            decoded_str = data.decode('utf-8')
            # 增加一个简单的启发式判断：如果字符串中包含大量不可打印字符，则认为它不是普通文本
            # 如果是合法的文本，则直接返回，避免被误判为嵌套消息
            if all(c.isprintable() or c.isspace() for c in decoded_str) and len(decoded_str) > 0:
                return decoded_str
        except UnicodeDecodeError:
            pass

        # 2. 如果不是有效的字符串，再检查是否为合法的 PB 嵌套结构
        if self.is_valid_pb_message(data):
            try:
                parsed = self.parse_pb_message(data)
                if isinstance(parsed, dict) and len(parsed) > 0:
                    return parsed
            except Exception:
                pass

        # 3. 实在不行则返回 Hex
        return data.hex()

    def parse_pb_message(self, stream):
        pos, msg = 0, {}
        while pos < len(stream):
            try:
                tag_wire, pos = self.parse_pb_varint(stream, pos)
                if pos > len(stream) or tag_wire == 0: break
                wire_type = tag_wire & 0x07
                field_num = tag_wire >> 3

                val = None
                if wire_type == 0:  # Varint
                    val, pos = self.parse_pb_varint(stream, pos)
                elif wire_type == 1:  # 64-bit
                    val, pos = stream[pos:pos + 8], pos + 8
                elif wire_type == 2:  # Length-delimited (关键点)
                    length, pos = self.parse_pb_varint(stream, pos)
                    # 此处调用改进后的 decode_length_delimited
                    val = self.decode_length_delimited(stream[pos:pos + length])
                    pos += length
                elif wire_type == 5:  # 32-bit
                    val, pos = stream[pos:pos + 4], pos + 4
                else:
                    break

                if field_num not in msg: msg[field_num] = []
                msg[field_num].append(val)
            except Exception:
                break

        # 展开单元素列表
        for k in msg:
            if len(msg[k]) == 1: msg[k] = msg[k][0]
        return msg


    def get_signature_headers(self, path, business_params):
        timestamp = int(time.time() * 1000)
        full_params = dict(business_params)
        full_params['timestamp'] = str(timestamp)


        hash1 = self.xxh64_hexdigest(self.device_material, seed=0)

        sign_params = {str(k): [str(v)] for k, v in full_params.items()}
        data = {
            "method": "GET",
            "timestamp": timestamp,
            "path": path,
            "parameters": sign_params,
            "body": ""
        }

        json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        hash2 = self.xxh64_hexdigest(json_str, seed=timestamp)
        final_input = f"{timestamp}|{hash2}|{hash1}"
        final_seed = timestamp ^ 0x9E3779B185EBCA87
        final_hash = self.xxh64_hexdigest(final_input, seed=final_seed)

        return full_params, f"v3:{timestamp}:{final_hash}"

    def request_api(self, path, params=None):
        if params is None: params = {}
        clean_params = {k: v for k, v in params.items() if v != ""}
        final_params, auth_header = self.get_signature_headers(path, clean_params)

        headers = { **self.base_headers, 'x-cyc-auth': auth_header }
        response = self.fetch(f"{self.base_url}{path}", params=final_params, verify=False, headers=headers)
        if 'application/protobuf' in response.headers.get('Content-Type', '').lower():
            return self.parse_pb_message(response.content)
        try:
            return response.json()
        except Exception:
            return {}

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