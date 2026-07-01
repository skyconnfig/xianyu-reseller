"""
深入研究闲鱼 PC 搜索 API 的分页机制
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

def search(page_no, page_size, keyword='PPT模板', extra_payload={}):
    payload = {
        'keyword': keyword,
        'pageNo': page_no,
        'pageSize': page_size,
        'searchFrom': 'search',
        'fluctuationUrl': '',
        'fluctuationData': '',
        **extra_payload
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
        return resp.json()
    return None

# 打印完整 page 1 响应结构
print("=== 完整响应结构 (第1页) ===\n")
data = search(1, 10, 'PPT模板')
if data:
    # 打印顶层 keys
    print(f"顶层 keys: {list(data.keys())}")
    print(f"ret: {data.get('ret')}")
    
    outer = data.get('data', {})
    print(f"\ndata keys: {list(outer.keys()) if outer else 'EMPTY'}")
    
    # 检查所有顶层 data 字段
    for key in ['resultList', 'total', 'totalCount', 'hasMore', 'hasNext', 'nextPage', 'pageSize', 'pageNum', 'pages', 'items']:
        val = outer.get(key, 'N/A')
        if isinstance(val, list):
            print(f"  {key}: list[{len(val)}]")
        else:
            print(f"  {key}: {val}")
    
    # 打印第一条的完整结构
    result_list = outer.get('resultList', [])
    if result_list:
        print(f"\n第一条 item 结构:")
        first = result_list[0]
        
        # 递归打印 keys
        def print_keys(d, indent=0):
            if isinstance(d, dict):
                for k, v in d.items():
                    prefix = '  ' * indent
                    if isinstance(v, dict):
                        print(f"{prefix}{k}: {{...{len(v)} keys}}")
                        print_keys(v, indent + 1)
                    elif isinstance(v, list):
                        print(f"{prefix}{k}: [...{len(v)} items]")
                        if v and isinstance(v[0], dict):
                            print_keys(v[0], indent + 1)
                    else:
                        val_str = str(v)[:80]
                        print(f"{prefix}{k}: {val_str}")
        
        print_keys(first, 1)

# 尝试不同参数组合找分页方法
print("\n\n=== 尝试不同分页参数 ===\n")

# 尝试使用 page 而非 pageNo
for label, payload_extra in [
    ('page=1', {'page': 1}),
    ('page=2', {'page': 2}),
    ('pageNum=2', {'pageNum': 2}),
    ('start=10', {'start': 10, 'offset': 10}),
]:
    data = search(1, 10, 'PPT模板', {k: v for k, v in [('pageNo', 1), ('pageSize', 10)]} | payload_extra)
    if data:
        ret = data.get('ret', [])
        if ret:
            print(f"  {label}: ❌ {ret[0]}")
        else:
            result_list = data.get('data', {}).get('resultList', [])
            item_ids = set()
            for item in result_list:
                aid = item.get('data', {}).get('item', {}).get('main', {}).get('clickParam', {}).get('args', {}).get('item_id', '')
                if aid: item_ids.add(aid)
            print(f"  {label}: ✅ {len(result_list)} 条, IDs: {sorted(item_ids)[:5]}...")
    time.sleep(0.3)

# 尝试使用 fluctuationUrl/fluctuationData 翻页
print("\n=== 尝试 fluctuationUrl 分页 ===\n")
data1 = search(1, 10, 'PPT模板')
if data1:
    outer = data1.get('data', {})
    fluc_url = outer.get('fluctuationUrl', '')
    fluc_data = outer.get('fluctuationData', '')
    print(f"  fluctuationUrl: {fluc_url[:100] if fluc_url else 'EMPTY'}")
    print(f"  fluctuationData: {fluc_data[:100] if fluc_data else 'EMPTY'}")
    
    # 尝试用 fluctuationData 做第2页
    if fluc_data:
        data2 = search(2, 10, 'PPT模板', {'fluctuationData': fluc_data})
        if data2:
            ret = data2.get('ret', [])
            result_list2 = data2.get('data', {}).get('resultList', [])
            item_ids2 = set()
            for item in result_list2:
                aid = item.get('data', {}).get('item', {}).get('main', {}).get('clickParam', {}).get('args', {}).get('item_id', '')
                if aid: item_ids2.add(aid)
            if ret:
                print(f"  fluctuationData分页: ❌ {ret[0]}")
            else:
                print(f"  fluctuationData分页: {len(result_list2)} 条, IDs: {sorted(item_ids2)[:5]}...")
