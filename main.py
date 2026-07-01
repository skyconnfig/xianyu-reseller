"""
闲鱼转卖助手 2.0 - 完整版
根据 cest.pyc 反汇编结果重建（已完善）
"""

import re
import os
import sys
import time
import json
import glob
import csv
import hashlib
import warnings
import webbrowser
import threading
import queue
import traceback
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import imageio
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter.ttk import Style, Treeview

# 忽略 SSL 警告
warnings.filterwarnings('ignore')

# ==================== 全局变量定义 ====================

goofish_cookies = None
agiso_cookies = None
user_authorization = None

goofish_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}

# Agiso API headers (从反汇编恢复)
agiso_upload_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'sec-ch-ua-platform': '"Windows"',
    'Authorization': '',
    'x_front': '1',
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://aldsidle.agiso.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://aldsidle.agiso.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
}

agiso_publish_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua-platform': '"Windows"',
    'Authorization': '',
    'x_front': '1',
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json',
    'Origin': 'https://aldsidle.agiso.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://aldsidle.agiso.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'
}

# 数据列表
prices = []
titles = []
want_counts = []
item_ids = []
ccat_ids = []
urls = []
user_nicks = []
areas = []
pic_urls = []          # 搜索结果中的封面图URL（转卖备选）

# 标签持久引用（替代递归遍历查找）
_stats_label = None

# GUI 控件
tree = None
entry_keyword = None

# 发布相关全局变量
global_image_ids = []       # 图片ID列表
global_oss_keys = []        # OSS Key列表
global_agiso_img_urls = []  # Agiso图片URL列表
global_describe = ''        # 商品描述
province_code = '440000'    # 省份代码（默认东莞）
city_code = '441900'        # 城市代码（默认东莞）
district_code = ''          # 区代码

# ==================== 工具函数 ====================

def parse_cookies(cookie_str):
    """解析 cookies 字符串（自动清理首尾空白和换行）"""
    cookie_str = cookie_str.strip()
    try:
        cookies = {}
        for item in cookie_str.split(';'):
            item = item.strip()
            if '=' in item:
                k, v = item.split('=', 1)
                cookies[k.strip()] = v.strip()
        return cookies
    except ValueError:
        messagebox.showerror('错误', 'Cookie 格式错误！')
        return None

def get_current_timestamp_milliseconds():
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)

def get_md5_hash_string(input_str):
    """计算字符串的 MD5 哈希值"""
    hash_object = hashlib.md5()
    hash_object.update(input_str.encode('utf-8'))
    return hash_object.hexdigest()

def clear_lists():
    """清空列表"""
    global prices, titles, want_counts, item_ids, ccat_ids, urls, user_nicks, areas, pic_urls
    prices.clear()
    titles.clear()
    want_counts.clear()
    item_ids.clear()
    ccat_ids.clear()
    urls.clear()
    user_nicks.clear()
    areas.clear()
    pic_urls.clear()
    for row in tree.get_children():
        tree.delete(row)
    # 重置统计（使用持久化引用）
    if _stats_label:
        _stats_label.config(text="共 0 条商品 | 已选 0 条")

# ==================== Cookie 验证函数 ====================

def validate_xianyu_cookies(cookies):
    """验证闲鱼 cookies 是否有效"""
    test_url = 'https://www.goofish.com/'
    try:
        response = requests.get(test_url, cookies=cookies, headers=goofish_headers, timeout=10, verify=False,
                                proxies={'http': None, 'https': None})
        if 'login' not in response.url and response.status_code == 200:
            return True
        else:
            messagebox.showerror('错误', '闲鱼 Cookie 无效或已过期！')
            return False
    except Exception as e:
        messagebox.showerror('请求失败', f'验证闲鱼 Cookie 失败：{e}')
        return False

def validate_agiso_cookies(cookies, authorization):
    """验证 Agiso cookies + authorization 是否有效（从反汇编恢复的正确版本）"""
    url = 'https://aldsidle.agiso.com/api/User/GetUserInfo'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'Authorization': authorization.strip(),
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://aldsidle.agiso.com/'
    }
    try:
        response = requests.get(url, cookies=cookies, headers=headers, verify=False,
                                proxies={'http': None, 'https': None}, timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                # 检查返回数据是否包含有效用户信息
                if 'data' in data and data.get('data'):
                    return True
                else:
                    messagebox.showerror('错误', f'Agiso 返回无效数据: {data}')
                    return False
            except json.JSONDecodeError:
                # 如果不是 JSON 但状态码 200，也算通过
                return True
        else:
            messagebox.showerror('请求失败', f'Agiso 验证失败 (HTTP {response.status_code})：{response.text[:200]}')
            return False
    except Exception as e:
        messagebox.showerror('请求失败', f'验证 Agisco 失败：{e}')
        return False

def get_user_input(prompt, title):
    """获取用户输入（使用 tkinter 对话框，自动清理首尾空白）"""
    value = simpledialog.askstring(title, prompt)
    return value.strip() if value else ''

def get_and_validate_cookies():
    """获取并验证 cookies（三步流程：闲鱼Cookie → 阿奇索Cookie → Authorization）"""
    global goofish_cookies, agiso_cookies, user_authorization

    # 步骤1：获取闲鱼 Cookie
    xianyu_cookie_str = get_user_input('请输入闲鱼 Cookie：', '闲鱼 Cookie')
    if not xianyu_cookie_str:
        return
    xianyu_cookies = parse_cookies(xianyu_cookie_str)
    if not xianyu_cookies:
        return
    if not validate_xianyu_cookies(xianyu_cookies):
        return

    # 步骤2：获取阿奇索 Cookie
    agiso_cookie_str = get_user_input('请输入阿奇索 Cookie：', '阿奇索 Cookie')
    if not agiso_cookie_str:
        return
    agiso_cookies_local = parse_cookies(agiso_cookie_str)
    if not agiso_cookies_local:
        return

    # 步骤3：获取阿奇索 Authorization
    auth_str = get_user_input('阿奇索Authorization 数据:', 'Authorization 数据不能为空')
    if not auth_str or not auth_str.strip():
        messagebox.showerror('错误', 'Authorization 不能为空！')
        return

    # 验证 Agiso (cookies + authorization)
    if not validate_agiso_cookies(agiso_cookies_local, auth_str):
        return

    # 全部验证通过，保存到全局变量
    goofish_cookies = xianyu_cookies
    agiso_cookies = agiso_cookies_local
    user_authorization = auth_str.strip()

    # 更新 Agiso headers 中的 Authorization
    agiso_upload_headers['Authorization'] = user_authorization
    agiso_publish_headers['Authorization'] = user_authorization

    messagebox.showinfo('验证结果', '阿奇索 Cookie 和 Authorization 有效！')

# ==================== 核心功能函数 ====================

def build_payload(param1, param2):
    """构建 API 请求参数"""
    return {
        'keyword': param2,
        'pageNo': param1,
        'pageSize': 10,      # 闲鱼 PC 搜索 API 固定上限为 10，设多也无效
        'searchFrom': 'search',
        'fluctuationUrl': '',
        'fluctuationData': ''
    }

def _fetch_single_page(page_no, keyword):
    """抓取单页数据，返回 (result_list, error_msg)。
    result_list 为 None 表示出错，error_msg 含错误描述。"""
    if not keyword:
        return (None, '请输入有效的关键词')
    if not goofish_cookies:
        return (None, '请先验证Cookie！')

    token = goofish_cookies.get('_m_h5_tk', '').split('_')[0]
    if not token:
        return (None, 'Cookie中缺少token，请重新验证Cookie！')

    payload = build_payload(page_no, keyword)
    data_str = json.dumps(payload)

    timestamp = get_current_timestamp_milliseconds()
    app_key = '34839810'
    sign = get_md5_hash_string(f'{token}&{timestamp}&{app_key}&{data_str}')

    params = {
        'jsv': '2.7.2', 'appKey': app_key, 't': timestamp, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
        'dataType': 'json', 'timeout': '20000',
        'api': 'mtop.taobao.idlemtopsearch.pc.search',
        'sessionOption': 'AutoLoginOnly', 'spm_cnt': 'a21ybx.search.0.0',
        'spm_pre': 'a21ybx.search.searchInput.0'
    }

    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/'
    try:
        response = requests.post(
            url, params=params, cookies=goofish_cookies,
            headers=goofish_headers, data={'data': data_str},
            verify=False, timeout=30,
            proxies={'http': None, 'https': None}
        )
        if response.status_code != 200:
            return (None, f'请求失败：HTTP {response.status_code}')

        json_data = response.json()

        if 'ret' in json_data:
            ret_all = json_data['ret']
            ret_code = ret_all[0] if ret_all else ''
            
            # 令牌过期 → 需要重新验证
            if 'TOKEN' in ret_code.upper():
                return (None, '闲鱼Token已过期，请重新验证Cookie！')
            
            # 限流/被挤爆 → 可重试
            if 'RGV587' in str(ret_all) or '挤爆' in str(ret_all):
                return (None, 'RGV587_LIMIT')  # 特殊标记，上层可重试
            
            if 'FAIL' in ret_code or 'ERROR' in ret_code:
                return (None, f'API错误：{ret_code}')

        outer_data = json_data.get('data', {})
        if not outer_data:
            return ([], None)

        # 限流响应特征：data 只有 url/dialogSize，没有 resultList
        if 'resultList' not in outer_data and ('url' in outer_data or 'dialogSize' in outer_data):
            return (None, 'RGV587_LIMIT')
        
        return (outer_data.get('resultList', []), None)

    except requests.exceptions.Timeout:
        return (None, '请求超时，请检查网络连接')
    except requests.exceptions.RequestException as e:
        return (None, f'请求异常：{e}')
    except Exception as e:
        return (None, f'程序异常：{e}')


def _parse_item(item, seen_ids):
    """解析单条商品数据，返回 dict 或 None（已存在/无效）"""
    try:
        data = item.get('data', {})
        item_data = data.get('item', {})
        main_data = item_data.get('main', {})

        click_param = main_data.get('clickParam', {})
        args = click_param.get('args', {})

        ex_content = main_data.get('exContent', {})
        detail_params = ex_content.get('detailParams', {})

        title = detail_params.get('title', '')
        title = ' '.join(title.splitlines()).strip()
        if len(title) > 80:
            title = title[:78] + '…'

        user_nick = detail_params.get('userNick', '')
        price_str = detail_params.get('soldPrice', '0')
        area = ex_content.get('area', '') or args.get('p_city', '')
        want_count = int(args.get('wantNum', 0)) if str(args.get('wantNum', '0')).isdigit() else 0
        item_id = args.get('item_id', '') or args.get('id', '')
        ccat_id = args.get('cCatId', '')

        fish_tags = ex_content.get('fishTags', {})
        r3_list = fish_tags.get('r3', {}).get('tagList', []) if isinstance(fish_tags, dict) else []
        if want_count == 0 and r3_list:
            for tag in r3_list:
                m = re.search(r'(\d+)人想要', tag.get('data', {}).get('content', ''))
                if m:
                    want_count = int(m.group(1))
                    break

        try:
            price = float(price_str)
        except (ValueError, TypeError):
            price = 0

        if not item_id or item_id in seen_ids:
            return None

        return {
            'price': price, 'title': title, 'want_count': want_count,
            'item_id': item_id, 'ccat_id': ccat_id,
            'user_nick': user_nick, 'area': area,
            'url': f'https://www.goofish.com/item?id={item_id}',
            'pic_url': ex_content.get('picUrl', '')
        }
    except Exception as e:
        print(f"解析商品出错: {e}")
        return None


def fetch_data(keyword):
    """抓取全部数据 —— 智能翻页去重，直到无可获取的新商品"""
    global prices, titles, want_counts, item_ids, ccat_ids, urls, user_nicks, areas, pic_urls

    if not keyword:
        keyword = entry_keyword.get().strip()
    if not keyword:
        messagebox.showerror('错误', '请输入有效的关键词')
        return
    if not goofish_cookies:
        messagebox.showerror('错误', '请先验证Cookie！')
        return

    # 闲鱼 PC 搜索 API 特征（实测）:
    #  - 每页固定返回 10 条，pageSize 设多无效
    #  - pageNo 翻页高度重复，每 3-5 页才有少数新结果
    #  - 连续请求易触发"被挤爆啦"限流
    # 策略: 遍历 50 页，去重聚合，连续 5 页无新数据或限流时停止
    page_no = 1
    max_pages = 50
    total_new = 0
    zero_new_streak = 0       # 连续无新数据页数
    max_zero_streak = 5       # 连续 N 页无新数据则停止
    limit_retries = 0         # 限流重试计数
    max_limit_retries = 3     # 同页最多重试 3 次
    seen_ids = set(item_ids)

    pdlg = ProgressDialog(tree.winfo_toplevel(), '搜索中', f'正在搜索 "{keyword}"...', max_pages)

    try:
        while page_no <= max_pages:
            pdlg.update_progress(page_no, f'正在抓取第 {page_no} 页...')

            result_list, error = _fetch_single_page(page_no, keyword)
            
            if error:
                if error == 'RGV587_LIMIT':
                    limit_retries += 1
                    if limit_retries > max_limit_retries:
                        print(f'  [搜索] 连续 {max_limit_retries} 次被限流，停止搜索')
                        break
                    print(f'  [搜索] 第 {page_no} 页被限流 (重试 {limit_retries}/{max_limit_retries})，等待 5 秒...')
                    pdlg.update_progress(page_no, f'被限流，等待中({limit_retries}/{max_limit_retries})...')
                    time.sleep(5)
                    continue  # 重试同页
                else:
                    # 令牌过期或其他致命错误
                    pdlg.destroy()
                    messagebox.showerror('错误', error)
                    return

            if not result_list:
                break  # 无更多数据

            page_added = 0
            for item in result_list:
                parsed = _parse_item(item, seen_ids)
                if parsed is None:
                    continue

                seen_ids.add(parsed['item_id'])
                prices.append(parsed['price'])
                titles.append(parsed['title'])
                want_counts.append(parsed['want_count'])
                item_ids.append(parsed['item_id'])
                ccat_ids.append(parsed['ccat_id'])
                urls.append(parsed['url'])
                user_nicks.append(parsed['user_nick'])
                areas.append(parsed['area'])
                pic_urls.append(parsed['pic_url'])

                tree.insert('', 'end', values=(
                    parsed['price'], parsed['title'], parsed['want_count'],
                    parsed['item_id'], parsed['ccat_id'],
                    parsed['user_nick'], parsed['area']
                ))
                page_added += 1

            total_new += page_added
            
            if page_added == 0:
                zero_new_streak += 1
                if zero_new_streak >= max_zero_streak:
                    print(f'  连续 {zero_new_streak} 页无新数据，停止搜索')
                    break
            else:
                zero_new_streak = 0
            
            print(f'第 {page_no} 页: 新增 {page_added} 条（累计 {total_new} 条）')
            page_no += 1
            time.sleep(0.5)  # 节流，避免触发限流

        pdlg.destroy()

        if total_new == 0:
            messagebox.showinfo('提示', '未找到相关商品')
        else:
            messagebox.showinfo('完成', f'搜索完成！共找到 {total_new} 条商品（总计 {len(item_ids)} 条）')

    except Exception as e:
        try:
            pdlg.destroy()
        except:
            pass
        messagebox.showerror('错误', f'抓取异常：{e}')
        import traceback
        traceback.print_exc()

    _update_page_stats()

def download_images(image_urls):
    """下载图片（多线程）"""
    import os
    
    def download_single_image(url):
        """下载单张图片"""
        try:
            response = requests.get(
                url,
                stream=True,
                timeout=30,
                verify=False,
                cookies=goofish_cookies,
                headers=goofish_headers,
                proxies={'http': None, 'https': None}
            )
            if response.status_code == 200:
                # 保存图片
                if not os.path.exists('images'):
                    os.makedirs('images')
                filename = f"image_{int(time.time())}_{len(os.listdir('images'))}.jpg"
                filepath = os.path.join('images', filename)
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                return filepath
        except Exception as e:
            print(f"下载图片失败: {e}")
            return None
    
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_single_image, url) for url in image_urls]
        for future in as_completed(futures):
            result = future.result()
            if result:  # 过滤掉失败的请求
                results.append(result)
    
    return results

def open_url():
    """打开 URL"""
    selected_item = tree.selection()
    
    if not selected_item:
        messagebox.showerror('错误', '请先选择一个商品！')
        return
    
    url = urls[tree.index(selected_item[0])]
    
    if url and url != 'Error：url':
        webbrowser.open(url)
        return
    
    messagebox.showerror('错误', '无法打开链接！')

# ==================== 配置管理函数 ====================

def save_config():
    """保存配置文件"""
    if not goofish_cookies:
        messagebox.showerror('错误', '没有Cookie可以保存！')
        return
    
    try:
        config_file = 'config.json'
        
        # 构建配置数据
        config = {
            'cookies': '; '.join([f'{k}={v}' for k, v in goofish_cookies.items()]),
            'headers': goofish_headers,
            'last_keyword': entry_keyword.get().strip() if entry_keyword else '',
            'save_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        messagebox.showinfo('成功', f'配置已保存到：{config_file}')
    except Exception as e:
        messagebox.showerror('错误', f'保存配置失败：{e}')

# ==================== 一键转卖功能（发布相关） ====================

def download_file(url, filename=None):
    """下载文件到临时目录"""
    try:
        print(f'  [下载] URL: {url[:100]}...')

        response = requests.get(
            url, stream=True, timeout=30, verify=False,
            cookies=goofish_cookies, headers=goofish_headers,
            proxies={'http': None, 'https': None}
        )

        print(f'  [下载] 状态码: {response.status_code}, Content-Length: {response.headers.get("Content-Length", "unknown")}')
        response.raise_for_status()

        if not filename:
            filename = f"img_{int(time.time())}.jpg"

        # 统一保存到 temp_img 目录（与转换函数同目录）
        save_dir = os.path.join(os.getcwd(), 'temp_img')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, filename)

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f'  [下载] 已保存: {save_path} ({os.path.getsize(save_path)} bytes)')
        return save_path
    except requests.exceptions.RequestException as e:
        print(f'  [下载] 失败: {e}')
        return None

def convert_images_to_png_in_directory():
    """将 temp_img 目录中的图片转换为PNG格式"""
    img_dir = os.path.join(os.getcwd(), 'temp_img')
    supported_extensions = ('.heic', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')

    if not os.path.exists(img_dir):
        print('  [转换] temp_img 不存在，跳过')
        return

    converted_count = 0
    try:
        for filename in os.listdir(img_dir):
            if filename.lower().endswith(supported_extensions) and not filename.lower().endswith('.png'):
                source_path = os.path.join(img_dir, filename)
                try:
                    image = imageio.imread(source_path)
                    base_name, _ = os.path.splitext(filename)
                    png_filename = f'{base_name}.png'
                    png_path = os.path.join(img_dir, png_filename)
                    imageio.imwrite(png_path, image)
                    os.remove(source_path)
                    converted_count += 1
                except Exception as e:
                    print(f'  [转换] 文件错误 {filename}: {e}')
    except Exception as e:
        print(f'  [转换] 过程出错: {e}')
    if converted_count:
        print(f'  [转换] 转换了 {converted_count} 个文件为 PNG')

def find_png_files_without_extension():
    """查找 temp_img 目录中的所有 PNG 文件"""
    png_paths = []
    base_names = []
    img_dir = os.path.join(os.getcwd(), 'temp_img')

    if not os.path.exists(img_dir):
        print('  [查找PNG] temp_img 不存在')
        return base_names, png_paths

    try:
        for filename in os.listdir(img_dir):
            if filename.lower().endswith('.png'):
                filepath = os.path.join(img_dir, filename)
                png_paths.append(filepath)
                base_names.append(os.path.splitext(filename)[0])
    except Exception as e:
        print(f'  [查找PNG] 出错: {e}')

    print(f'  [查找PNG] 找到 {len(png_paths)} 个 PNG: {[os.path.basename(p) for p in png_paths]}')
    return base_names, png_paths

def delete_png_files_recursively():
    """清理 temp_img 临时目录"""
    img_dir = os.path.join(os.getcwd(), 'temp_img')
    try:
        if os.path.exists(img_dir):
            count = 0
            for filename in os.listdir(img_dir):
                filepath = os.path.join(img_dir, filename)
                try:
                    os.remove(filepath)
                    count += 1
                except Exception:
                    pass
            try:
                os.rmdir(img_dir)
            except Exception:
                pass
            if count:
                print(f'  [清理] 删除了 {count} 个临时文件')
    except Exception as e:
        print(f'  [清理] 出错: {e}')

def upload_file(file_path):
    """上传文件到Agiso服务器"""
    global global_image_ids, global_oss_keys, global_agiso_img_urls

    url = 'https://aldsidle.agiso.com/api/GoodsManage/MediaUpload'
    file_name = os.path.basename(file_path)

    print(f'  [上传] 文件: {file_name} ({os.path.getsize(file_path)} bytes)')
    
    # 检查 Agiso 认证是否就绪
    if not agiso_cookies:
        print(f'  [上传] 错误: 阿奇索 Cookie 未设置！')
        return False
    if not user_authorization:
        print(f'  [上传] 错误: Authorization 未设置！')
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (file_name, f, 'image/png')}
            response = requests.post(
                url,
                cookies=agiso_cookies,
                headers=agiso_upload_headers,
                files=files,
                verify=False,
                proxies={'http': None, 'https': None}
            )
        
        print(f'  [上传] 状态码: {response.status_code}, 响应: {response.text[:500]}')
        
        if response.status_code == 200:
            response_data = response.json()
            # 始终保存完整响应到日志文件
            try:
                log_dir = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(log_dir, 'upload_response.log'), 'a', encoding='utf-8') as uf:
                    uf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {file_name}\n')
                    uf.write(json.dumps(response_data, ensure_ascii=False) + '\n\n')
            except:
                pass
            print(f'  [上传] 完整JSON: {json.dumps(response_data, ensure_ascii=False)[:500]}')
            if response_data.get('succeeded') or response_data.get('isSuccess'):
                # Agiso 新版 API: data 嵌套了一层 data.data
                raw_data = response_data.get('data', {})
                data = raw_data.get('data', raw_data)  # 兼容新旧两种结构
                image_id = data.get('imageId', '')
                oss_key = data.get('ossKey', '')
                agiso_url = data.get('agisoImgUrl', '')
                if not image_id:
                    print(f'  [上传] ⚠️ 响应中无 imageId！raw_data keys: {list(raw_data.keys()) if raw_data else "[]"}, nested keys: {list(data.keys()) if data else "[]"}')
                    return False  # 无有效 imageId，视为失败
                global_image_ids.append(image_id)
                global_oss_keys.append(oss_key)
                global_agiso_img_urls.append(agiso_url)
                print(f'  [上传] 成功! imageId={image_id}, ossKey={oss_key[:20] if oss_key else ""}...')
                return True
            else:
                print(f'  [上传] API 返回失败: {response_data.get("message", "unknown")}')
                return False
        else:
            print(f'  [上传] HTTP 错误: {response.status_code}')
            return False
    except Exception as e:
        print(f'  [上传] 异常: {e}')
        return False

class ProgressDialog:
    """进度对话框"""
    def __init__(self, parent, title, message, maximum):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry('300x150')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        self.dialog.geometry(f'+{x}+{y}')
        
        self.label = ttk.Label(self.dialog, text=message)
        self.label.pack(pady=10)
        
        self.progress = ttk.Progressbar(self.dialog, orient='horizontal',
                                         length=250, mode='determinate', maximum=maximum)
        self.progress.pack(pady=10)
        
        self.percent_label = ttk.Label(self.dialog, text='0%')
        self.percent_label.pack()
        
        self.dialog.protocol('WM_DELETE_WINDOW', lambda: None)
    
    def update_progress(self, value, message=None):
        self.progress['value'] = value
        max_val = self.progress['maximum']
        percent = int((value / max_val) * 100) if max_val > 0 else 0
        self.percent_label.config(text=f'{percent}%')
        if message:
            self.label.config(text=message)
        self.dialog.update()
    
    def destroy(self):
        try:
            self.dialog.destroy()
        except:
            pass

def process_images_with_progress(img_urls):
    """带进度条的图片处理与上传"""
    global global_image_ids, global_oss_keys, global_agiso_img_urls
    
    global_image_ids.clear()
    global_oss_keys.clear()
    global_agiso_img_urls.clear()
    
    # 创建进度对话框
    progress_dialog = ProgressDialog(tree.winfo_toplevel(), '图片处理',
                                      '正在处理图片...', len(img_urls) * 3)
    
    def process_step():
        total = len(img_urls)
        for i, img_url in enumerate(img_urls):
            msg = f'正在处理第 {i + 1}/{total} 张图片'
            progress_dialog.update_progress(i * 3 + 1, msg)
            print(f'处理图片: {img_url}')
            
            # 下载图片
            filepath = download_file(img_url)
            if not filepath:
                print(f'下载失败: {img_url}')
                continue
            
            # 转换为PNG
            convert_images_to_png_in_directory()
            
            # 查找并上传PNG文件
            png_names, png_paths = find_png_files_without_extension()
            for png_path in png_paths:
                progress_dialog.update_progress(i * 3 + 2, f'正在上传第 {i + 1} 张图片...')
                upload_file(png_path)
            
            # 清理临时文件
            delete_png_files_recursively()
        
        progress_dialog.update_progress(len(img_urls) * 3, '图片处理完成，准备发布...')
        
        # 执行发布
        publish()
        
        # 关闭进度对话框
        try:
            progress_dialog.destroy()
        except:
            pass
    
    threading.Thread(target=process_step, daemon=True).start()

def print_selected_row_info():
    """获取选中商品详情，提取图片和描述，启动转卖流程"""
    global global_describe

    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning('警告', '请先选择一行数据')
        return
    
    item_values = tree.item(selected_item, 'values')
    idx = tree.index(selected_item[0])
    item_id = item_ids[idx]
    
    print('———— 一键转卖 ————')
    print(f'商品ID: {item_id}')
    print(f'价格: {prices[idx]}')
    print(f'URL: {urls[idx]}')
    
    # 获取搜索结果中的 picUrl（作为备选图片源）
    fallback_img_url = pic_urls[idx] if idx < len(pic_urls) else ''
    
    img_urls = []
    describe_text = titles[idx] if idx < len(titles) else ''
    
    # 尝试调用详情API获取完整图片列表和描述
    detail_data = {"itemId": str(item_id)}
    detail_data_str = json.dumps(detail_data)
    
    token = goofish_cookies.get('_m_h5_tk', '').split('_')[0]
    if not token:
        messagebox.showerror('错误', 'Cookie中缺少token')
        return
    
    timestamp = get_current_timestamp_milliseconds()
    app_key = '34839810'
    sign = get_md5_hash_string(f'{token}&{timestamp}&{app_key}&{detail_data_str}')
    
    params = {
        'jsv': '2.7.2', 'appKey': app_key, 't': timestamp, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
        'dataType': 'json', 'timeout': '20000',
        'api': 'mtop.taobao.idle.pc.detail',
        'sessionOption': 'AutoLoginOnly', 'spm_cnt': 'a21ybx.item.0.0'
    }
    
    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/'
    
    try:
        response = requests.post(
            url, params=params, cookies=goofish_cookies,
            headers=goofish_headers, data={'data': detail_data_str},
            verify=False, timeout=30,
            proxies={'http': None, 'https': None}
        )
        
        if response.status_code == 200:
            detail_json = response.json()
            
            # 检查API是否成功
            ret_code = detail_json.get('ret', [''])[0] if detail_json.get('ret') else ''
            
            if 'SUCCESS' in ret_code:
                # 成功：从详情文本中解析图片
                text = detail_json.get('data', {}).get('item', {}).get('main', {}).get('text', '')
                
                image_compile = re.compile(r'"\\"image\\":\\"(?P<imgUrl>.*?)\\",\\"width\\":\\"', re.S)
                img_urls = [img.group('imgUrl') for img in image_compile.finditer(text)]
                
                # 提取描述
                describe_compile = re.compile(r'"},\\"mainParams\\":{\\"content\\":\\"(?P<describe>.*?)\\",\\"', re.S)
                result_describe = describe_compile.search(text)
                if result_describe:
                    describe_text = result_describe.group('describe')
                    
                    # 清理描述中的特殊字符
                    describe_text = describe_text.replace('\\n', '\n').replace('\\r', '')
                
                print(f'详情API找到 {len(img_urls)} 张图片')
                print(f'商品描述: {describe_text[:100]}...')
            else:
                # API返回失败但不是网络错误（如 FAIL_SYS_USER_VALIDATE）
                print(f'详情API返回: {ret_code} — 使用备选方案获取图片')
        
    except Exception as e:
        print(f'详情API请求异常: {e}')
    
    # 备选方案：如果详情API没拿到图片，使用搜索结果中的picUrl
    if not img_urls and fallback_img_url:
        img_urls = [fallback_img_url]
        print(f'使用搜索结果中的封面图: {fallback_img_url[:80]}...')
    
    if not img_urls:
        # 最终备选：尝试用商品ID构造图片URL
        # 闲鱼图片URL模式: https://gw.alicdn.com/bao/uploaded/...
        messagebox.showwarning('提示', 
            f'未获取到商品图片。\n\n'
            f'可能原因:\n'
            f'• Cookie 权限不足（详情API返回验证失败）\n'
            f'• 商品已下架或删除\n\n'
            f'建议：\n'
            f'• 更新闲鱼 Cookie 后重试\n'
            f'• 或手动打开商品页面确认是否有效')
        return
    
    # 设置全局描述
    global_describe = describe_text
    print(f'最终使用 {len(img_urls)} 张图片进行转卖')
    print(f'商品描述: {global_describe[:100]}...')
    
    # 开始处理图片和发布
    process_images_with_progress(img_urls)

def _do_publish(item_values, silent=False):
    """
    核心发布逻辑（原版 complete_process 调用链）：
      publish()   → 发布到阿奇索 → 闲鱼上架
      save_good() → 收藏原商品到闲鱼收藏夹
      delete_png()→ 清理临时文件
    
    silent=True 时不弹 messagebox，供批量模式调用；返回 True/False 表示成功与否。
    """
    global province_code, city_code, district_code

    # 确定日志目录（使用脚本所在目录）
    log_dir = os.path.dirname(os.path.abspath(__file__))

    # 立即写入入口标记（确认函数被调用）
    try:
        with open(os.path.join(log_dir, 'publish_entry.log'), 'a', encoding='utf-8') as pf:
            pf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] _do_publish called, silent={silent}, images={len(global_image_ids)}, desc_len={len(global_describe)}\n')
    except:
        pass

    # 全函数 try/except —— 任何异常都写文件
    try:
        return _do_publish_impl(item_values, silent, log_dir)
    except Exception as fatal_err:
        err_file = os.path.join(log_dir, 'publish_fatal.log')
        with open(err_file, 'a', encoding='utf-8') as ef:
            ef.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] FATAL 异常: {fatal_err}\n')
            ef.write(traceback.format_exc() + '\n\n')
        print(f'[Agiso Publish] FATAL: {fatal_err}')
        traceback.print_exc()
        if not silent:
            messagebox.showerror('发布失败', f'发布失败（致命错误）:\n{fatal_err}\n\n详情已写入 publish_fatal.log')
        return False


def _do_publish_impl(item_values, silent, log_dir):
    """_do_publish 的实际实现体"""
    print(f'图片ID列表: {global_image_ids}')
    print(f'OSS Keys: {global_oss_keys}')
    print(f'图片URL列表: {global_agiso_img_urls}')
    print(f'商品描述: {global_describe[:100]}...')
    print(f'地区代码: {province_code}, {city_code}, {district_code}')

    # 保存状态到日志
    try:
        with open(os.path.join(log_dir, 'publish_state.log'), 'a', encoding='utf-8') as sf:
            sf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] global_image_ids={global_image_ids}\n')
            sf.write(f'  global_agiso_img_urls={global_agiso_img_urls}\n')
            sf.write(f'  global_oss_keys={global_oss_keys}\n\n')
    except:
        pass

    # 构建图片列表
    # Agiso API 字段名: 'imgList'（原版反汇编字段名，实测 API 只接受这个）
    # 值为对象列表: [{'imageId': 'xxx', 'agisoImgUrl': 'yyy', 'ossKey': 'zzz'}, ...]
    # 最大数量限制约 9 张
    max_images = 9
    
    # 过滤空值 imageId（上传失败时可能产生）
    valid_ids = [iid for iid in global_image_ids if iid]
    valid_urls = [u for i, u in enumerate(global_agiso_img_urls) if i < len(valid_ids)]
    valid_oss = [o for i, o in enumerate(global_oss_keys) if i < len(valid_ids)]

    if len(valid_ids) > max_images:
        print(f'  [发布] 图片数量 {len(valid_ids)} 超过限制 {max_images}，截取前 {max_images} 张')
    
    if not valid_ids or not valid_ids[0]:
        if not silent:
            messagebox.showerror('错误', '没有有效的已上传图片！请先获取商品图片。')
        return False

    # 构建图片列表对象
    # ⚠️ 关键: 字段名必须是 'imgList'（不是 'imagesList'）
    #   实测 Agiso API 只接受 'imgList'，用 'imagesList' 会报 "图片列表数据有误"
    #   imageId 保持 string 类型（避免大整数精度丢失）
    #   agisoImgUrl 保持上传 API 返回的原始值（含 ?x-oss-process=... 参数）
    
    images_list_data = [
        {
            'imageId': str(valid_ids[i]),
            'agisoImgUrl': str(valid_urls[i]) if i < len(valid_urls) else '',
            'ossKey': str(valid_oss[i]) if i < len(valid_oss) else ''
        }
        for i in range(min(len(valid_ids), max_images))
    ]

    print(f'  [发布] imgList 数据 ({len(images_list_data)} 项):')
    for idx, item in enumerate(images_list_data):
        print(f'    [{idx}] imageId={item["imageId"]} (type={type(item["imageId"]).__name__}), url_len={len(item["agisoImgUrl"])}')

    # 提取价格和标题（列顺序: 0=价格, 1=标题, ...）
    # 原版 price 从 item_values[1].replace('¥', '').strip() 取，是字符串类型
    # 原版用 float(price) 仅校验，API 仍发送原始字符串
    price_str = str(item_values[0]) if len(item_values) > 0 else '0'
    try:
        float(price_str)  # 仅校验格式有效
    except (ValueError, TypeError):
        price_str = '0'
    title_text = str(item_values[1]) if len(item_values) > 1 else ''

    # 构建地区列表
    division_list = [province_code, city_code]
    if district_code:
        division_list.append(district_code)

    # 构建发布参数
    payload = {
        'itemBizType': 2,
        'goodsType': [99, 'eebfcb1cd9bfce8e212e21d79c0262e7',
                      'eebfcb1cd9bfce8e212e21d79c0262e7',
                      '3cdbae6d47df9251a7f7e02f36b0b49a'],
        'spBizType': '99',
        'categoryId': 50023914,
        'channelCatId': '3cdbae6d47df9251a7f7e02f36b0b49a',
        'pvList': [],
        'virtual': False,
        'title': title_text[:30],
        'desc': global_describe.replace('\\\\n', '\n') if global_describe else '',
        'divisionIdList': division_list,
        'freeShipping': True,
        'reservePrice': price_str,
        'originalPrice': 0,
        'quantity': 9999,
        'stuffStatus': 0,
        'transportFee': 0,
        'itemSkuList': [],
        'categoryName': '其他/电子资料/电子资料/电子资料',
        'imgList': images_list_data
    }

    payload_str = json.dumps(payload, ensure_ascii=False)
    print(f'\n请求体: {payload_str[:1000]}...')

    # 保存请求到绝对路径，确保能找到
    req_dump_path = os.path.join(log_dir, 'publish_request_dump.json')
    resp_dump_path = os.path.join(log_dir, 'publish_response_dump.json')
    err_log_path = os.path.join(log_dir, 'publish_error.log')

    try:
        with open(req_dump_path, 'w', encoding='utf-8') as df:
            json.dump({
                'url': 'https://aldsidle.agiso.com/api/GoodsManage/Publish',
                'content_type': agiso_publish_headers.get('Content-Type', 'unknown'),
                'payload': {k: (v if k != 'imgList' else json.loads(json.dumps(images_list_data, ensure_ascii=False))) for k, v in payload.items()},
                'imgList_full': json.loads(json.dumps(images_list_data, ensure_ascii=False)),
            }, df, ensure_ascii=False, indent=2)
        print(f'[Agiso Publish] 请求已保存到: {req_dump_path}')
    except Exception as dump_err:
        print(f'[Agiso Publish] ⚠️ 保存请求失败: {dump_err}')

    url = 'https://aldsidle.agiso.com/api/GoodsManage/Publish'
    print(f'[Agiso Publish] → 发送到 {url}')

    try:
        response = requests.post(
            url, cookies=agiso_cookies, headers=agiso_publish_headers,
            data=payload_str, verify=False, timeout=30,
            proxies={'http': None, 'https': None}
        )

        print(f'状态码: {response.status_code}')

        # 保存完整响应用于调试
        try:
            with open(resp_dump_path, 'w', encoding='utf-8') as rf:
                rf.write(response.text[:5000])
            print(f'[Agiso Publish] 响应已保存到: {resp_dump_path}')
        except Exception as dump_err:
            print(f'[Agiso Publish] ⚠️ 保存响应失败: {dump_err}')

        if response.status_code == 200:
            response_data = response.json()
            print(f'\n[Agiso Publish] 完整响应: {json.dumps(response_data, ensure_ascii=False)}')
            # Agiso 响应结构: {"succeeded": true, "data": {"isSuccess": true/false, ...}}
            # 注意: 顶层 "succeeded" 仅表示 HTTP 请求成功，不代表发布成功
            # 真正决定发布成败的是 data.isSuccess
            data_field = response_data.get('data', {})
            publish_success = data_field.get('isSuccess', False) or response_data.get('isSuccess')
            
            if publish_success:
                print(f'[Agiso Publish] ✅ 发布成功')
                if not silent:
                    messagebox.showinfo('成功', '商品已成功发布上架！')
                # ① 收藏原商品到闲鱼收藏夹（原版 complete_process 调用链）
                save_good()
                # ② 清理临时文件
                delete_png_files_recursively()
                return True
            else:
                error_msg = data_field.get('errorMsg', '') or response_data.get('message', response_data.get('msg', '未知错误'))
                print(f'[Agiso Publish] ❌ 失败: {error_msg}')
                print(f'[Agiso Publish] 完整响应: {response.text[:2000]}')
                # 写入日志文件
                try:
                    with open(err_log_path, 'a', encoding='utf-8') as lf:
                        lf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Publish失败: {error_msg}\n')
                        lf.write(f'  完整响应: {response.text[:2000]}\n\n')
                    print(f'[Agiso Publish] 错误已保存到: {err_log_path}')
                except Exception as log_err:
                    print(f'[Agiso Publish] ⚠️ 写入错误日志失败: {log_err}')
                if not silent:
                    messagebox.showerror('发布失败', f'发布失败: {error_msg}\n\n详情已写入 publish_error.log')
                return False
        else:
            error_detail = response.text[:500]
            print(f'HTTP错误: {error_detail}')
            try:
                with open(err_log_path, 'a', encoding='utf-8') as lf:
                    lf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] HTTP错误({response.status_code}): {error_detail}\n\n')
                print(f'[Agiso Publish] HTTP错误已保存到: {err_log_path}')
            except Exception as log_err:
                print(f'[Agiso Publish] ⚠️ 写入错误日志失败: {log_err}')
            if not silent:
                messagebox.showerror('发布失败', f'发布失败：HTTP {response.status_code}\n\n详情已写入 publish_error.log')
            return False
    except Exception as e:
        print(f'发布异常: {str(e)}')
        import traceback
        traceback.print_exc()
        try:
            with open(err_log_path, 'a', encoding='utf-8') as lf:
                lf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] 发布异常: {str(e)}\n')
                lf.write(traceback.format_exc() + '\n\n')
            print(f'[Agiso Publish] 异常已保存到: {err_log_path}')
        except Exception as log_err:
            print(f'[Agiso Publish] ⚠️ 写入异常日志失败: {log_err}')
        if not silent:
            messagebox.showerror('发布失败', f'发布失败：{str(e)}\n\n详情已写入 publish_error.log')
        return False


def publish():
    """单件发布入口（带弹框提示）"""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning('警告', '请先选择一行数据')
        return

    item_values = tree.item(selected_item, 'values')
    _do_publish(item_values, silent=False)

def save_good():
    """收藏商品"""
    selected_item = tree.selection()
    if not selected_item:
        return
    
    save_data = {"itemId": str(item_ids[tree.index(selected_item[0])])}
    save_data_str = json.dumps(save_data)
    
    token = goofish_cookies.get('_m_h5_tk', '').split('_')[0]
    if not token:
        return
    
    timestamp = get_current_timestamp_milliseconds()
    app_key = '34839810'
    sign = get_md5_hash_string(f'{token}&{timestamp}&{app_key}&{save_data_str}')
    
    params = {
        'jsv': '2.7.2', 'appKey': app_key, 't': timestamp, 'sign': sign,
        'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
        'dataType': 'json', 'timeout': '20000', 'needLoginPC': 'true',
        'api': 'mtop.taobao.idle.collect.item',
        'sessionOption': 'AutoLoginOnly', 'spm_cnt': 'a21ybx.item.0.0'
    }
    
    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.collect.item/1.0/'
    
    try:
        response = requests.post(
            url, params=params, cookies=goofish_cookies,
            headers=goofish_headers, data={'data': save_data_str},
            verify=False, timeout=30,
            proxies={'http': None, 'https': None}
        )
        if response.status_code == 200:
            print(f'[+]收藏商品成功: {response.text[:200]}')
        else:
            print(f'[-]收藏商品失败: {response.status_code}')
    except Exception as e:
        print(f'[-]收藏异常: {e}')

def set_region_codes_dialog():
    """设置发布地区对话框"""
    global province_code, city_code, district_code
    
    root_win = tree.winfo_toplevel()
    dialog = tk.Toplevel(root_win)
    dialog.title('设置发布地区')
    dialog.geometry('350x450')
    dialog.transient(root_win)
    dialog.grab_set()
    
    # 省份
    ttk.Label(dialog, text='省份代码:').pack(pady=(15, 0))
    province_entry = ttk.Entry(dialog, width=20)
    province_entry.insert(0, province_code)
    province_entry.pack(pady=5)
    
    # 城市
    ttk.Label(dialog, text='城市代码:').pack(pady=(10, 0))
    city_entry = ttk.Entry(dialog, width=20)
    city_entry.insert(0, city_code)
    city_entry.pack(pady=5)
    
    # 区域
    ttk.Label(dialog, text='区域代码:').pack(pady=(10, 0))
    district_entry = ttk.Entry(dialog, width=20)
    district_entry.insert(0, district_code)
    district_entry.pack(pady=5)
    
    # 帮助信息
    help_text = ('常用地区代码参考：\n'
                 '广东省东莞市: 440000-441900\n'
                 '北京市朝阳区: 110000-110100-110105\n'
                 '上海市浦东新区: 310000-310100-310115\n'
                 '深圳市南山区: 440000-440300-440305\n'
                 '广州市天河区: 440000-440100-440106\n\n'
                 '默认发布地区：广东省东莞市')
    
    help_label = ttk.Label(dialog, text=help_text, justify='left')
    help_label.pack(pady=10, padx=20)
    
    def save_codes():
        global province_code, city_code, district_code
        province_code = province_entry.get().strip()
        city_code = city_entry.get().strip()
        district_code = district_entry.get().strip()
        messagebox.showinfo('成功', '地区代码已保存！')
        dialog.destroy()
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=15)
    ttk.Button(btn_frame, text='保存', command=save_codes).pack(side='left', padx=10)
    ttk.Button(btn_frame, text='取消', command=dialog.destroy).pack(side='left', padx=10)

def load_config():
    """加载配置文件"""
    global goofish_cookies, goofish_headers
    
    config_file = 'config.json'
    if not os.path.exists(config_file):
        messagebox.showinfo('提示', '没有找到配置文件！')
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 加载Cookie
        if 'cookies' in config:
            cookie_str = config['cookies']
            goofish_cookies = parse_cookies(cookie_str)
            if goofish_cookies:
                messagebox.showinfo('成功', 'Cookie已加载！')
                
                # 加载上次的关键词
                if 'last_keyword' in config and entry_keyword:
                    entry_keyword.insert(0, config['last_keyword'])
                
                return True
        
        return False
    except Exception as e:
        print(f"加载配置失败: {e}")
        return False

# ==================== 数据导出函数 ====================

def export_to_csv():
    """导出数据到CSV文件"""
    if not item_ids:
        messagebox.showerror('错误', '没有数据可以导出！')
        return
    
    try:
        filename = f"闲鱼数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['价格', '标题', '想要人数', '商品ID', '分类ID', '卖家', '地区'])
            
            # 写入数据
            for i in range(len(item_ids)):
                writer.writerow([
                    prices[i] if i < len(prices) else '',
                    titles[i] if i < len(titles) else '',
                    want_counts[i] if i < len(want_counts) else '',
                    item_ids[i] if i < len(item_ids) else '',
                    ccat_ids[i] if i < len(ccat_ids) else '',
                    user_nicks[i] if i < len(user_nicks) else '',
                    areas[i] if i < len(areas) else ''
                ])
        
        messagebox.showinfo('成功', f'数据已导出到：{filename}')
    except Exception as e:
        messagebox.showerror('错误', f'导出CSV失败：{e}')

def export_to_excel():
    """导出数据到Excel文件"""
    try:
        import openpyxl
    except ImportError:
        messagebox.showerror('错误', '请先安装openpyxl库：\npip install openpyxl')
        return
    
    if not item_ids:
        messagebox.showerror('错误', '没有数据可以导出！')
        return
    
    try:
        filename = f"闲鱼数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # 创建工作簿
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "闲鱼商品数据"
        
        # 写入表头
        headers = ['价格', '标题', '想要人数', '商品ID', '分类ID', '卖家', '地区']
        ws.append(headers)
        
        # 设置表头样式
        from openpyxl.styles import Font, Alignment
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # 写入数据
        for i in range(len(item_ids)):
            ws.append([
                prices[i] if i < len(prices) else '',
                titles[i] if i < len(titles) else '',
                want_counts[i] if i < len(want_counts) else '',
                item_ids[i] if i < len(item_ids) else '',
                ccat_ids[i] if i < len(ccat_ids) else '',
                user_nicks[i] if i < len(user_nicks) else '',
                areas[i] if i < len(areas) else ''
            ])
        
        # 调整列宽
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 50
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 12
        ws.column_dimensions['G'].width = 10
        
        # 保存文件
        wb.save(filename)
        messagebox.showinfo('成功', f'数据已导出到：{filename}')
    except Exception as e:
        messagebox.showerror('错误', f'导出Excel失败：{e}')

# ==================== 辅助函数 ====================

def _update_page_stats():
    """更新统计标签显示"""
    if _stats_label:
        _stats_label.config(text=f"共 {len(item_ids)} 条商品 | 已选 0 条")

def batch_resell_selected():
    """多商品一键转卖 - 批量处理所有选中的商品"""
    selected_items = tree.selection()
    
    if not selected_items:
        messagebox.showwarning('提示', '请先选择要转卖的商品（可多选）')
        return
    
    # 确认操作
    count = len(selected_items)
    result = messagebox.askyesno(
        '确认批量转卖',
        f'即将对 {count} 个选中商品执行一键转卖：\n\n'
        f'每个商品会依次执行：\n'
        f'  ① 获取详情/封面图\n  ② 上传图片到阿奇索\n  ③ 直接发布上架\n\n'
        f'是否继续？'
    )
    if not result:
        return

    # 获取选中的行索引
    indices = [tree.index(sid) for sid in selected_items]
    
    # 创建进度对话框
    total_steps = count * 4  # 每个商品约4步
    pdlg = ProgressDialog(tree.winfo_toplevel(), '批量转卖', f'准备处理 {count} 个商品...', total_steps)

    def process_all():
        success_count = 0
        fail_count = 0
        
        for i, idx in enumerate(indices):
            item_id = item_ids[idx] if idx < len(item_ids) else ''
            
            # === 步骤1: 获取图片和描述 ===
            title_short = titles[idx][:15] if idx < len(titles) else "未知"
            pdlg.update_progress(i * 4 + 1, "[{} / {}] 获取 [{}] 的图片...".format(i+1, count, title_short))
            
            # 使用与单件相同的逻辑获取图片
            img_urls, describe_text = _get_item_images_and_desc(idx)
            
            if not img_urls:
                print(f'[批量] 商品 {item_id} 无可用图片，跳过')
                fail_count += 1
                continue
            
            # === 步骤2: 处理图片并上传 ===
            pdlg.update_progress(i * 4 + 2, f"[{i+1}/{count}] 上传图片...")
            
            # 清空之前的上传结果（保留全局描述）
            global global_image_ids, global_oss_keys, global_agiso_img_urls
            global_image_ids.clear()
            global_oss_keys.clear()
            global_agiso_img_urls.clear()
            
            # 下载→转换→上传
            uploaded_ok = False
            for img_url in img_urls:
                filepath = download_file(img_url)
                if filepath:
                    convert_images_to_png_in_directory()
                    _, png_paths = find_png_files_without_extension()
                    for pp in png_paths:
                        ok = upload_file(pp)
                        if ok and not uploaded_ok:
                            uploaded_ok = True
                    delete_png_files_recursively()
            
            if not global_image_ids:
                print(f'[批量] 商品 {item_id} 图片上传失败，跳过发布')
                fail_count += 1
                continue
            
            # === 步骤3: 发布商品（完整调用链：发布→收藏→清理）===
            pdlg.update_progress(i * 4 + 3, f"[{i+1}/{count}] 发布到阿奇索...")

            # 设置当前商品的描述
            global global_describe
            global_describe = describe_text

            # 直接传入 item_values，静默发布（不弹框）
            item_values = tree.item(selected_items[i], 'values')
            # 确保 tree 选中当前项（save_good() 内部依赖 tree.selection()）
            old_selection = tree.selection()
            tree.selection_set(selected_items[i])

            ok = False
            try:
                ok = _do_publish(item_values, silent=True)
            except Exception as pub_err:
                print(f'[批量] 发布异常: {pub_err}')
                import traceback
                traceback.print_exc()
                try:
                    dump_dir = os.path.dirname(os.path.abspath(__file__))
                    with open(os.path.join(dump_dir, 'publish_error.log'), 'a', encoding='utf-8') as lf:
                        lf.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] 批量发布异常: {pub_err}\n')
                        lf.write(traceback.format_exc() + '\n\n')
                except Exception as log_err:
                    print(f'[批量] ⚠️ 写入错误日志失败: {log_err}')
                ok = False

            # 恢复选中状态
            tree.selection_set(old_selection)

            if ok:
                success_count += 1
                pdlg.update_progress((i + 1) * 4, f"[{i+1}/{count}] 「{titles[idx][:10] if idx < len(titles) else ''}」✅ 发布成功")
            else:
                fail_count += 1
                pdlg.update_progress((i + 1) * 4, f"[{i+1}/{count}] 「{titles[idx][:10] if idx < len(titles) else ''}」❌ 发布失败")

        pdlg.destroy()
        
        # 最终报告
        msg = f'批量转卖完成！\n\n成功: {success_count} 个\n失败: {fail_count} 个\n总计: {count} 个'
        if fail_count == 0:
            messagebox.showinfo('批量转卖成功', msg)
        else:
            messagebox.showwarning('批量转卖部分成功', msg)
    
    threading.Thread(target=process_all, daemon=True).start()

def _get_item_images_and_desc(idx):
    """
    获取指定索引的商品的图片URL列表和描述文本。
    返回 (img_urls: list[str], describe_text: str)
    与 print_selected_row_info 的图片获取逻辑相同，但只返回数据不触发流程。
    """
    global global_describe
    
    item_id = item_ids[idx] if idx < len(item_ids) else ''
    fallback_img_url = pic_urls[idx] if idx < len(pic_urls) else ''
    
    img_urls = []
    describe_text = titles[idx] if idx < len(titles) else ''
    
    if not item_id:
        return ([], describe_text)
    
    # 尝试详情 API
    token = goofish_cookies.get('_m_h5_tk', '').split('_')[0]
    if token:
        try:
            detail_data = {"itemId": str(item_id)}
            detail_data_str = json.dumps(detail_data)
            timestamp = get_current_timestamp_milliseconds()
            sign = get_md5_hash_string(f'{token}&{timestamp}&34839810&{detail_data_str}')
            params = {
                'jsv': '2.7.2', 'appKey': '34839810', 't': timestamp, 'sign': sign,
                'v': '1.0', 'type': 'originaljson', 'accountSite': 'xianyu',
                'dataType': 'json', 'timeout': '20000',
                'api': 'mtop.taobao.idle.pc.detail',
                'sessionOption': 'AutoLoginOnly', 'spm_cnt': 'a21ybx.item.0.0'
            }
            resp = requests.post(
                'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/',
                params=params, cookies=goofish_cookies, headers=goofish_headers,
                data={'data': detail_data_str}, verify=False, timeout=30,
                proxies={'http': None, 'https': None}
            )
            if resp.status_code == 200:
                dj = resp.json()
                rc = dj.get('ret', [''])[0] if dj.get('ret') else ''
                if 'SUCCESS' in rc:
                    txt = dj.get('data', {}).get('item', {}).get('main', {}).get('text', '')
                    ic = re.compile(r'"\\"image\\":\\"(?P<u>.*?)\\",\\"width\\":\\"', re.S)
                    img_urls = [m.group('u') for m in ic.finditer(txt)]
                    dc = re.compile(r'"},\\"mainParams\\":{\\"content\\":\\"(?P<d>.*?)\\",\\"', re.S)
                    dm = dc.search(txt)
                    if dm:
                        describe_text = dm.group('d').replace('\\n', '\n').replace('\\r', '')
        except Exception as e:
            print(f'[详情API] 异常: {e}')
    
    # 备选方案
    if not img_urls and fallback_img_url:
        img_urls = [fallback_img_url]
    
    return (img_urls, describe_text)


# ==================== 主程序 ====================

# 排序状态
sort_column = None
sort_reverse = False

def on_tree_heading_click(event):
    """点击表头排序"""
    global sort_column, sort_reverse, prices, titles, want_counts, item_ids, ccat_ids, urls, user_nicks, areas, pic_urls

    # 获取点击的列标识符
    col_id = tree.identify_column(event.x)
    if not col_id:
        return
    
    # 从列ID中提取列名 (格式: #0, #1, ...)
    try:
        col_idx = int(col_id.lstrip('#'))
        if col_idx >= len(visible_columns):
            return
        column = visible_columns[col_idx]
    except ValueError:
        return
    
    # 切换排序方向
    if sort_column == column:
        sort_reverse = not sort_reverse
    else:
        sort_column = column
        sort_reverse = False
    
    # 获取数据索引（映射可见列名到数据列表索引）
    col_to_data_index = {
        '价格': 0, '标题': 1, '想要人数': 2,
        '商品ID': 3, '分类ID': 4, '卖家': 5, '地区': 6
    }
    
    data_idx = col_to_data_index.get(column, -1)
    if data_idx < 0 or not item_ids:
        return
    
    # 构建排序键
    def get_sort_key(i):
        data_lists = [prices, titles, want_counts, item_ids, ccat_ids, user_nicks, areas]
        val = data_lists[data_idx][i] if i < len(data_lists[data_idx]) else ''
        
        # 数字类型按数值排序
        if column in ('价格', '想要人数', '商品ID', '分类ID'):
            try:
                val_float = float(val)
                if column == '价格' and isinstance(val, str) and val.startswith('¥'):
                    val_float = float(val.replace('¥', '').strip())
                return (0, val_float) if not sort_reverse else (0, -val_float)
            except (ValueError, TypeError):
                pass
        
        # 字符串按文本排序
        return (1, str(val).lower()) if not sort_reverse else (1, str(val).lower(), True)
    
    # 生成排序列表
    indices = list(range(len(item_ids)))
    indices.sort(key=get_sort_key)

    # 同步重排所有数据列表（保证 tree.index() 能正确映射到数据位置）
    prices = [prices[i] for i in indices]
    titles = [titles[i] for i in indices]
    want_counts = [want_counts[i] for i in indices]
    item_ids = [item_ids[i] for i in indices]
    ccat_ids = [ccat_ids[i] for i in indices]
    urls = [urls[i] for i in indices]
    user_nicks = [user_nicks[i] for i in indices]
    areas = [areas[i] for i in indices]
    pic_urls = [pic_urls[i] for i in indices]

    # 清空并重新填充表格（与数据列表顺序一致）
    for row_id in tree.get_children():
        tree.delete(row_id)

    for i in range(len(item_ids)):
        clean_title = ' '.join(str(titles[i]).splitlines()).strip()
        if len(clean_title) > 80:
            clean_title = clean_title[:78] + '…'
        tree.insert('', 'end', values=(
            prices[i], clean_title, want_counts[i],
            item_ids[i], ccat_ids[i],
            user_nicks[i], areas[i]
        ))
    
    # 更新表头指示（在标题后加 ↑/↓）
    for c in visible_columns:
        heading_text = c
        if c == column:
            heading_text += ' ↓' if sort_reverse else ' ↑'
        tree.heading(c, text=heading_text)

def main():
    """主程序入口（GUI）"""
    global tree, entry_keyword, visible_columns

    # 创建主窗口
    root = tk.Tk()
    root.title("闲鱼转卖助手 2.0【鱼小铺版】")
    root.geometry("1550x850")
    root.minsize(1100, 650)

    # 设置样式
    style = Style()
    style.theme_use('clam')
    # Treeview 视觉优化：更大字体、固定行高（防止换行内容撑高行）
    style.configure('Treeview',
                    font=('Microsoft YaHei UI', 10),
                    rowheight=30)
    style.configure('Treeview.Heading',
                    font=('Microsoft YaHei UI', 10, 'bold'))
    style.map('Treeview',
              background=[('selected', '#0078d4')],
              foreground=[('selected', 'white')])

    # 创建主框架
    main_frame = ttk.Frame(root, padding="8")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # ===== 第一行：搜索控制 =====
    input_frame = ttk.Frame(main_frame)
    input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 6))

    ttk.Label(input_frame, text="关键词：").pack(side=tk.LEFT, padx=(0, 4))
    entry_keyword = ttk.Entry(input_frame, width=28)
    entry_keyword.pack(side=tk.LEFT, padx=(0, 10))

    ttk.Button(input_frame, text="验证Cookie", command=get_and_validate_cookies).pack(side=tk.LEFT, padx=3)
    ttk.Button(input_frame, text="搜索全部", command=lambda: fetch_data(entry_keyword.get().strip())).pack(side=tk.LEFT, padx=3)
    ttk.Button(input_frame, text="清空", command=clear_lists).pack(side=tk.LEFT, padx=3)
    ttk.Button(input_frame, text="打开链接", command=open_url).pack(side=tk.LEFT, padx=3)

    # ===== 第二行：工具栏 =====
    input_frame2 = ttk.Frame(main_frame)
    input_frame2.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 6))

    ttk.Button(input_frame2, text="导出CSV", command=export_to_csv).pack(side=tk.LEFT, padx=3)
    ttk.Button(input_frame2, text="导出Excel", command=export_to_excel).pack(side=tk.LEFT, padx=3)
    ttk.Separator(input_frame2, orient='vertical').pack(side=tk.LEFT, fill='y', padx=6)
    ttk.Button(input_frame2, text="下载图片", command=lambda: download_images(urls)).pack(side=tk.LEFT, padx=3)
    ttk.Button(input_frame2, text="设置地区", command=set_region_codes_dialog).pack(side=tk.LEFT, padx=3)
    ttk.Separator(input_frame2, orient='vertical').pack(side=tk.LEFT, fill='y', padx=6)

    # 统计信息标签
    stats_label = ttk.Label(input_frame2, text="共 0 条商品", font=('Microsoft YaHei UI', 10))
    stats_label.pack(side=tk.RIGHT, padx=5)

    # ===== 第三行：转卖功能 =====
    input_frame3 = ttk.Frame(main_frame)
    input_frame3.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 6))

    ttk.Button(input_frame3, text="🚀 一键转卖（选中项）", command=batch_resell_selected).pack(side=tk.LEFT, padx=3)
    ttk.Label(input_frame3, text="提示：Ctrl/Shift+点击可多选 | 点击表头可排序",
                font=('Microsoft YaHei UI', 9), foreground='gray').pack(side=tk.LEFT, padx=15)

    # ===== 表格区域 =====
    tree_frame = ttk.Frame(main_frame)
    tree_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
    scrollbar = ttk.Scrollbar(tree_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 列配置 — 宽度按数据内容合理分配，标题列自动填满剩余空间
    visible_columns = ['价格', '标题', '想要人数', '商品ID', '分类ID', '卖家', '地区']
    col_config = {
        '价格':      {'width': 80,   'anchor': 'e',       'stretch': False},
        '标题':      {'width': 420,  'anchor': 'w',       'stretch': True},
        '想要人数':   {'width': 70,   'anchor': 'center',  'stretch': False},
        '商品ID':     {'width': 130,  'anchor': 'center',  'stretch': False},
        '分类ID':     {'width': 95,   'anchor': 'center',  'stretch': False},
        '卖家':       {'width': 100,  'anchor': 'w',       'stretch': False},
        '地区':       {'width': 85,   'anchor': 'w',       'stretch': False},
    }

    tree = Treeview(
        tree_frame,
        columns=tuple(visible_columns),
        show='headings',
        selectmode='extended',
        yscrollcommand=scrollbar.set,
        xscrollcommand=h_scrollbar.set,
        height=25
    )

    # 配置列 + 绑定表头点击排序事件
    for i, col in enumerate(visible_columns):
        cfg = col_config[col]
        tree.heading(col, text=col)
        stretch_opt = cfg.get('stretch', False)
        tree.column(col, width=cfg['width'], anchor=cfg['anchor'],
                    minwidth=max(cfg['width'] // 2, 50), stretch=stretch_opt)

    # 绑定表头点击排序（通过 identify_region 判断点击位置）
    def on_tree_click(event):
        region = tree.identify_region(event.x, event.y)
        if region == 'heading':
            on_tree_heading_click(event)
        else:
            on_tree_select_change(event)

    tree.bind('<ButtonRelease-1>', on_tree_click)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=tree.yview)
    h_scrollbar.config(command=tree.xview)

    # 网格权重
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(3, weight=1)

    # 持久化引用供其他函数使用
    global _stats_label
    _stats_label = stats_label

    # 启动主循环
    root.mainloop()

def on_tree_select_change(event):
    """选择变化时更新统计信息"""
    if _stats_label is None:
        return
    selected = tree.selection()
    total = len(item_ids)
    if selected:
        count = len(selected)
        _stats_label.config(text=f"已选 {count}/{total} 条")
    else:
        _stats_label.config(text=f"共 {total} 条商品 | 已选 0 条")

if __name__ == "__main__":
    main()
