"""
测试闲鱼搜索 API — 检查不同 pageSize 实际返回数量
"""
import requests
import json
import urllib3
import hashlib
import time
urllib3.disable_warnings()

GOOFISH_COOKIES_STR = 't=c02ad5127a543c333659ba69392d7737; cna=AA7EImro2hgCAXjjJNk5qlGy; tracknick=%E5%B0%8F%E6%97%B6258; unb=401943248; havana_lgc2_77=eyJoaWQiOjQwMTk0MzI0OCwic2ciOiIyZWM4OTE3ZTY4MzhjMjFhYTg2NWNjMzc3ZjAxMGQ2MiIsInNpdGUiOjc3LCJ0b2tlbiI6IjE3SEY3dTY2dFpNNHlEQnVidVdqZ0h3In0; _hvn_lgc_=77; havana_lgc_exp=1784983155114; isg=BBkZNkXZl7VFPUshiQuHk17fKAXzpg1YpvAu5zvOr8C_QjjUg_I_KbxRQA40eqWQ; xlly_s=1; cookie2=1a149c3e77334d6deba8cfb22431ce4d; _samesite_flag_=true; _tb_token_=e3eb51e7fbeff; sgcookie=E100igQs9V0plDfEIFOagdJa2llEVx3Fqb%2F5PAMSDKe5cxwnqK8YTWfgd1QgNlYrriUqHIDfOanVpdES1SJzQSxSGQZRnMRu8eo2Z1vKyAFGVeU%3D; csg=e1d13f89; sdkSilent=1782954144735; mtop_partitioned_detect=1; _m_h5_tk=3e2a8f0550866a3e53256f0f7ef91895_1782909541281; _m_h5_tk_enc=e067c75a1db2859ea6f720a8daa132db; tfstk=gsXjZvtT0q0XpCrYWqrzFm_OKhv15uyECctOxGHqXKpxWVIpzZ823l26WZYP3ES2Hmfl8MHV3SvZCKvMByzULJoVmdv9KmeAzEjRqhEyDEE_OxpMByzraAd0ddbVI7WyMgEWbhoxkNKx2gLkvFp9kC3-wHLJWdQ9k8dJvHux6nHteutMyFp9BNp8Vh8JWdpOWghAN2-_bEsbbbaaBKi9-iLSBABYnITC2fktBTtXG9SvPgSPFnOXJCRtZ86AzGBVnQVjMdjPON1OJzl2k6tCPB5bRx_CohI6XZwnAUBffTOcaqhvAKTX9tdjYYSB6_6W3tUitgSWkB9Pa742_K_fteAYZzb1VE7OhQ3bzF5F4td5Jzk5SC1O3LBYyJsz3v8QTNhsVBD6Ver7VfcGh6TwPfDFkKAvqn97VugXeIKkVeWaVfhWM3xXyuZSlMf..'

# 解析 cookies
from http.cookies import SimpleCookie
jar = requests.cookies.RequestsCookieJar()
cookie = SimpleCookie()
cookie.load(GOOFISH_COOKIES_STR)
for key, morsel in cookie.items():
    jar[key] = morsel.value

token = jar.get('_m_h5_tk', '').split('_')[0]
print(f'token: {token[:10]}...')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def get_timestamp():
    return str(int(time.time() * 1000))

def get_sign(token, timestamp, app_key, data_str):
    return hashlib.md5(f'{token}&{timestamp}&{app_key}&{data_str}'.encode()).hexdigest()

def search_page(keyword, page_no, page_size):
    payload = {
        'keyword': keyword,
        'pageNo': page_no,
        'pageSize': page_size,
        'searchFrom': 'search',
        'fluctuationUrl': '',
        'fluctuationData': '',
    }
    data_str = json.dumps(payload)
    ts = get_timestamp()
    sign = get_sign(token, ts, '34839810', data_str)

    params = {
        'jsv': '2.7.2', 'appKey': '34839810', 't': ts, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
        'dataType': 'json', 'timeout': '20000',
        'api': 'mtop.taobao.idlemtopsearch.pc.search',
        'sessionOption': 'AutoLoginOnly', 'spm_cnt': 'a21ybx.search.0.0',
        'spm_pre': 'a21ybx.search.searchInput.0'
    }

    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/'
    resp = requests.post(url, params=params, cookies=jar, headers=headers,
                        data={'data': data_str}, verify=False, timeout=30)
    
    if resp.status_code == 200:
        data = resp.json()
        outer = data.get('data', {})
        result_list = outer.get('resultList', [])
        return len(result_list)
    return 0

print("\n=== 测试不同 pageSize 实际返回数量 ===")
print("关键词: PPT模板\n")

# 测试 page 1 用不同 pageSize
for page_size in [10, 20, 30, 40, 50]:
    count = search_page('PPT模板', 1, page_size)
    print(f'  pageSize={page_size:>3} → 实际返回 {count} 条')
    time.sleep(0.3)

# 测试翻页
print("\n=== 测试翻页（pageSize=40）===")
total = 0
for p in range(1, 6):
    count = search_page('PPT模板', p, 40)
    print(f'  第 {p} 页: 返回 {count} 条')
    total += count
    if count == 0:
        break
    time.sleep(0.3)
print(f'  总计: {total} 条')
