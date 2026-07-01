"""
尝试不同的搜索 API 端点和分页策略，找到能获取全部结果的方法
"""
import requests, json, urllib3, hashlib, time
from http.cookies import SimpleCookie
urllib3.disable_warnings()

GOOFISH_COOKIES_STR = 't=c02ad5127a543c333659ba69392d7737; cna=AA7EImro2hgCAXjjJNk5qlGy; tracknick=%E5%B0%8F%E6%97%B6258; unb=401943248; havana_lgc2_77=eyJoaWQiOjQwMTk0MzI0OCwic2ciOiIyZWM4OTE3ZTY4MzhjMjFhYTg2NWNjMzc3ZjAxMGQ2MiIsInNpdGUiOjc3LCJ0b2tlbiI6IjE3SEY3dTY2dFpNNHlEQnVidVdqZ0h3In0; _hvn_lgc_=77; havana_lgc_exp=1784983155114; isg=BBkZNkXZl7VFPUshiQuHk17fKAXzpg1YpvAu5zvOr8C_QjjUg_I_KbxRQA40eqWQ; xlly_s=1; cookie2=1a149c3e77334d6deba8cfb22431ce4d; _samesite_flag_=true; _tb_token_=e3eb51e7fbeff; sgcookie=E100igQs9V0plDfEIFOagdJa2llEVx3Fqb%2F5PAMSDKe5cxwnqK8YTWfgd1QgNlYrriUqHIDfOanVpdES1SJzQSxSGQZRnMRu8eo2Z1vKyAFGVeU%3D; csg=e1d13f89; sdkSilent=1782954144735; mtop_partitioned_detect=1; _m_h5_tk=573eef29de45983e2fb7d602782e0563_1782917802637; _m_h5_tk_enc=af9f425a1f2f2b75cb7ba364e10e4ce6; x5sec=7b22733b32223a2262383537393665383933323438646434222c22617365727665723b33223a22307c435053666c4e4947454f376d36785161437a51774d546b304d7a49304f4473304d4b7170335a72342f2f2f2f2f77453d227d; tfstk=gXDZZwZ23dpw1RYo40228Cldu72TB-85uxabmmm0fP4GCO_mT40L5jG_5ilEo2F_SxoA3ommkhUXXBitX-eDPU62Fcn9DtsDgewDmD2b0OcmZzitX-IdAZAStcdqFS23j-00KWq_V-fGn5xUxozhIoXgmwxUDy2cIo2c-pq7qZq0mqmHYoU3o-VioJxUDy40n-cx6V3APuVMX47lt2TQf5zojyWr2vrgt1ng8tXmLfFarTaFntDUbmFZyDByGzc857aq-p6a3Dqq87GwzOuqm0h0Tx7Mf40ngqqK9E54zjmswjVejdmUQPPmd7SGgRlmWxPt_iK-xR0KwzFM9eEECYN4yW7HSDiUS7lq5eB05bon87MCRTwow2k4Z8jPRZE3NsDx_Zf4skEUPH-elvy8qjEYfI1AMWVuYztTisCYskBf_xtGMsF34kzWXWC..'

jar = requests.cookies.RequestsCookieJar()
cookie = SimpleCookie()
cookie.load(GOOFISH_COOKIES_STR)
for key, morsel in cookie.items():
    jar[key] = morsel.value
token = jar.get('_m_h5_tk', '').split('_')[0]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def call_api(api, payload, account_site='xianyu'):
    """通用 API 调用"""
    data_str = json.dumps(payload, ensure_ascii=False)
    ts = str(int(time.time() * 1000))
    sign = hashlib.md5(f'{token}&{ts}&34839810&{data_str}'.encode()).hexdigest()
    
    params = {
        'jsv': '2.7.2', 'appKey': '34839810', 't': ts, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': account_site,
        'dataType': 'json', 'timeout': '20000', 'api': api,
        'sessionOption': 'AutoLoginOnly',
    }
    
    url = f'https://h5api.m.goofish.com/h5/{api}/1.0/'
    resp = requests.post(url, params=params, cookies=jar, headers=headers,
                         data={'data': data_str}, verify=False,
                         proxies={'http': None, 'https': None}, timeout=30)
    
    if resp.status_code == 200:
        return resp.json()
    return None

def extract_ids(data):
    """从响应提取 item IDs"""
    ids = []
    outer = data.get('data', {})
    for item in outer.get('resultList', []):
        # 尝试多种路径
        aid = None
        try:
            aid = item.get('data', {}).get('item', {}).get('main', {}).get('clickParam', {}).get('args', {}).get('item_id', '')
        except:
            pass
        if not aid:
            try:
                aid = item.get('itemId', '') or item.get('id', '')
            except:
                pass
        if aid:
            ids.append(str(aid))
    return ids

# 方法1: 使用 search_id 翻页
print("=== 方法1: search_id 翻页 ===")
data1 = call_api('mtop.taobao.idlemtopsearch.pc.search', {
    'keyword': 'PPT模板', 'pageNo': 1, 'pageSize': 10,
    'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': '',
})
if data1:
    ids1 = extract_ids(data1)
    print(f"  page 1: {len(ids1)} 条")
    
    # 提取 search_id
    search_id = None
    outer = data1.get('data', {})
    for item in outer.get('resultList', []):
        try:
            sid = item.get('data', {}).get('item', {}).get('main', {}).get('clickParam', {}).get('args', {}).get('search_id', '')
            if sid: search_id = sid; break
        except:
            pass
    
    # 如果没有 search_id，生成一个随机 ID
    if not search_id:
        import uuid
        search_id = uuid.uuid4().hex
    print(f"  search_id: {search_id}")
    
    # 尝试带 search_id 翻页
    data2 = call_api('mtop.taobao.idlemtopsearch.pc.search', {
        'keyword': 'PPT模板', 'pageNo': 2, 'pageSize': 10,
        'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': '',
        'searchId': search_id,
    })
    if data2:
        ids2 = extract_ids(data2)
        overlap = set(ids1) & set(ids2)
        new = set(ids2) - set(ids1)
        print(f"  page 2 (with search_id): {len(ids2)} 条, 重复{len(overlap)}, 新{len(new)}")
time.sleep(0.3)

# 方法2: 使用手机H5搜索API
print("\n=== 方法2: 手机H5搜索API ===")
for api in [
    'mtop.taobao.idle.search',
    'mtop.taobao.idle.local.search',
    'mtop.taobao.idle.main.search',
    'mtop.taobao.idle.awesome.search',
]:
    data = call_api(api, {
        'keyword': 'PPT模板',
        'page': 1, 'pageSize': 20,
    })
    if data:
        ret = data.get('ret', [])
        if ret and 'FAIL' in str(ret[0]):
            print(f"  {api}: ❌ {ret[0]}")
        else:
            ids = extract_ids(data)
            print(f"  {api}: ✅ {len(ids)} 条")
    else:
        print(f"  {api}: ❌ no response")
    time.sleep(0.3)

# 方法3: PC API 快速翻页聚合（翻很多页取并集）
print("\n=== 方法3: PC API 快速翻页聚合 (20页) ===")
all_ids = set()
for p in range(1, 21):
    data = call_api('mtop.taobao.idlemtopsearch.pc.search', {
        'keyword': 'PPT模板', 'pageNo': p, 'pageSize': 10,
        'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': '',
    })
    if data:
        ret = data.get('ret', [])
        if ret and 'FAIL' in str(ret[0]):
            print(f"  page {p}: ❌ {ret[0]}")
            break
        new_ids = set(extract_ids(data))
        new_count = len(new_ids - all_ids)
        all_ids |= new_ids
        print(f"  page {p}: 返回{len(new_ids)}条, 新增{new_count}条, 累计{len(all_ids)}条")
        if new_count == 0:
            pass  # 继续尝试
    time.sleep(0.15)

print(f"\n  总计去重后: {len(all_ids)} 条")

# 方法4: 热门关键词测上限
print("\n=== 方法4: 热门关键词 (手机) 翻页聚合 ===")
all_ids2 = set()
for p in range(1, 21):
    data = call_api('mtop.taobao.idlemtopsearch.pc.search', {
        'keyword': '手机', 'pageNo': p, 'pageSize': 10,
        'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': '',
    })
    if data:
        ret = data.get('ret', [])
        if ret and 'FAIL' in str(ret[0]):
            break
        new_ids = set(extract_ids(data))
        new_count = len(new_ids - all_ids2)
        all_ids2 |= new_ids
        if p <= 10:
            print(f"  page {p}: 返回{len(new_ids)}条, 新增{new_count}条, 累计{len(all_ids2)}条")
    time.sleep(0.15)

print(f"  总计去重后: {len(all_ids2)} 条")
