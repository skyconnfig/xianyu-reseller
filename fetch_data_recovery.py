"""
fetch_data() 函数恢复 - 基于反汇编分析
"""

def fetch_data(keyword):
    """抓取数据（核心函数）"""
    # 验证关键词
    if not keyword:
        keyword = entry_keyword.get().strip()
    
    if not keyword:
        messagebox.showerror('错误', '请输入有效的关键词')
        return
    
    # 构建请求参数
    payload = build_payload(page_number, keyword)
    data_str = json.dumps(payload)
    print(data_str)
    
    # 提取 token
    token = gofish_cookies.get('_m_h5_tk', '').split('_')[0]
    
    # 生成签名
    timestamp = get_current_timestamp_milliseconds()
    app_key = '34839810'
    sign = get_md5_hash_string(f'{token}&{timestamp}&{app_key}&{data_str}')
    
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
    response = requests.post(
        url,
        params=params,
        cookies=goffish_cookies,
        headers=goffish_headers,
        data={'data': data_str},
        verify=False
    )
    
    if response.status_code != 200:
        messagebox.showerror('错误', f'请求失败：{response.status_code}')
        return
    
    # 解析响应
    json_data = response.json()
    outer_data = json_data.get('data', {})
    result_list = outer_data.get('resultList', [])
    
    # 处理每个商品
    for item in result_list:
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
        second_utparams = args.get('utparam', {})
        second_args = second_utparams.get('args', {})
        first_utparams = second_args.get('utparam', {})
        first_args = first_utparams.get('args', {})
        
        item_id = first_args.get('item_id', '')
        ccat_id = first_args.get('ccat_id', '')
        
        # 构建URL
        url = f'https://www.goofish.com/item?id={item_id}'
        
        # 格式化价格
        formatted_price = f'¥{price / 100:.2f}' if isinstance(price, (int, float)) else '¥0.00'
        
        # 添加到全局列表
        prices.append(formatted_price)
        titles.append(title)
        want_counts.append(want_count)
        item_ids.append(item_id)
        ccat_ids.append(ccat_id)
        urls.append(url)
        user_nicks.append(user_nick)
        areas.append(area)
        
        # 添加到表格
        tree.insert('', 'end', values=(
            formatted_price,
            title,
            want_count,
            user_nick,
            area
        ))
    
    messagebox.showinfo('完成', f'成功抓取 {len(result_list)} 条数据！')
