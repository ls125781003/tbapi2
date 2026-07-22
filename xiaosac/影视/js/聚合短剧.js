/*
@header({
  searchable: 1,
  filterable: 1,
  quickSearch: 1,
  title: '短剧聚合1[DRPY]',
  author: 'Gemini',
  '类型': '短剧',
  lang: 'ds'
})
*/

globalThis.aggConfig = {
    keys: 'd3dGiJc651gSQ8w1',
    charMap: {
        '+': 'P', '/': 'X', '0': 'M', '1': 'U', '2': 'l', '3': 'E', '4': 'r', '5': 'Y', '6': 'W', '7': 'b', '8': 'd', '9': 'J',
        'A': '9', 'B': 's', 'C': 'a', 'D': 'I', 'E': '0', 'F': 'o', 'G': 'y', 'H': '_', 'I': 'H', 'J': 'G', 'K': 'i', 'L': 't',
        'M': 'g', 'N': 'N', 'O': 'A', 'P': '8', 'Q': 'F', 'R': 'k', 'S': '3', 'T': 'h', 'U': 'f', 'V': 'R', 'W': 'q', 'X': 'C',
        'Y': '4', 'Z': 'p', 'a': 'm', 'b': 'B', 'c': 'O', 'd': 'u', 'e': 'c', 'f': '6', 'g': 'K', 'h': 'x', 'i': '5', 'j': 'T',
        'k': '-', 'l': '2', 'm': 'z', 'n': 'S', 'o': 'Z', 'p': '1', 'q': 'V', 'r': 'v', 's': 'j', 't': 'Q', 'u': '7', 'v': 'D',
        'w': 'w', 'x': 'n', 'y': 'L', 'z': 'e'
    },
    headers: {
        default: { 'User-Agent': 'okhttp/3.12.11', 'content-type': 'application/json; charset=utf-8' }
    },
    platform: {
        星芽: { host: 'https://app.whjzjx.cn', url1: '/cloud/v2/theater/home_page?theater_class_id', url2: '/v2/theater_parent/detail', search: '/v3/search', classes: '/cloud/v2/theater/classes', rankDetail: '/cloud/v1/first_level_ranking/detail', loginUrl: 'https://u.shytkjgs.com/user/v1/account/login' },
        西饭: { host: 'https://xifan-api-cn.youlishipin.com', url1: '/xifan/drama/portalPage', url2: '/xifan/drama/getDuanjuInfo', search: '/xifan/search/getSearchList' },
        七猫: { host: 'https://api-store.qmplaylet.com', url1: '/api/v1/playlet/index', url2: 'https://api-read.qmplaylet.com/player/api/v1/playlet/info', search: '/api/v1/playlet/search' },
        围观: { host: 'https://api.drama.9ddm.com', url1: '/drama/home/shortVideoTags', url2: '/drama/home/shortVideoDetail', search: '/drama/home/search' },
        河马: { host: 'https://www.kuaikaw.cn', search: '/seo/video/6007' }
    },
    platformList: [
        { name: '七猫短剧', id: '七猫' },
        { name: '星芽短剧', id: '星芽' },
        { name: '西饭短剧', id: '西饭' },
        { name: '围观短剧', id: '围观' },
        { name: '河马短剧', id: '河马' }
    ],
    search: { limit: 30, timeout: 6000 }
};

// ==================== 工具辅助函数 ====================
async function md5(str) {
    return CryptoJS.MD5(str).toString(CryptoJS.enc.Hex).toLowerCase();
}
function base64Encode(text) {
    return CryptoJS.enc.Base64.stringify(CryptoJS.enc.Utf8.parse(text));
}
function base64Decode(text) {
    return CryptoJS.enc.Utf8.stringify(CryptoJS.enc.Base64.parse(text));
}
function stripHtml(text) {
    return String(text || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
}
function joinTags(tags) {
    if (Array.isArray(tags)) {
        return tags.map(tag => {
            if (!tag) return '';
            if (typeof tag === 'string') return tag;
            return tag.name || tag.title || tag.label || tag.text || '';
        }).filter(Boolean).join(' ');
    }
    return String(tags || '');
}
function buildSearchRemark(platform, episodeText = '', extra = '') {
    const parts = [platform];
    const ep = String(episodeText || '').trim();
    if (ep) parts.push(/集|期|完结|更新/.test(ep) ? ep : `${ep}集`);
    const suffix = String(extra || '').trim();
    return suffix ? `${parts.join('｜')} ${suffix}` : parts.join('｜');
}
function parseNextData(html) {
    try {
        const match = String(html || '').match(/<script id="__NEXT_DATA__" type="application\/json">([\s\S]*?)<\/script>/);
        return match?.[1] ? JSON.parse(match[1]) : null;
    } catch (e) {
        return null;
    }
}
function normalizeHemaSearchBook(book) {
    if (!book?.bookId) return null;
    return {
        vod_id: `河马@/drama/${book.bookId}`,
        vod_name: book.bookName,
        vod_pic: book.coverWap,
        vod_remarks: buildSearchRemark('河马短剧', `${book.statusDesc || (book.status === 1 ? '完本' : '更新中') || ''} ${book.totalChapterNum || ''}集`.trim()),
        vod_tag: joinTags(book.bookTypeThree || book.tags || book.categoryName || book.categoryNames),
        vod_content: [book.introduction, book.desc, book.bookDesc, book.actor, book.actress].filter(Boolean).join(' ')
    };
}
function buildHemaTmpId() {
    return Math.random().toString(36).slice(2, 18);
}
function getHemaHeaders(referer = 'https://www.kuaikaw.cn') {
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        Referer: referer,
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    };
}
function getHemaApiHeaders(referer) {
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        Referer: referer,
        Origin: 'https://www.kuaikaw.cn',
        'Content-Type': 'application/json',
        Accept: 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        pname: 'www.kuaikaw.cn',
        tmpid: buildHemaTmpId()
    };
}
async function getQmParamsAndSign() {
    const sessionId = Math.floor(Date.now()).toString();
    const data = {
        "static_score": "0.8", "uuid": "00000000-7fc7-08dc-0000-000000000000",
        "device-id": "20250220125449b9b8cac84c2dd3d035c9052a2572f7dd0122edde3cc42a70",
        "sourceuid": "aa7de295aad621a6", "refresh-type": "0", "model": "22021211RC",
        "client-id": "aa7de295aad621a6", "brand": "Redmi", "sys-ver": "12", "phone-level": "H",
        "wlb-uid": "aa7de295aad621a6", "session-id": sessionId
    };
    const jsonStr = JSON.stringify(data);
    const base64Str = btoa(unescape(encodeURIComponent(jsonStr)));
    let qmParams = '';
    for (let i = 0; i < base64Str.length; i++) {
        qmParams += globalThis.aggConfig.charMap[base64Str[i]] || base64Str[i];
    }
    const paramsStr = `AUTHORIZATION=app-version=10001application-id=com.duoduo.readchannel=unknownis-white=net-env=5platform=androidqm-params=${qmParams}reg=${globalThis.aggConfig.keys}`;
    return { qmParams, sign: await md5(paramsStr) };
}
async function getHeaderX() {
    const { qmParams, sign } = await getQmParamsAndSign();
    return {
        'net-env': '5', 'reg': '', 'channel': 'unknown', 'is-white': '', 'platform': 'android',
        'application-id': 'com.duoduo.read', 'authorization': '', 'app-version': '10001',
        'user-agent': 'webviewversion/0', 'qm-params': qmParams, 'sign': sign
    };
}

// ==================== 主规则对象 ====================
var rule = {
    类型: '短剧',
    title: '聚合短剧1[短]',
    author: 'Gemini',
    host: '',
    url: '',
    searchUrl: '*',
    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    timeout: 5000,
    play_parse: true,
    search_match: true,
    headers: globalThis.aggConfig.headers.default,
    filter_url: '{{fl.area}}',
    
    filter_def: {
        星芽: { area: '1', class2: '0', rank: '1' },
        西饭: { area: '都市' },
        七猫: { area: '0' },
        围观: { area: '' },
        河马: { area: '462' }
    },

    filter: {
        七猫: [{
            key: 'area', name: '分类',
            value: [
                { n: '全部', v: '0' }, { n: '男频', v: '1' }, { n: '新剧', v: '3' }, { n: '现代言情', v: '21' },
                { n: '神豪', v: '37' }, { n: '萌宝', v: '356' }, { n: '穿越', v: '373' }, { n: '战神', v: '527' },
                { n: '神医', v: '1269' }, { n: '古装', v: '1272' }
            ]
        }],
        星芽: [{
            key: 'area', name: '剧场',
            value: [
                { n: '剧场', v: '1' }, { n: '热播短剧', v: '2' }, { n: '会员专享', v: '8' },
                { n: '星选好剧', v: '7' }, { n: '新剧', v: '3' }, { n: '阳光剧场', v: '5' }, { n: '排行榜', v: '9' }
            ]
        }, {
            key: 'class2', name: '类型',
            value: [
                { n: '全部', v: '0' }, { n: '都市', v: '4' }, { n: '逆袭', v: '7' }, { n: '古装', v: '5' },
                { n: '亲情', v: '41' }, { n: '现代言情', v: '15' }, { n: '重生', v: '6' }, { n: '虐恋', v: '8' },
                { n: '玄幻', v: '35' }, { n: '穿越', v: '17' }, { n: '脑洞', v: '32' }, { n: '甜宠', v: '33' },
                { n: '古代言情', v: '37' }, { n: '战神', v: '24' }, { n: '历史', v: '40' }, { n: '赘婿', v: '26' },
                { n: '萌宝', v: '9' }, { n: '神医', v: '25' }
            ]
        }, {
            key: 'rank', name: '榜单',
            value: [
                { n: '实时热榜', v: '1' }, { n: '热搜榜', v: '2' }, { n: '新剧榜', v: '3' },
                { n: '剧单榜', v: '4' }, { n: '口碑榜', v: '5' }
            ]
        }],
        西饭: [{
            key: 'area', name: '分类',
            value: [
                { n: '都市', v: '都市' }, { n: '甜宠', v: '甜宠' }, { n: '逆袭', v: '逆袭' },
                { n: '战神', v: '战神' }, { n: '古装', v: '古装' }, { n: '穿越', v: '穿越' }, { n: '萌宝', v: '萌宝' }
            ]
        }],
        围观: [{
            key: 'area', name: '分类',
            value: [
                { n: '全部', v: '' }, { n: '都市', v: '都市' }, { n: '逆袭', v: '逆袭' }, { n: '家庭', v: '家庭' },
                { n: '古装', v: '古装' }, { n: '复仇', v: '复仇' }, { n: '甜宠', v: '甜宠' }, { n: '悬疑', v: '悬疑' },
                { n: '爱情', v: '爱情' }, { n: '重生', v: '重生' }, { n: '总裁', v: '总裁' }, { n: '穿越', v: '穿越' },
                { n: '萌宝', v: '萌宝' }, { n: '战神', v: '战神' }, { n: '职场', v: '职场' }, { n: '神豪', v: '神豪' },
                { n: '神医', v: '神医' }, { n: '赘婿', v: '赘婿' }
            ]
        }],
        河马: [{
            key: 'area', name: '分类',
            value: [
                { n: '甜宠', v: '462' }, { n: '古装仙侠', v: '1102' }, { n: '现代言情', v: '1145' },
                { n: '青春', v: '1170' }, { n: '豪门恩怨', v: '585' }, { n: '逆袭', v: '417-464' },
                { n: '重生', v: '439-465' }, { n: '系统', v: '1159' }, { n: '总裁', v: '1147' }, { n: '职场商战', v: '943' }
            ]
        }]
    },

    预处理: async function () {
        const cfg = globalThis.aggConfig;
        try {
            const data = { 'device': '24250683a3bdb3f118dff25ba4b1cba1a' };
            const options = {
                method: 'POST',
                headers: { 'User-Agent': 'okhttp/4.10.0', 'platform': '1', 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            };
            let html = await request(cfg.platform.星芽.loginUrl, options);
            const res = JSON.parse(html);
            const token = res?.data?.token || res?.token;
            this.xingya_headers = { ...rule.headers, authorization: token };
        } catch (e) {
            log(`星芽短剧token获取失败: ${e.message}`);
            this.xingya_headers = rule.headers;
        }
    },

    class_parse: () => ({
        class: globalThis.aggConfig.platformList.map(item => ({
            type_id: item.id,
            type_name: item.name
        }))
    }),

    推荐: async function () {
        const cfg = globalThis.aggConfig;
        const randomPlat = cfg.platformList[Math.floor(Math.random() * cfg.platformList.length)];
        const platId = randomPlat.id;
        const defaultFilter = this.filter_def?.[platId] || {};
        const fakeContext = {
            MY_CATE: platId,
            MY_FL: defaultFilter,
            MY_PAGE: 1,
            ...this
        };
        return await this.一级.call(fakeContext);
    },

    一级: async function () {
        const { MY_CATE, MY_FL, MY_PAGE } = this;
        const area = MY_FL?.area || '';
        const plat = globalThis.aggConfig.platform[MY_CATE];
        const cfg = globalThis.aggConfig;
        let d = [];
        if (!plat) return setResult(d);

        const fetchStr = async (url, opt = {}) => await request(url, { headers: this.headers, ...opt });

        try {
            switch (MY_CATE) {
                case '七猫': {
                    const sign = await md5(`operation=1playlet_privacy=1tag_id=${area}${cfg.keys}`);
                    const url = `${plat.host}${plat.url1}?tag_id=${area}&playlet_privacy=1&operation=1&sign=${sign}`;
                    const headers = { ...await getHeaderX(), ...cfg.headers.default };
                    const res = JSON.parse(await fetchStr(url, { headers }));
                    (res?.data?.list || []).forEach(item => {
                        d.push({ title: item.title, img: item.image_link, desc: `${item.total_episode_num}集`, url: `七猫@${encodeURIComponent(item.playlet_id)}` });
                    });
                    break;
                }
                case '星芽': {
                    const class2 = MY_FL?.class2 || '0';
                    const headers = this.xingya_headers || cfg.headers.default;
                    if (area === '9') {
                        const rank = MY_FL?.rank || class2 || '1';
                        const res = JSON.parse(await fetchStr(`${plat.host}${plat.rankDetail}?id=${rank}`, { headers }));
                        (res?.data?.list || []).forEach(item => {
                            const i = item.theater || item;
                            if (!i?.id) return;
                            d.push({ title: i.title, img: i.cover_url, desc: `${i.total || ''}集`, url: `星芽@${plat.host}${plat.url2}?theater_parent_id=${i.id}` });
                        });
                    } else {
                        const url = `${plat.host}${plat.url1}=${area}&type=1&class2_ids=${class2}&page_num=${MY_PAGE}&page_size=24`;
                        const res = JSON.parse(await fetchStr(url, { headers }));
                        (res?.data?.list || []).forEach(i => {
                            const item = i.theater || i;
                            if (!item?.id) return;
                            d.push({ title: item.title, img: item.cover_url, desc: `${item.total || ''}集`, url: `星芽@${plat.host}${plat.url2}?theater_parent_id=${item.id}` });
                        });
                    }
                    break;
                }
                case '西饭': {
                    const typeName = area;
                    const searchUrl = `${plat.host}${plat.search}?reqType=search&offset=0&keyword=${encodeURIComponent(typeName || '')}&quickEngineVersion=-1&scene=`;
                    const res = JSON.parse(await fetchStr(searchUrl));
                    const elements = res?.result?.elements || [];
                    for (const block of elements) {
                        const contents = Array.isArray(block?.contents) ? block.contents : [];
                        for (const item of contents) {
                            const dj = item?.duanjuVo || {};
                            if (!dj.duanjuId) continue;
                            const categories = Array.isArray(dj.categories) ? dj.categories : [];
                            if (typeName && !categories.includes(typeName)) continue;
                            d.push({ title: dj.title, img: dj.coverImageUrl, desc: `${dj.total || ''}集`, url: `西饭@${dj.duanjuId}#${dj.source}` });
                        }
                    }
                    break;
                }
                case '围观': {
                    const clientInfo = await md5(String(Date.now()).slice(-10));
                    const url = `${plat.host}${plat.search}?version_code=1500&version_name=1.5.0&device_name=Pixel%208%20Pro&device_type=phone&is_first_day=true&is_first_24h=true&app_launch_way=icon&default_homepage=homepage_interaction&device_owning_firm=Google&font_scale=default&os_type=1&clientInfo=${clientInfo}`;
                    const opt = {
                        method: 'POST',
                        headers: { 'User-Agent': 'okhttp/5.1.0', 'Content-Type': 'application/json; charset=utf-8' },
                        body: JSON.stringify({ audience: '全部', order: '最新', page: MY_PAGE, pageSize: 30, searchWord: '', subject: area || '' })
                    };
                    const res = JSON.parse(await fetchStr(url, opt));
                    (res?.data || []).forEach(i => {
                        d.push({ title: i.title, img: i.horzPoster || i.vertPoster, desc: `${i.episodeCount || ''}集`, url: `围观@${i.oneId}` });
                    });
                    break;
                }
                case '河马': {
                    const url = `${plat.host}/browse/${area || '462'}/${MY_PAGE}`;
                    const html = await fetchStr(url, { headers: getHemaHeaders(url) });
                    const json = parseNextData(html);
                    const bookList = json?.props?.pageProps?.bookList || [];
                    for (const book of bookList) {
                        if (!book?.bookId) continue;
                        d.push({ title: book.bookName, img: book.coverWap, desc: `${book.statusDesc || ''} ${book.totalChapterNum || ''}集`.trim(), url: `河马@/drama/${book.bookId}` });
                    }
                    break;
                }
            }
        } catch (e) {
            log(`${MY_CATE}一级加载失败: ${e.message}`);
        }
        return setResult(d);
    },

    二级: async function () {
        const { orId } = this;
        const [platform, ...rest] = orId.split('@');
        const id = rest.join('@');
        const cfg = globalThis.aggConfig;
        const plat = cfg.platform[platform];
        const fetchStr = async (url, opt = {}) => await request(url, { headers: this.headers, ...opt });

        let VOD = {
            vod_id: orId, vod_name: '未知', vod_pic: '', vod_remarks: '',
            vod_content: '', vod_play_from: platform + '短剧', vod_play_url: ''
        };

        if (!plat) return VOD;

        try {
            switch (platform) {
                case '七猫': {
                    const didDecoded = decodeURIComponent(id);
                    const sign = await md5(`playlet_id=${didDecoded}${cfg.keys}`);
                    const url = `${plat.url2}?playlet_id=${didDecoded}&sign=${sign}`;
                    const headers = { ...await getHeaderX(), ...cfg.headers.default };
                    const res = JSON.parse(await fetchStr(url, { headers }));
                    if (res?.data) {
                        const d = res.data;
                        VOD.vod_name = d.title; VOD.vod_pic = d.image_link; VOD.vod_remarks = `${d.total_episode_num}集`; VOD.vod_content = d.intro;
                        VOD.vod_play_url = (d.play_list || []).map(i => `${i.sort}$${i.video_url}`).join('#');
                    }
                    break;
                }
                case '星芽': {
                    const headers = this.xingya_headers || cfg.headers.default;
                    const res = JSON.parse(await fetchStr(id, { headers }));
                    if (res?.data) {
                        const d = res.data;
                        VOD.vod_name = d.title; VOD.vod_pic = d.cover_url; VOD.vod_remarks = d.desc_tags + ''; VOD.vod_content = d.introduction || '';
                        VOD.vod_play_url = (d.theaters || []).map(i => `${i.num}$${i.son_video_url}`).join('#');
                    }
                    break;
                }
                case '西饭': {
                    const [duanjuId, source] = id.split('#');
                    const url = `${plat.host}${plat.url2}?duanjuId=${duanjuId}&source=${source}`;
                    const res = JSON.parse(await fetchStr(url));
                    if (res?.result) {
                        const d = res.result;
                        VOD.vod_name = d.title; VOD.vod_pic = d.coverImageUrl; VOD.vod_content = d.desc || '';
                        VOD.vod_remarks = d.updateStatus === 'over' ? `${d.total}集 已完结` : `更新${d.total}集`;
                        VOD.vod_play_url = (d.episodeList || []).map(e => `${e.index}$${e.playUrl}`).join('#');
                    }
                    break;
                }
                case '围观': {
                    const clientInfo = await md5(String(Date.now()).slice(-10));
                    const url = `${plat.host}${plat.url2}?version_code=1500&version_name=1.5.0&device_name=Pixel%208%20Pro&device_type=phone&is_first_day=true&is_first_24h=true&app_launch_way=icon&default_homepage=homepage_interaction&device_owning_firm=Google&font_scale=default&os_type=1&clientInfo=${clientInfo}&oneId=${id}&page=1&pageSize=1000&userId=0&queryAll=true`;
                    const res = JSON.parse(await fetchStr(url, { headers: { 'User-Agent': 'okhttp/5.1.0', 'Content-Type': 'application/json; charset=utf-8' } }));
                    if (res?.data?.length) {
                        const episodes = res.data;
                        VOD.vod_name = res.title || episodes[0]?.title || VOD.vod_name;
                        VOD.vod_pic = res.vertPoster || episodes[0]?.vertPoster || '';
                        VOD.vod_remarks = `共${episodes.length}集`; VOD.vod_content = res.description || '';
                        VOD.vod_play_url = episodes.map(e => `${e.playOrder || e.title}$${base64Encode(JSON.stringify(e.videoClarityList || []))}`).join('#');
                    }
                    break;
                }
                case '河马': {
                    const didPath = id.startsWith('/drama/') ? id : `/drama/${id}`;
                    const html = await fetchStr(`${plat.host}${didPath}`, { headers: getHemaHeaders(`${plat.host}${didPath}`) });
                    const json = parseNextData(html);
                    const pageProps = json?.props?.pageProps || {};
                    const bookInfo = pageProps.bookInfoVo || {};
                    const chapterList = pageProps.chapterList || [];
                    VOD.vod_name = bookInfo.title || bookInfo.bookName || VOD.vod_name; VOD.vod_pic = bookInfo.coverWap || '';
                    VOD.vod_remarks = `${bookInfo.statusDesc || ''} ${bookInfo.totalChapterNum || ''}集`.trim(); VOD.vod_content = bookInfo.introduction || '';
                    VOD.vod_play_url = chapterList.map(chapter => {
                        const chapterId = chapter.chapterId; const chapterName = chapter.chapterName;
                        const videoVo = chapter.chapterVideoVo || {}; const directUrl = videoVo.mp4 || videoVo.mp4720p || videoVo.vodMp4Url;
                        return `${chapterName}$${directUrl && /\.(mp4|m3u8)/.test(directUrl) ? directUrl : `${didPath.replace('/drama/', '')}+${chapterId}`}`;
                    }).join('#');
                    break;
                }
            }
        } catch (e) {
            VOD.vod_name = '加载失败';
        }
        return VOD;
    },

    搜索: async function (wd, quick, pg) {
        const { KEY, MY_PAGE } = this;
        const cfg = globalThis.aggConfig;
        const d = [];
        const timeout = cfg.search.timeout;
        const wdLower = KEY.toLowerCase();

        const tasks = cfg.platformList.map(async (p) => {
            try {
                const plat = cfg.platform[p.id];
                let results = [];

                if (p.id === '七猫') {
                    const sign = await md5(`page=${MY_PAGE}wd=${KEY}${cfg.keys}`);
                    const url = `${plat.host}${plat.search}?page=${MY_PAGE}&wd=${encodeURIComponent(KEY)}&sign=${sign}`;
                    const headerX = await getHeaderX();
                    const res = JSON.parse(await request(url, { headers: { ...headerX, ...cfg.headers.default }, timeout }));
                    (res?.data?.list || []).forEach(i => {
                        results.push({ title: i.title, img: i.image_link, desc: buildSearchRemark('七猫短剧', i.total_num || i.total_episode_num || '', i.hot_value || ''), url: `七猫@${encodeURIComponent(i.id || i.playlet_id)}` });
                    });
                } else if (p.id === '星芽') {
                    const headers = this.xingya_headers || cfg.headers.default;
                    const res = JSON.parse(await request(plat.host + plat.search, { method: 'POST', headers, body: JSON.stringify({ text: KEY }), timeout }));
                    (res.data?.theater?.search_data || []).forEach(i => {
                        results.push({ title: i.title, img: i.cover_url, desc: buildSearchRemark('星芽短剧', i.total || i.current_num, i.play_amount_str || i.pv_str ? `播放:${i.play_amount_str || i.pv_str}` : ''), url: `星芽@${plat.host}${plat.url2}?theater_parent_id=${i.id}` });
                    });
                } else if (p.id === '西饭') {
                    const url = `${plat.host}${plat.search}?reqType=search&offset=${(MY_PAGE - 1) * 30}&keyword=${encodeURIComponent(KEY)}&quickEngineVersion=-1&scene=`;
                    const res = JSON.parse(await request(url, { timeout }));
                    const elements = Array.isArray(res?.result?.elements) ? res.result.elements : [];
                    const contents = elements.flatMap(el => Array.isArray(el?.contents) ? el.contents : [el]);
                    contents.forEach(vod => {
                        const dj = vod?.duanjuVo || vod || {};
                        if (!dj.duanjuId || !dj.title) return;
                        results.push({ title: dj.title, img: dj.coverImageUrl, desc: buildSearchRemark('西饭短剧', dj.total), url: `西饭@${dj.duanjuId}#${dj.source || ''}` });
                    });
                } else if (p.id === '围观') {
                    const clientInfo = await md5(String(Date.now()).slice(-10));
                    const url = `${plat.host}${plat.search}?version_code=1500&version_name=1.5.0&device_name=Pixel%208%20Pro&device_type=phone&is_first_day=true&is_first_24h=true&app_launch_way=icon&default_homepage=homepage_interaction&device_owning_firm=Google&font_scale=default&os_type=1&clientInfo=${clientInfo}`;
                    const res = JSON.parse(await request(url, {
                        method: 'POST',
                        headers: { 'User-Agent': 'okhttp/5.1.0', 'Content-Type': 'application/json; charset=utf-8' },
                        body: JSON.stringify({ audience: '', order: '', page: MY_PAGE, pageSize: 30, keyword: KEY, subject: '' }),
                        timeout
                    }));
                    (res?.data || []).forEach(i => {
                        results.push({ title: i.title, img: i.horzPoster || i.vertPoster, desc: buildSearchRemark('围观短剧', i.episodeCount || ''), url: `围观@${i.oneId}` });
                    });
                } else if (p.id === '河马') {
                    const res = JSON.parse(await request(`${plat.host}${plat.search}`, {
                        method: 'POST',
                        headers: getHemaApiHeaders(`${plat.host}/search?searchValue=${encodeURIComponent(KEY)}`),
                        body: JSON.stringify({ sourceType: 1, keyword: KEY, index: MY_PAGE }),
                        timeout
                    }));
                    const apiBookList = Array.isArray(res?.data?.bookList) ? res.data.bookList : [];
                    apiBookList.map(normalizeHemaSearchBook).filter(Boolean).forEach(v => {
                        results.push({ title: v.vod_name, img: v.vod_pic, desc: v.vod_remarks, url: v.vod_id });
                    });
                }
                return results;
            } catch (e) {
                log(`搜索失败（平台：${p.name}）：${e.message}`);
                return [];
            }
        });

        const settledResults = await Promise.allSettled(tasks);
        const flatResults = settledResults
            .filter(r => r.status === 'fulfilled')
            .flatMap(r => r.value)
            .map(item => ({ ...item, title: stripHtml(item.title) }));

        return setResult(rule.search_match ? flatResults.filter(i => (i.title || '').toLowerCase().includes(wdLower)) : flatResults);
    },

    lazy: async function (flag, id, flags) {
        const cfg = globalThis.aggConfig;

        if (/七猫/.test(flag)) {
            return { parse: 0, url: id };
        }

        if (/西饭/.test(flag)) {
            return { parse: 0, url: id };
        }

        if (/围观/.test(flag)) {
            try {
                const ps = JSON.parse(base64Decode(id));
                let urls = [];
                for (const item of ps || []) {
                    if (item?.name && item?.url) {
                        urls.push(item.name, item.url);
                    }
                }
                return { parse: 0, url: urls.length ? urls : id, headers: { 'User-Agent': 'okhttp/5.1.0' } };
            } catch (e) {
                return { parse: 0, url: id };
            }
        }

        if (/河马/.test(flag)) {
            if (/\.(mp4|m3u8)(\?|$)/i.test(id)) {
                return { parse: 0, url: id, header: getHemaHeaders() };
            }
            const parts = String(id || '').split('+');
            if (parts.length >= 2) {
                const [dramaId, chapterId] = parts;
                const episodeUrl = `${cfg.platform.河马.host}/episode/${dramaId}/${chapterId}`;
                const html = await request(episodeUrl, { headers: getHemaHeaders(episodeUrl) });
                const json = parseNextData(html);
                const videoInfo = json?.props?.pageProps?.chapterInfo?.chapterVideoVo || {};
                const videoUrl = videoInfo.mp4 || videoInfo.mp4720p || videoInfo.vodMp4Url || (String(html).match(/(https?:\/\/[^"']+\.mp4[^"']*)/) || [])[1] || '';
                return { parse: 0, url: videoUrl, header: getHemaHeaders() };
            }
            return { parse: 0, url: id, header: getHemaHeaders() };
        }

        return { parse: 0, url: id };
    }
};