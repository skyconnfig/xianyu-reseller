"""快速诊断 — API 是否正常"""
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

payload = {'keyword': 'PPT模板', 'pageNo': 1, 'pageSize': 10, 'searchFrom': 'search', 'fluctuationUrl': '', 'fluctuationData': ''}
data_str = json.dumps(payload, ensure_ascii=False)
ts = str(int(time.time() * 1000))
sign = hashlib.md5(f'{token}&{ts}&34839810&{data_str}'.encode()).hexdigest()

print(f"Token: {token}")
print(f"Timestamp: {ts}")
print(f"Sign: {sign}")
print(f"Data: {data_str}")
print()

params = {
    'jsv': '2.7.2', 'appKey': '34839810', 't': ts, 'sign': sign,
    'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
    'dataType': 'json', 'timeout': '20000',
    'api': 'mtop.taobao.idlemtopsearch.pc.search',
    'sessionOption': 'AutoLoginOnly',
    'spm_cnt': 'a21ybx.search.0.0', 'spm_pre': 'a21ybx.search.searchInput.0'
}

url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/'
resp = requests.post(url, params=params, cookies=jar, headers=headers,
                     data={'data': data_str}, verify=False,
                     proxies={'http': None, 'https': None}, timeout=30)

print(f'Status: {resp.status_code}')
data = resp.json()
print(f'Response keys: {list(data.keys())}')
print(f'ret: {data.get("ret")}')
outer = data.get('data', {})
print(f'data keys: {list(outer.keys())}')
rl = outer.get('resultList', [])
print(f'resultList count: {len(rl)}')

# Check if resultList items have proper structure
if rl:
    item = rl[0]
    print(f'First item keys: {list(item.keys())}')
    try:
        main = item['data']['item']['main']
        args = main['clickParam']['args']
        ex = main['exContent']
        print(f'  item_id: {args.get("item_id")}')
        print(f'  title: {ex.get("detailParams", {}).get("title", "")[:50]}')
        print(f'  picUrl: {ex.get("picUrl", "")[:50]}')
    except Exception as e:
        print(f'  parse error: {e}')
        print(json.dumps(item, ensure_ascii=False)[:500])
