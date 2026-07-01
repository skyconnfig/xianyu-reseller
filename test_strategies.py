"""
策略5: 用不同搜索参数获取更多去重结果 — 综合策略
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

API = 'mtop.taobao.idlemtopsearch.pc.search'

def call_api(payload):
    data_str = json.dumps(payload, ensure_ascii=False)
    ts = str(int(time.time() * 1000))
    sign = hashlib.md5(f'{token}&{ts}&34839810&{data_str}'.encode()).hexdigest()
    
    params = {
        'jsv': '2.7.2', 'appKey': '34839810', 't': ts, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
        'dataType': 'json', 'timeout': '20000', 'api': API,
        'sessionOption': 'AutoLoginOnly',
    }
    url = f'https://h5api.m.goofish.com/h5/{API}/1.0/'
    resp = requests.post(url, params=params, cookies=jar, headers=headers,
                         data={'data': data_str}, verify=False,
                         proxies={'http': None, 'https': None}, timeout=30)
    
    if resp.status_code == 200:
        return resp.json()
    return None

def extract_all(data):
    items = []
    outer = data.get('data', {})
    for item in outer.get('resultList', []):
        try:
            main = item.get('data', {}).get('item', {}).get('main', {})
            args = main.get('clickParam', {}).get('args', {})
            ex = main.get('exContent', {})
            
            items.append({
                'item_id': str(args.get('item_id', '')),
                'price': ex.get('detailParams', {}).get('soldPrice', '0'),
                'title': ex.get('detailParams', {}).get('title', ''),
                'user_nick': ex.get('detailParams', {}).get('userNick', ''),
                'area': ex.get('area', ''),
                'want_count': int(args.get('wantNum', 0)) if str(args.get('wantNum', '0')).isdigit() else 0,
                'cCatId': str(args.get('cCatId', '')),
                'pic_url': ex.get('picUrl', ''),
            })
        except:
            pass
    return items

keyword = 'PPT模板'
all_items = {}  # item_id -> item

# 策略A: 不同 pageSize (API 可能会返回部分不同结果)
print("=== 策略A: 多 pageSize 聚合 ===")
for size in [10, 20, 30, 40, 50]:
    data = call_api({'keyword': keyword, 'pageNo': 1, 'pageSize': size, 'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': ''})
    if data:
        items = extract_all(data)
        new = 0
        for item in items:
            if item['item_id'] not in all_items:
                all_items[item['item_id']] = item
                new += 1
        print(f"  pageSize={size}: 返回{len(items)}条, 新增{new}条, 累计{len(all_items)}条")
    time.sleep(0.2)

# 策略B: 价格区间搜索
print("\n=== 策略B: 价格区间搜索 ===")
for price_range in [
    {'startPrice': '0', 'endPrice': '1'},
    {'startPrice': '1', 'endPrice': '5'},
    {'startPrice': '5', 'endPrice': '20'},
    {'startPrice': '20', 'endPrice': '100'},
]:
    payload = {'keyword': keyword, 'pageNo': 1, 'pageSize': 40, 'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': '', **price_range}
    data = call_api(payload)
    if data:
        items = extract_all(data)
        new = 0
        for item in items:
            if item['item_id'] not in all_items:
                all_items[item['item_id']] = item
                new += 1
        print(f"  {price_range}: 返回{len(items)}条, 新增{new}条, 累计{len(all_items)}条")
    time.sleep(0.2)

# 策略C: 多页翻页（pageNo 1-30，取并集）
print("\n=== 策略C: 多页遍历 ===")
for p in range(1, 31):
    data = call_api({'keyword': keyword, 'pageNo': p, 'pageSize': 40, 'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': ''})
    if data:
        items = extract_all(data)
        new = 0
        for item in items:
            if item['item_id'] not in all_items:
                all_items[item['item_id']] = item
                new += 1
        if p <= 5 or new > 0:
            print(f"  page {p}: 新增{new}条, 累计{len(all_items)}条")
    time.sleep(0.15)

print(f"\n{'='*50}")
print(f"最终结果: {len(all_items)} 条去重商品")
print(f"{'='*50}")
# 打印前10条
for i, (_, item) in enumerate(sorted(all_items.items(), key=lambda x: x[1]['price'])):
    if i < 10:
        print(f"  {item['price']}元 - {item['title'][:40]}... - {item['user_nick']}")
