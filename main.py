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
    'Content-Type': 'application/json-patch+json',
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

# 页码
page_number = 1

# GUI 控件
tree = None
entry_keyword = None

# ==================== 工具函数 ====================

def parse_cookies(cookie_str):
    """解析 cookies 字符串"""
    try:
        cookies = dict(item.split('=', 1) for item in cookie_str.split('; '))
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
    global prices, titles, want_counts, item_ids, ccat_ids, urls, user_nicks, areas
    prices.clear()
    titles.clear()
    want_counts.clear()
    item_ids.clear()
    ccat_ids.clear()
    urls.clear()
    user_nicks.clear()
    areas.clear()
    for row in tree.get_children():
        tree.delete(row)

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
    """获取用户输入（使用 tkinter 对话框）"""
    return simpledialog.askstring(title, prompt)

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
        'pageSize': 40,
        'searchFrom': 'search',
        'fluctuationUrl': '',
        'fluctuationData': ''
    }

def fetch_data(keyword):
    """抓取数据（核心函数 - 改进版）"""
    global prices, titles, want_counts, item_ids, ccat_ids, urls, user_nicks, areas, page_number
    
    # 验证关键词
    if not keyword:
        keyword = entry_keyword.get().strip()
    
    if not keyword:
        messagebox.showerror('错误', '请输入有效的关键词')
        return
    
    # 验证Cookie是否已设置
    if not goofish_cookies:
        messagebox.showerror('错误', '请先验证Cookie！')
        return
    
    # 构建请求参数
    payload = build_payload(page_number, keyword)
    data_str = json.dumps(payload)
    print(f"请求参数: {data_str}")
    
    # 提取 token
    token = goofish_cookies.get('_m_h5_tk', '').split('_')[0]
    if not token:
        messagebox.showerror('错误', 'Cookie中缺少token，请重新验证Cookie！')
        return
    
    # 生成签名
    timestamp = get_current_timestamp_milliseconds()
    app_key = '34839810'
    sign_str = f'{token}&{timestamp}&{app_key}&{data_str}'
    sign = get_md5_hash_string(sign_str)
    print(f"签名字符串: {sign_str}")
    print(f"签名: {sign}")
    
    # 构建请求参数
    params = {
        'jsv': '2.7.2',
        'appKey': app_key,
        't': timestamp,
        'sign': sign,
        'v': '1.0',
        'type': 'originaljson',
        'accountSite': 'xianyu',
        'dataType': 'json',
        'timeout': '20000',
        'api': 'mtop.taobao.idlemtopsearch.pc.search',
        'sessionOption': 'AutoLoginOnly',
        'spm_cnt': 'a21ybx.search.0.0',
        'spm_pre': 'a21ybx.search.searchInput.0'
    }
    
    # 发送请求
    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/'
    try:
        print(f"发送请求到: {url}")
        response = requests.post(
            url,
            params=params,
            cookies=goofish_cookies,
            headers=goofish_headers,
            data={'data': data_str},
            verify=False,
            timeout=30,
            proxies={'http': None, 'https': None}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            messagebox.showerror('错误', f'请求失败：{response.status_code}\n{response.text[:200]}')
            return
        
        # 解析响应
        try:
            json_data = response.json()
            print(f"响应数据: {json.dumps(json_data, ensure_ascii=False)[:500]}")
        except json.JSONDecodeError as e:
            messagebox.showerror('错误', f'JSON解析失败：{e}\n响应内容：{response.text[:200]}')
            return
        
        # 检查API返回的错误
        if 'ret' in json_data:
            ret_code = json_data['ret'][0] if json_data['ret'] else ''
            if 'FAIL' in ret_code or 'ERROR' in ret_code:
                messagebox.showerror('API错误', f'API返回错误：{ret_code}\n详细信息：{json_data.get("data", {}).get("retMsg", "")}')
                return
        
        # 提取数据
        outer_data = json_data.get('data', {})
        if not outer_data:
            messagebox.showinfo('提示', '未获取到数据，请检查Cookie是否有效或关键词是否正确')
            return
        
        result_list = outer_data.get('resultList', [])
        if not result_list:
            messagebox.showinfo('提示', '未找到相关商品')
            return
        
        print(f"获取到 {len(result_list)} 个商品")
        
        # 处理每个商品
        new_count = 0
        for item in result_list:
            try:
                data = item.get('data', {})
                item_data = data.get('item', {})
                main_data = item_data.get('main', {})
                
                # 提取点击参数
                click_param = main_data.get('clickParam', {})
                args = click_param.get('args', {})
                
                # 提取商品信息
                price = main_data.get('price', {}).get('price', 0)
                title = main_data.get('title', '')
                user_nick = main_data.get('userNick', '')
                area = main_data.get('area', '')
                fish_tags = main_data.get('fishTags', [])
                r3_tag_list = main_data.get('r3TagList', [])
                want_count = main_data.get('wantCount', 0)
                
                # 提取商品ID和分类ID
                item_id = args.get('itemId', '')
                ccat_id = args.get('ccatId', '')
                
                # 构建商品链接
                item_url = f'https://www.goofish.com/item?id={item_id}' if item_id else 'Error：url'
                
                # 检查是否已存在
                if item_id and item_id not in item_ids:
                    # 添加到全局列表
                    prices.append(price)
                    titles.append(title)
                    want_counts.append(want_count)
                    item_ids.append(item_id)
                    ccat_ids.append(ccat_id)
                    urls.append(item_url)
                    user_nicks.append(user_nick)
                    areas.append(area)
                    
                    # 添加到表格
                    tree.insert('', 'end', values=(
                        price,
                        title,
                        want_count,
                        item_id,
                        ccat_id,
                        item_url,
                        user_nick,
                        area
                    ))
                    
                    new_count += 1
                    
            except Exception as e:
                print(f"处理商品时出错: {e}")
                continue
        
        messagebox.showinfo('成功', f'成功抓取 {new_count} 个新商品（总计 {len(item_ids)} 个）')
        
    except requests.exceptions.Timeout:
        messagebox.showerror('错误', '请求超时，请检查网络连接')
    except requests.exceptions.RequestException as e:
        messagebox.showerror('错误', f'请求异常：{e}')
    except Exception as e:
        messagebox.showerror('错误', f'程序异常：{e}')
        import traceback
        traceback.print_exc()

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

def fetch_next_page_data():
    """抓取下一页数据"""
    global page_number
    page_number += 1
    fetch_data(entry_keyword.get().strip())

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
            writer.writerow(['价格', '标题', '想要人数', '商品ID', '分类ID', '链接', '卖家', '地区'])
            
            # 写入数据
            for i in range(len(item_ids)):
                writer.writerow([
                    prices[i] if i < len(prices) else '',
                    titles[i] if i < len(titles) else '',
                    want_counts[i] if i < len(want_counts) else '',
                    item_ids[i] if i < len(item_ids) else '',
                    ccat_ids[i] if i < len(ccat_ids) else '',
                    urls[i] if i < len(urls) else '',
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
        headers = ['价格', '标题', '想要人数', '商品ID', '分类ID', '链接', '卖家', '地区']
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
                urls[i] if i < len(urls) else '',
                user_nicks[i] if i < len(user_nicks) else '',
                areas[i] if i < len(areas) else ''
            ])
        
        # 调整列宽
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 40
        ws.column_dimensions['G'].width = 15
        ws.column_dimensions['H'].width = 12
        
        # 保存文件
        wb.save(filename)
        messagebox.showinfo('成功', f'数据已导出到：{filename}')
    except Exception as e:
        messagebox.showerror('错误', f'导出Excel失败：{e}')

# ==================== 主程序 ====================

def main():
    """主程序入口（GUI）"""
    global tree, entry_keyword
    
    # 创建主窗口
    root = tk.Tk()
    root.title("闲鱼转卖助手 2.0【鱼小铺版】")
    root.geometry("1200x700")
    
    # 设置样式
    style = Style()
    style.theme_use('clam')
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # 输入框和按钮框架（第一行）
    input_frame = ttk.Frame(main_frame)
    input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
    
    ttk.Label(input_frame, text="关键词：").pack(side=tk.LEFT, padx=5)
    entry_keyword = ttk.Entry(input_frame, width=30)
    entry_keyword.pack(side=tk.LEFT, padx=5)
    
    ttk.Button(input_frame, text="验证Cookie", command=get_and_validate_cookies).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame, text="抓取数据", command=lambda: fetch_data(entry_keyword.get().strip())).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame, text="下一页", command=fetch_next_page_data).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame, text="清空列表", command=clear_lists).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame, text="打开链接", command=open_url).pack(side=tk.LEFT, padx=5)
    
    # 第二行按钮框架（导出和配置）
    input_frame2 = ttk.Frame(main_frame)
    input_frame2.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
    
    ttk.Button(input_frame2, text="导出CSV", command=export_to_csv).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame2, text="导出Excel", command=export_to_excel).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame2, text="保存配置", command=save_config).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame2, text="加载配置", command=load_config).pack(side=tk.LEFT, padx=5)
    ttk.Button(input_frame2, text="下载图片", command=lambda: download_images(urls)).pack(side=tk.LEFT, padx=5)
    
    # 创建表格
    tree_frame = ttk.Frame(main_frame)
    tree_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    
    # 滚动条
    scrollbar = ttk.Scrollbar(tree_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Treeview 表格
    tree = Treeview(
        tree_frame,
        columns=('价格', '标题', '想要人数', '商品ID', '分类ID', '链接', '卖家', '地区'),
        show='headings',
        yscrollcommand=scrollbar.set,
        height=20
    )
    
    # 设置列标题
    for col in tree['columns']:
        tree.heading(col, text=col)
        tree.column(col, width=100 if col != '标题' else 200)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=tree.yview)
    
    # 配置网格权重
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(2, weight=1)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main()
