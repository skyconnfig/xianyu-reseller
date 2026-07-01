"""
用新 Cookie 测试闲鱼搜索 API — 验证翻页和全部数据抓取
"""
import requests
import json
import urllib3
import hashlib
import time
from http.cookies import SimpleCookie
urllib3.disable_warnings()

GOOFISH_COOKIES_STR = 't=c02ad5127a543c333659ba69392d7737; cna=AA7EImro2hgCAXjjJNk5qlGy; tracknick=%E5%B0%8F%E6%97%B6258; unb=401943248; havana_lgc2_77=eyJoaWQiOjQwMTk0MzI0OCwic2ciOiIyZWM4OTE3ZTY4MzhjMjFhYTg2NWNjMzc3ZjAxMGQ2MiIsInNpdGUiOjc3LCJ0b2tlbiI6IjE3SEY3dTY2dFpNNHlEQnVidVdqZ0h3In0; _hvn_lgc_=77; havana_lgc_exp=1784983155114; isg=BBkZNkXZl7VFPUshiQuHk17fKAXzpg1YpvAu5zvOr8C_QjjUg_I_KbxRQA40eqWQ; xlly_s=1; cookie2=1a149c3e77334d6deba8cfb22431ce4d; _samesite_flag_=true; _tb_token_=e3eb51e7fbeff; sgcookie=E100igQs9V0plDfEIFOagdJa2llEVx3Fqb%2F5PAMSDKe5cxwnqK8YTWfgd1QgNlYrriUqHIDfOanVpdES1SJzQSxSGQZRnMRu8eo2Z1vKyAFGVeU%3D; csg=e1d13f89; sdkSilent=1782954144735; mtop_partitioned_detect=1; _m_h5_tk=573eef29de45983e2fb7d602782e0563_1782917802637; _m_h5_tk_enc=af9f425a1f2f2b75cb7ba364e10e4ce6; x5sec=7b22733b32223a2262383537393665383933323438646434222c22617365727665723b33223a22307c435053666c4e4947454f376d36785161437a51774d546b304d7a49304f4473304d4b7170335a72342f2f2f2f2f77453d227d; tfstk=gXDZZwZ23dpw1RYo40228Cldu72TB-85uxabmmm0fP4GCO_mT40L5jG_5ilEo2F_SxoA3ommkhUXXBitX-eDPU62Fcn9DtsDgewDmD2b0OcmZzitX-IdAZAStcdqFS23j-00KWq_V-fGn5xUxozhIoXgmwxUDy2cIo2c-pq7qZq0mqmHYoU3o-VioJxUDy40n-cx6V3APuVMX47lt2TQf5zojyWr2vrgt1ng8tXmLfFarTaFntDUbmFZyDByGzc857aq-p6a3Dqq87GwzOuqm0h0Tx7Mf40ngqqK9E54zjmswjVejdmUQPPmd7SGgRlmWxPt_iK-xR0KwzFM9eEECYN4yW7HSDiUS7lq5eB05bon87MCRTwow2k4Z8jPRZE3NsDx_Zf4skEUPH-elvy8qjEYfI1AMWVuYztTisCYskBf_xtGMsF34kzWXWC..'

# 解析
jar = requests.cookies.RequestsCookieJar()
cookie = SimpleCookie()
cookie.load(GOOFISH_COOKIES_STR)
for key, morsel in cookie.items():
    jar[key] = morsel.value

token = jar.get('_m_h5_tk', '').split('_')[0]
print(f'_m_h5_tk token: {token}\n')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def search_page(keyword, page_no, page_size):
    payload = {
        'keyword': keyword,
        'pageNo': page_no,
        'pageSize': page_size,
        'searchFrom': 'search',
        'fluctuationUrl': '',
        'fluctuationData': '',
    }
    data_str = json.dumps(payload, ensure_ascii=False)
    ts = str(int(time.time() * 1000))
    s = f'{token}&{ts}&34839810&{data_str}'
    sign = hashlib.md5(s.encode()).hexdigest()

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
        data = resp.json()
        
        # 检查 ret 错误
        ret = data.get('ret', [])
        if ret and ('FAIL' in str(ret[0]) if ret else False):
            return None, f'API错误: {ret[0]}'
        
        outer = data.get('data', {})
        result_list = outer.get('resultList', [])
        return result_list, None
    return None, f'HTTP {resp.status_code}'

# 测试不同 pageSize
print("=== 1. 测试 pageSize 上限 ===")
print("关键词: PPT模板, 第1页\n")
best_size = None
for size in [10, 15, 20, 25, 30, 40]:
    result_list, err = search_page('PPT模板', 1, size)
    if err:
        print(f'  pageSize={size:>3} → ❌ {err}')
        if 'TOKEN' in err:
            print('  Cookie 过期，请更新！')
            exit(1)
    else:
        count = len(result_list) if result_list else 0
        print(f'  pageSize={size:>3} → 返回 {count} 条')
        if count > 0 and (best_size is None or count > best_size):
            best_size = count
    time.sleep(0.3)

print(f'\n  最佳 pageSize: {best_size}')

# 测试翻页
print("\n=== 2. 测试翻页 (pageSize=20) ===")
total = 0
seen_ids = set()
for p in range(1, 21):
    result_list, err = search_page('PPT模板', p, 20)
    if err:
        print(f'  第 {p} 页: ❌ {err}')
        break
    
    count = len(result_list) if result_list else 0
    if count == 0:
        print(f'  第 {p} 页: 空 (已达末尾)')
        break
    
    # 统计新商品
    new_count = 0
    for item in result_list:
        item_data = item.get('data', {}).get('item', {}).get('main', {})
        click_param = item_data.get('clickParam', {}).get('args', {})
        item_id = click_param.get('item_id', '') or click_param.get('id', '')
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            new_count += 1
    
    print(f'  第 {p} 页: 返回 {count} 条 (新增 {new_count} 条, 累计 {len(seen_ids)} 条)')
    total += count
    
    if new_count == 0 and count > 0:
        print(f'  ⚠️ 全部重复，已达末尾')
        break
    
    time.sleep(0.3)

print(f'\n  总计: {total} 条返回, 去重后 {len(seen_ids)} 条')
