"""
最终测试：确认 pageNo 翻页是否工作 + 检查 resultInfo
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

def search(page_no):
    payload = {
        'keyword': 'PPT模板',
        'pageNo': page_no,
        'pageSize': 10,
        'searchFrom': 'search',
        'fluctuationUrl': '',
        'fluctuationData': '',
    }
    data_str = json.dumps(payload, ensure_ascii=False)
    ts = str(int(time.time() * 1000))
    sign = hashlib.md5(f'{token}&{ts}&34839810&{data_str}'.encode()).hexdigest()
    
    params = {
        'jsv': '2.7.2', 'appKey': '34839810', 't': ts, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
        'dataType': 'json', 'timeout': '20000',
        'api': 'mtop.taobao.idlemtopsearch.pc.search',
        'sessionOption': 'AutoLoginOnly',
        'spm_cnt': 'a21ybx.search.0.0',
        'spm_pre': 'a21ybx.search.searchInput.0'
    }
    
    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/'
    resp = requests.post(url, params=params, cookies=jar, headers=headers,
                         data={'data': data_str}, verify=False,
                         proxies={'http': None, 'https': None}, timeout=30)
    
    if resp.status_code == 200:
        d = resp.json()
        
        # 打印 resultInfo
        outer = d.get('data', {})
        result_info = outer.get('resultInfo', {})
        
        # 提取 IDs
        ids = []
        for item in outer.get('resultList', []):
            aid = item.get('data', {}).get('item', {}).get('main', {}).get('clickParam', {}).get('args', {}).get('item_id', '')
            ids.append(aid)
        
        return {
            'ids': ids,
            'resultInfo': result_info,
            'ret': d.get('ret', []),
            'data_keys': list(outer.keys()),
        }
    return None

# 测试 pageNo=1, 2, 3, 4, 5 并比较
print("=== pageNo 翻页测试 ===\n")
pages_data = {}
for p in [1, 2, 3, 4, 5]:
    data = search(p)
    if data:
        pages_data[p] = data
        print(f"pageNo={p}: {len(data['ids'])} 条, IDs: {data['ids']}")
        
        # 打印 resultInfo
        ri = data.get('resultInfo', {})
        if ri:
            print(f"  resultInfo: total={ri.get('total')}, hasMore={ri.get('hasMore')}, pageSize={ri.get('pageSize')}")
        else:
            print(f"  resultInfo: EMPTY")
    time.sleep(0.3)

# 比较 overlap
print("\n=== ID 比较 ===")
p1_ids = set(pages_data.get(1, {}).get('ids', []))
for p in [2, 3, 4, 5]:
    pids = set(pages_data.get(p, {}).get('ids', []))
    overlap = p1_ids & pids
    new = pids - p1_ids
    print(f"  page 1 ∩ page {p}: {len(overlap)} 重复, {len(new)} 新")
    if new:
        print(f"    新 IDs: {new}")
