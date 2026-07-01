"""
闲鱼转卖助手 - 发布/转卖功能模块
基于 cest.pyc 反汇编恢复
"""

import os
import re
import json
import time
import hashlib
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import requests
import imageio

# ==================== 导入主模块全局变量 ====================
# 这些变量将在 main.py 中全局定义，这里通过参数传递
# goofish_cookies, agiso_cookies, user_authorization
# goofish_headers, agiso_upload_headers, agiso_publish_headers
# tree, item_ids, urls, prices, titles, want_counts, user_nicks, areas, ccat_ids

# ==================== 全局变量（发布相关） ====================

global_image_ids = []      # 图片ID列表
global_oss_keys = []       # OSS Key列表
global_agiso_img_urls = [] # Agiso图片URL列表
global_describe = ''       # 商品描述

province_code = '440000'   # 省份代码（默认东莞）
city_code = '441900'       # 城市代码（默认东莞）
district_code = ''         # 区代码

current_sort_column = None
reverse_sort = False

# ==================== 工具函数 ====================

def get_md5_hash_string(input_str):
    """计算字符串的 MD5 哈希值"""
    hash_object = hashlib.md5()
    hash_object.update(input_str.encode('utf-8'))
    return hash_object.hexdigest()

def get_current_timestamp_milliseconds():
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)

def convert_to_int_or_float(value):
    """将字符串转换为 int 或 float"""
    match = re.search(r'\d+(\.\d+)?', str(value))
    if match:
        number_str = match.group()
        try:
            return int(number_str)
        except ValueError:
            return float(number_str)
    return 'N/A'

# ==================== 排序相关 ====================

def sort_by_want_count(want_count_global, reverse_sort_global, 
                       titles_list, prices_list, want_counts_list, 
                       user_nicks_list, areas_list, item_ids_list, 
                       ccat_ids_list, urls_list, tree_widget):
    """按想要人数排序"""
    data_list = list(zip(titles_list, prices_list, want_counts_list, 
                         user_nicks_list, areas_list, item_ids_list, 
                         ccat_ids_list, urls_list))
    
    sorted_data = sorted(data_list, key=lambda x: x[2], reverse=reverse_sort_global)
    
    # 清空全局列表
    titles_list.clear()
    prices_list.clear()
    want_counts_list.clear()
    user_nicks_list.clear()
    areas_list.clear()
    item_ids_list.clear()
    ccat_ids_list.clear()
    urls_list.clear()
    
    # 清空 Treeview
    for row in tree_widget.get_children():
        tree_widget.delete(row)
    
    # 重新填充
    for row in sorted_data:
        title, price, want_count, user_nick, area, item_id, ccat_id, url = row
        
        formatted_price = f'¥{price}' if price != 'Error： price' else 'Error： price'
        
        titles_list.append(title)
        prices_list.append(price)
        want_counts_list.append(want_count)
        user_nicks_list.append(user_nick)
        areas_list.append(area)
        item_ids_list.append(item_id)
        ccat_ids_list.append(ccat_id)
        urls_list.append(url)
        
        tree_widget.insert('', 'end', values=(
            formatted_price, title, want_count, user_nick, area
        ))

def on_column_click(column_name):
    """处理列点击排序"""
    global current_sort_column, reverse_sort
    
    if current_sort_column == column_name:
        reverse_sort = not reverse_sort
    else:
        current_sort_column = column_name
        reverse_sort = False
    
    sort_by_want_count()

# ==================== 右键菜单 ====================

def on_right_click(event, tree_widget, root_window):
    """右键点击菜单"""
    selected_item = tree_widget.identify_row(event.y)
    
    if selected_item:
        tree_widget.selection_set(selected_item)
        
        menu = tk.Menu(root_window, tearoff=0)
        menu.add_command(label='打开网站', command=lambda: open_url_wrapper(tree_widget))
        menu.add_separator()
        menu.add_command(label='进入软件交流群', command=lambda: 
            webbrowser.open('https://qm.qq.com/q/AFlCLqMB7I'))
        
        menu.post(event.x_root, event.y_root)

# ==================== 数据抓取相关 ====================

def on_fetch_button_click(clear_lists_func, fetch_data_func):
    """点击搜索按钮的事件处理"""
    clear_lists_func()
    global page_number
    page_number = 1
    fetch_data_func()

def fetch_next_page_data(fetch_data_func, keyword_getter):
    """抓取下一页数据"""
    global page_number
    page_number += 1
    fetch_data_func(keyword_getter())

# ==================== 文件操作 ====================

def download_file(url, filename=None):
    """下载文件"""
    try:
        response = requests.get(
            url,
            stream=True,
            timeout=30,
            verify=False,
            cookies=goofish_cookies,
            headers=goofish_headers
        )
        response.raise_for_status()
        
        if not filename:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
        
        save_path = os.path.join(os.getcwd(), 'downloaded_file', filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return save_path
    except requests.exceptions.RequestException as e:
        print(f'下载过程中出现错误: {e}')
        return None

def convert_images_to_png_in_directory():
    """将目录中的图片转换为PNG格式"""
    current_directory = os.getcwd()
    supported_extensions = ('.heic', '.jpg', '.jpeg')
    
    try:
        for filename in os.listdir(current_directory):
            if filename.lower().endswith(supported_extensions):
                source_path = os.path.join(current_directory, filename)
                try:
                    image = imageio.imread(source_path)
                    base_name, _ = os.path.splitext(filename)
                    png_filename = f'{base_name}.png'
                    png_path = os.path.join(current_directory, png_filename)
                    imageio.imwrite(png_path, image)
                    os.remove(source_path)
                except Exception as e:
                    print(f'无法读取文件 {filename}: {e}')
                    continue
                except Exception as e:
                    print(f'无法写入文件 {png_filename}: {e}')
                    continue
                except Exception as e:
                    print(f'无法删除文件 {filename}: {e}')
                    continue
    except Exception as e:
        print(f'转换过程中出现错误: {e}')

def find_png_files_without_extension():
    """查找当前目录中所有PNG文件（不含扩展名）"""
    png_filenames_no_ext = []
    png_filepaths_no_ext = []
    
    try:
        with os.scandir(os.getcwd()) as entries:
            for entry in entries:
                if entry.is_file():
                    filename = entry.name
                    if filename.lower().endswith('.png'):
                        base_name, _ = os.path.splitext(filename)
                        png_filenames_no_ext.append(base_name)
                        png_filepaths_no_ext.append(os.path.join(os.getcwd(), filename))
    except Exception as e:
        print(f'搜索过程中出现错误: {e}')
    
    return png_filenames_no_ext, png_filepaths_no_ext

def delete_png_files_recursively():
    """递归删除当前目录及子目录中的所有PNG文件"""
    for root_dir, dirs, files in os.walk(os.getcwd()):
        for filename in files:
            if filename.lower().endswith('.png'):
                try:
                    os.remove(os.path.join(root_dir, filename))
                except Exception as e:
                    print(f'删除文件失败: {filename}, {e}')

# ==================== 上传文件 ====================

def upload_file(file_path):
    """上传文件到Agiso服务器"""
    global global_image_ids, global_oss_keys, global_agiso_img_urls
    
    url = 'https://aldsidle.agiso.com/api/GoodsManage/MediaUpload'
    
    file_name = os.path.basename(file_path)
    
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (file_name, f, 'image/png')}
            response = requests.post(
                url,
                cookies=agiso_cookies,
                headers=agiso_upload_headers,
                files=files,
                verify=False
            )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('succeeded'):
                data = response_data.get('data', {})
                image_id = data.get('imageId', '')
                oss_key = data.get('ossKey', '')
                agiso_img_url = data.get('agisoImgUrl', '')
                
                global_image_ids.append(image_id)
                global_oss_keys.append(oss_key)
                global_agiso_img_urls.append(agiso_img_url)
                
                return True
        
        return False
    except requests.exceptions.RequestException as e:
        print(f'请求错误: {e}')
        return False

# ==================== 进度对话框 ====================

class ProgressDialog:
    """进度对话框"""
    
    def __init__(self, parent, title, message, maximum):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry('300x150')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 使窗口居中
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 300) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        self.dialog.geometry(f'+{x}+{y}')
        
        # 标签
        self.label = ttk.Label(self.dialog, text=message)
        self.label.pack(pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(
            self.dialog,
            orient='horizontal',
            length=250,
            mode='determinate',
            maximum=maximum
        )
        self.progress.pack(pady=10)
        
        # 百分比标签
        self.percent_label = ttk.Label(self.dialog, text='0%')
        self.percent_label.pack()
        
        self.dialog.protocol('WM_DELETE_WINDOW', self._ignore_close)
    
    def _ignore_close(self):
        """忽略关闭按钮"""
        pass
    
    def update_progress(self, value, message=None):
        """更新进度"""
        self.progress['value'] = value
        percent = int((value / self.progress['maximum']) * 100) if self.progress['maximum'] > 0 else 0
        self.percent_label.config(text=f'{percent}%')
        if message:
            self.label.config(text=message)
        self.dialog.update()
    
    def destroy(self):
        """销毁对话框"""
        self.dialog.destroy()

# ==================== 图片处理与发布流程 ====================

def download_and_process_images(img_urls, progress_dialog):
    """下载图片并处理上传流程的核心函数"""
    global global_image_ids, global_oss_keys, global_agiso_img_urls
    
    total_images = len(img_urls)
    
    for i, img_url in enumerate(img_urls):
        # 更新进度
        progress_msg = f'正在处理第 {i + 1}/{total_images} 张图片'
        progress_dialog.update_progress(i + 1, progress_msg)
        print(f'处理图片 URL: {img_url}')
        
        # 下载图片
        filepath = download_file(img_url)
        if not filepath:
            print(f'下载图片失败: {img_url}')
            continue
        
        # 转换为PNG
        convert_images_to_png_in_directory()
        
        # 查找PNG文件
        png_names, png_paths = find_png_files_without_extension()
        
        # 上传每个PNG文件
        for png_path in png_paths:
            upload_file(png_path)
        
        # 清理转换后的文件
        delete_png_files_recursively()
    
    # 处理完成
    progress_dialog.update_progress(len(img_urls), '图片处理完成，准备发布...')
    
    # 执行发布
    publish()

def process_images_with_progress(img_urls):
    """带进度条的图片处理"""
    global global_image_ids, global_oss_keys, global_agiso_img_urls
    
    # 清空图片相关列表
    global_image_ids.clear()
    global_oss_keys.clear()
    global_agiso_img_urls.clear()
    
    # 创建进度对话框
    progress_dialog = ProgressDialog(root, '图片处理', '正在处理图片...', len(img_urls) * 3)
    
    # 在后台线程中处理
    def process_step():
        download_and_process_images(img_urls, progress_dialog)
    
    threading.Thread(target=process_step, daemon=True).start()

def complete_process(progress_dialog):
    """完成处理流程"""
    print("所有图片处理完成")
    
    if progress_dialog:
        try:
            progress_dialog.destroy()
        except:
            pass
    
    # 执行发布
    publish()

def print_selected_row_info(goofish_cookies_ref, goofish_headers_ref, tree_ref, item_ids_ref, urls_ref):
    """输出选中行信息并开始转卖流程"""
    selected_item = tree_ref.selection()
    
    if not selected_item:
        messagebox.showwarning('警告', '请先选择一行数据')
        return
    
    item_values = tree_ref.item(selected_item, 'values')
    
    # 打印调试信息
    print('——————————————————————————————————————')
    print(f'商品ID: {item_ids_ref[tree_ref.index(selected_item[0])]}')
    print(f'价格: {item_values[1]}')
    print(f'想要人数: {item_values[2]}')
    print(f'卖家名称: {item_values[3]}')
    print(f'地区: {item_values[4]}')
    print(f'URL: {urls_ref[tree_ref.index(selected_item[0])]}')
    
    # 获取商品详情
    item_id = item_ids_ref[tree_ref.index(selected_item[0])]
    
    # 构建请求
    detail_data = {"itemId": str(item_id)}
    detail_data_str = json.dumps(detail_data)
    
    app_key = '34839810'
    timestamp = get_current_timestamp_milliseconds()
    token = goofish_cookies_ref.get('_m_h5_tk', '').split('_')[0]
    sign = get_md5_hash_string(f'{token}&{timestamp}&{app_key}&{detail_data_str}')
    
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
        'api': 'mtop.taobao.idle.pc.detail',
        'sessionOption': 'AutoLoginOnly',
        'spm_cnt': 'a21ybx.item.0.0'
    }
    
    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail/1.0/'
    
    try:
        detail_response = requests.post(
            url,
            params=params,
            cookies=goofish_cookies_ref,
            headers=goofish_headers_ref,
            data={'data': detail_data_str},
            verify=False
        )
        
        if detail_response.status_code == 200:
            detail_json = detail_response.json()
            
            # 提取图片URL
            img_urls = []
            text = detail_json.get('data', {}).get('item', {}).get('main', {}).get('text', '')
            
            image_compile = re.compile(r'"\\"image\\":\\"(?P<imgUrl>.*?)\\",\\"width\\":\\"', re.S)
            reuslt_images = image_compile.finditer(text)
            
            for img in reuslt_images:
                img_urls.append(img.group('imgUrl'))
            
            # 提取描述
            describe_compile = re.compile(r'"},\\"mainParams\\":{\\"content\\":\\"(?P<describe>.*?)\\",\\"', re.S)
            result_describe = describe_compile.search(text)
            
            global global_describe
            if result_describe:
                global_describe = result_describe.group('describe')
            
            print(f'找到 {len(img_urls)} 张图片')
            print(f'商品描述: {global_describe[:100]}...')
            
            # 开始处理图片和发布
            process_images_with_progress(img_urls)
        else:
            messagebox.showerror('错误', f'获取商品详情失败：{detail_response.status_code}')
    except Exception as e:
        messagebox.showerror('错误', f'获取商品详情失败：{e}')

# ==================== 发布商品 ====================

def publish():
    """发布商品到Agiso"""
    global goofish_cookies, agiso_cookies, user_authorization
    global global_image_ids, global_oss_keys, global_agiso_img_urls, global_describe
    global province_code, city_code, district_code
    
    selected_item = tree.selection()
    
    if not selected_item:
        messagebox.showwarning('警告', '请先选择一行数据')
        return
    
    item_values = tree.item(selected_item, 'values')
    
    # 调试信息
    print('\n==== 调试信息 ====')
    print(f'图片ID列表: {global_image_ids}')
    print(f'OSS Keys: {global_oss_keys}')
    print(f'图片URL列表: {global_agiso_img_urls}')
    print(f'商品描述: {global_describe[:100]}...')
    print(f'选中的商品值: {item_values}')
    print(f'地区代码: {province_code}, {city_code}, {district_code}')
    
    # 构建图片列表（API 字段名: 'imgList'，对象格式, 最多 9 张）
    max_images = 9
    valid_ids = [iid for iid in global_image_ids if iid][:max_images]
    valid_urls = [u for i, u in enumerate(global_agiso_img_urls) if i < len(valid_ids) and global_image_ids[i]]
    valid_oss = [o for i, o in enumerate(global_oss_keys) if i < len(valid_ids) and global_image_ids[i]]
    if not valid_ids:
        messagebox.showerror('错误', '没有有效的已上传图片！请先获取商品图片。')
        return
    images_list_data = [
        {'imageId': str(valid_ids[i]), 'agisoImgUrl': str(valid_urls[i]) if i < len(valid_urls) else '', 'ossKey': str(valid_oss[i]) if i < len(valid_oss) else ''}
        for i in range(len(valid_ids))
    ]
    print(f'  [publish] imgList ({len(images_list_data)} 项)')
    
    # 提取价格
    price = item_values[1].replace('¥', '').strip()
    
    try:
        float(price)
    except ValueError:
        messagebox.showerror('错误', f'无效的价格格式: {price}')
        return
    
    # 构建地区列表
    division_list = [province_code, city_code]
    if district_code:
        division_list.append(district_code)
    
    # 构建发布参数
    payload = {
        'itemBizType': 2,
        'goodsType': [99, 'eebfcb1cd9bfce8e212e21d79c0262e7', 'eebfcb1cd9bfce8e212e21d79c0262e7', '3cdbae6d47df9251a7f7e02f36b0b49a'],
        'spBizType': '99',
        'categoryId': 50023914,
        'channelCatId': '3cdbae6d47df9251a7f7e02f36b0b49a',
        'pvList': [],
        'virtual': False,
        'title': item_values[0][:30],
        'desc': global_describe.replace('\\n', '\n') if global_describe else '',
        'divisionIdList': division_list,
        'freeShipping': True,
        'reservePrice': price,
        'originalPrice': 0,
        'quantity': 9999,
        'stuffStatus': 0,
        'transportFee': 0,
        'itemSkuList': [],
        'categoryName': '其他/电子资料/电子资料/电子资料',
        'imgList': images_list_data
    }
    
    payload_str = json.dumps(payload, ensure_ascii=False, indent=2)
    
    print('\n==== 请求信息 ====')
    print(f'请求 URL: https://aldsidle.agiso.com/api/GoodsManage/Publish')
    
    # 更新请求头
    agiso_publish_headers['Authorization'] = user_authorization
    
    print(f'请求头: {json.dumps(agiso_publish_headers, indent=2)}')
    print(f'请求体: {payload_str}')
    
    url = 'https://aldsidle.agiso.com/api/GoodsManage/Publish'
    
    try:
        response = requests.post(
            url,
            cookies=agiso_cookies,
            headers=agiso_publish_headers,
            data=payload_str,
            verify=False
        )
        
        print('\n==== 响应信息 ====')
        print(f'状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        print(f'响应体: {response.text[:1000]}')
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                # Agiso 响应结构: {"succeeded": true, "data": {"isSuccess": true/false, ...}}
                # 注意: 顶层 "succeeded" 仅表示 HTTP 请求成功，不代表发布成功
                data_field_pf = response_data.get('data', {})
                if data_field_pf.get('isSuccess') or response_data.get('isSuccess'):
                    print(f'\n==== 发布成功 ====')
                    print(f'响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)[:500]}')
                    messagebox.showinfo('成功', '商品发布成功！')
                    
                    # 收藏原商品
                    save_good()
                    
                    # 清理临时PNG文件
                    delete_png_files_recursively()
                else:
                    error_msg = data_field_pf.get('errorMsg', '') or response_data.get('message', '未知错误')
                    print(f'\n==== 发布失败 ====')
                    print(f'错误信息: {error_msg}')
                    print(f'完整响应: {response.text[:2000]}')
                    messagebox.showerror('发布失败', f'发布失败: {error_msg}')
            except json.JSONDecodeError:
                print(f'\n==== 解析错误 ====')
                print(f'原始响应: {response.text[:2000]}')
                messagebox.showerror('发布失败', '发布失败：服务器响应解析错误')
        else:
            print(f'\n==== 请求失败 ====')
            print(f'响应内容: {response.text[:2000]}')
            messagebox.showerror('发布失败', f'发布失败：HTTP {response.status_code}')
    except Exception as e:
        print(f'\n==== 请求异常 ====')
        print(f'异常信息: {str(e)}')
        messagebox.showerror('发布失败', f'发布失败：{str(e)}')

# ==================== 收藏商品 ====================

def save_good():
    """收藏商品"""
    selected_item = tree.selection()
    
    if not selected_item:
        messagebox.showwarning('警告', '请先选择一行数据')
        return
    
    item_values = tree.item(selected_item, 'values')
    
    save_data = {"itemId": str(item_ids[tree.index(selected_item[0])])}
    save_data_str = json.dumps(save_data)
    
    app_key = '34839810'
    timestamp = get_current_timestamp_milliseconds()
    token = goofish_cookies.get('_m_h5_tk', '').split('_')[0]
    sign = get_md5_hash_string(f'{token}&{timestamp}&{app_key}&{save_data_str}')
    
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
        'needLoginPC': 'true',
        'api': 'mtop.taobao.idle.collect.item',
        'sessionOption': 'AutoLoginOnly',
        'spm_cnt': 'a21ybx.item.0.0'
    }
    
    url = 'https://h5api.m.goofish.com/h5/mtop.taobao.idle.collect.item/1.0/'
    
    try:
        response = requests.post(
            url,
            params=params,
            cookies=goofish_cookies,
            headers=goofish_headers,
            data={'data': save_data_str},
            verify=False
        )
        
        if response.status_code == 200:
            print(f'[+]收藏商品成功')
            print(f'[+]相应内容: {response.text[:500]}')
        else:
            print(f'[-]收藏商品失败: {response.status_code}')
    except Exception as e:
        print(f'[-]收藏商品异常: {e}')

# ==================== 地区设置对话框 ====================

def set_region_codes():
    """设置发布地区的对话框"""
    dialog = tk.Toplevel()
    dialog.title('设置发布地区')
    dialog.geometry('350x450')
    
    # 省份
    province_frame = ttk.Frame(dialog)
    province_frame.pack(fill='x', padx=20, pady=10)
    
    ttk.Label(province_frame, text='省份代码:').pack(side='left')
    province_entry = ttk.Entry(province_frame)
    province_entry.insert(0, province_code)
    province_entry.pack(side='left', fill='x', expand=True, padx=5)
    
    # 城市
    city_frame = ttk.Frame(dialog)
    city_frame.pack(fill='x', padx=20, pady=10)
    
    ttk.Label(city_frame, text='城市代码:').pack(side='left')
    city_entry = ttk.Entry(city_frame)
    city_entry.insert(0, city_code)
    city_entry.pack(side='left', fill='x', expand=True, padx=5)
    
    # 区域
    district_frame = ttk.Frame(dialog)
    district_frame.pack(fill='x', padx=20, pady=10)
    
    ttk.Label(district_frame, text='区域代码:').pack(side='left')
    district_entry = ttk.Entry(district_frame)
    district_entry.insert(0, district_code)
    district_entry.pack(side='left', fill='x', expand=True, padx=5)
    
    # 帮助信息
    help_text = ('常用地区代码参考：\n'
                 '广东省东莞市: 440000-441900\n'
                 '北京市朝阳区: 110000-110100-110105\n'
                 '上海市浦东新区: 310000-310100-310115\n'
                 '深圳市南山区: 440000-440300-440305\n'
                 '广州市天河区: 440000-440100-440106\n'
                 '特别注意：\n'
                 '部分地区需要填写区域代码，部分地区不需要！\n'
                 '本程序的商品默认发布地区为广东省东莞市！')
    
    help_label = ttk.Label(dialog, text=help_text, justify='left')
    help_label.pack(padx=20, pady=10)
    
    # 保存按钮
    def save_codes():
        global province_code, city_code, district_code
        province_code = province_entry.get().strip()
        city_code = city_entry.get().strip()
        district_code = district_entry.get().strip()
        messagebox.showinfo('成功', '地区代码已保存！')
        dialog.destroy()
    
    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)
    
    ttk.Button(button_frame, text='保存', command=save_codes).pack(side='left', padx=5)
    ttk.Button(button_frame, text='取消', command=dialog.destroy).pack(side='left', padx=5)
