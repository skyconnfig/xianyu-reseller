"""
测试闲鱼搜索 API — 调试版本，打印完整响应
"""
import requests
import json
import urllib3
import hashlib
import time
from http.cookies import SimpleCookie
urllib3.disable_warnings()

GOOFISH_COOKIES_STR = 't=c02ad5127a543c333659ba69392d7737; cna=AA7EImro2hgCAXjjJNk5qlGy; tracknick=%E5%B0%8F%E6%97%B6258; unb=401943248; havana_lgc2_77=eyJoaWQiOjQwMTk0MzI0OCwic2ciOiIyZWM4OTE3ZTY4MzhjMjFhYTg2NWNjMzc3ZjAxMGQ2MiIsInNpdGUiOjc3LCJ0b2tlbiI6IjE3SEY3dTY2dFpNNHlEQnVidVdqZ0h3In0; _hvn_lgc_=77; havana_lgc_exp=1784983155114; isg=BBkZNkXZl7VFPUshiQuHk17fKAXzpg1YpvAu5zvOr8C_QjjUg_I_KbxRQA40eqWQ; xlly_s=1; cookie2=1a149c3e77334d6deba8cfb22431ce4d; _samesite_flag_=true; _tb_token_=e3eb51e7fbeff; sgcookie=E100igQs9V0plDfEIFOagdJa2llEVx3Fqb%2F5PAMSDKe5cxwnqK8YTWfgd1QgNlYrriUqHIDfOanVpdES1SJzQSxSGQZRnMRu8eo2Z1vKyAFGVeU%3D; csg=e1d13f89; sdkSilent=1782954144735; mtop_partitioned_detect=1; _m_h5_tk=3e2a8f0550866a3e53256f0f7ef91895_1782909541281; _m_h5_tk_enc=e067c75a1db2859ea6f720a8daa132db; tfstk=gsXjZvtT0q0XpCrYWqrzFm_OKhv15uyECctOxGHqXKpxWVIpzZ823l26WZYP3ES2Hmfl8MHV3SvZCKvMByzULJoVmdv9KmeAzEjRqhEyDEE_OxpMByzraAd0ddbVI7WyMgEWbhoxkNKx2gLkvFp9kC3-wHLJWdQ9k8dJvHux6nHteutMyFp9BNp8Vh8JWdpOWghAN2-_bEsbbbaaBKi9-iLSBABYnITC2fktBTtXG9SvPgSPFnOXJCRtZ86AzGBVnQVjMdjPON1OJzl2k6tCPB5bRx_CohI6XZwnAUBffTOcaqhvAKTX9tdjYYSB6_6W3tUitgSWkB9Pa742_K_fteAYZzb1VE7OhQ3bzF5F4td5Jzk5SC1O3LBYyJsz3v8QTNhsVBD6Ver7VfcGh6TwPfDFkKAvqn97VugXeIKkVeWaVfhWM3xXyuZSlMf..'

# 解析 cookies
jar = requests.cookies.RequestsCookieJar()
cookie = SimpleCookie()
cookie.load(GOOFISH_COOKIES_STR)
for key, morsel in cookie.items():
    jar[key] = morsel.value

# 用 main.py 的方式解析 token
token = jar.get('_m_h5_tk', '').split('_')[0]
print(f'token from CookieJar: "{token}"')

# 直接用字符串解析 token
token2 = GOOFISH_COOKIES_STR.split('_m_h5_tk=')[1].split('_')[0] if '_m_h5_tk=' in GOOFISH_COOKIES_STR else 'N/A'
print(f'token from string: "{token2}"')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}

def get_timestamp():
    return str(int(time.time() * 1000))

def get_sign(token, timestamp, app_key, data_str):
    s = f'{token}&{timestamp}&{app_key}&{data_str}'
    return hashlib.md5(s.encode()).hexdigest()

payload = {
    'keyword': 'PPT模板',
    'pageNo': 1,
    'pageSize': 20,
    'searchFrom': 'search',
    'fluctuationUrl': '',
    'fluctuationData': '',
}
data_str = json.dumps(payload, ensure_ascii=False)
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

print(f'\n发送请求...')
print(f'URL: {url}')
print(f'Token: {token}')
print(f'Sign: {sign}')
print(f'Cookies: _m_h5_tk={jar.get("_m_h5_tk", "N/A")[:40]}...')

resp = requests.post(url, params=params, cookies=jar, headers=headers,
                    data={'data': data_str}, verify=False, timeout=30)

print(f'\n状态码: {resp.status_code}')
print(f'响应 (前2000字符):\n{resp.text[:2000]}')
