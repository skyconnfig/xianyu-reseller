"""
Agiso API 独立测试脚本
直接调用 Agiso API 测试不同的 imagesList 字段名和格式
"""

import requests
import json
import os
import io
from PIL import Image
import urllib3
urllib3.disable_warnings()

# ==================== 用户提供的凭证 ====================

AGISO_COOKIES = {
    'UM_distinctid': '19efece95f31ac8-06ca4873e3d87e8-26061051-1bcab9-19efece95f42804',
    'perf_dv6Tr4n': '1',
    'acw_tc': '276208fe17829098160436612ec932b76fd17d1ee3d00440f58d68f96c0d24',
    'CNZZDATA1280882580': '2097473239-1782391412-%7C1782909630',
}

AUTHORIZATION = 'Bearer 3EB936291B65B39C834BDB8C5BFB7A57:5dc6f02d051b46a5866e5fe67db1833d888a6b7528f44ea0870509257fa643c2'

UPLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua-platform': '"Windows"',
    'Authorization': AUTHORIZATION,
    'x_front': '1',
    'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://aldsidle.agiso.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://aldsidle.agiso.com/',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}

PUBLISH_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
    'Accept': 'application/json, text/plain, */*',
    'sec-ch-ua-platform': '"Windows"',
    'Authorization': AUTHORIZATION,
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
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}

PROXIES = {'http': None, 'https': None}


def create_test_image():
    """创建一个简单的测试图片"""
    img = Image.new('RGB', (300, 300), color=(100, 150, 200))
    # 加点内容
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    draw.text((50, 130), "TEST IMAGE", fill=(255, 255, 255))
    draw.rectangle([50, 50, 250, 250], outline=(255, 255, 255), width=2)
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def test_upload():
    """测试图片上传"""
    print("\n" + "=" * 60)
    print("步骤1: 上传测试图片")
    print("=" * 60)
    
    url = 'https://aldsidle.agiso.com/api/GoodsManage/MediaUpload'
    img_buf = create_test_image()
    
    files = {'files': ('test_img.png', img_buf, 'image/png')}
    
    print(f"URL: {url}")
    print(f"Authorization: {AUTHORIZATION[:30]}...")
    
    try:
        response = requests.post(
            url,
            cookies=AGISO_COOKIES,
            headers=UPLOAD_HEADERS,
            files=files,
            verify=False,
            proxies=PROXIES,
            timeout=30,
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:1000]}")
        
        if response.status_code == 200:
            data = response.json()
            raw_data = data.get('data', {})
            inner_data = raw_data.get('data', raw_data)
            
            image_id = inner_data.get('imageId', '')
            oss_key = inner_data.get('ossKey', '')
            agiso_url = inner_data.get('agisoImgUrl', '')
            
            print(f"\n✅ 上传成功:")
            print(f"  imageId: {image_id} (type={type(image_id).__name__})")
            print(f"  ossKey:  {oss_key}")
            print(f"  agisoImgUrl: {agiso_url}")
            
            return {
                'imageId': str(image_id),
                'ossKey': str(oss_key),
                'agisoImgUrl': str(agiso_url),
            }
        else:
            print(f"❌ 上传失败: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None


def test_publish_with_format(img_info, field_name, image_format, label):
    """用指定的字段名和格式尝试发布"""
    print(f"\n{'─' * 60}")
    print(f"测试: {label}")
    print(f"  字段名: {field_name}")
    print(f"  格式: {image_format}")
    print(f"{'─' * 60}")
    
    # 构建图片列表
    if image_format == 'object_list':
        # 对象列表格式
        img_list = [{
            'imageId': img_info['imageId'],
            'agisoImgUrl': img_info['agisoImgUrl'],
            'ossKey': img_info['ossKey'],
        }]
    elif image_format == 'object_list_int_id':
        # imageId 转 int
        img_list = [{
            'imageId': int(img_info['imageId']),
            'agisoImgUrl': img_info['agisoImgUrl'],
            'ossKey': img_info['ossKey'],
        }]
    elif image_format == 'object_list_no_url':
        # 只有 imageId 和 ossKey
        img_list = [{
            'imageId': img_info['imageId'],
            'ossKey': img_info['ossKey'],
        }]
    elif image_format == 'string_list':
        # 纯字符串 ID 列表
        img_list = [img_info['imageId']]
    elif image_format == 'url_list':
        # URL 列表
        img_list = [img_info['agisoImgUrl']]
    else:
        print(f"  未知格式: {image_format}")
        return None
    
    # 构建 payload（基础部分）
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
        'title': '测试商品请勿购买',
        'desc': '测试商品描述',
        'divisionIdList': ['440000', '441900'],
        'freeShipping': True,
        'reservePrice': '1',
        'originalPrice': 0,
        'quantity': 9999,
        'stuffStatus': 0,
        'transportFee': 0,
        'itemSkuList': [],
        'categoryName': '其他/电子资料/电子资料/电子资料',
        field_name: img_list,  # 动态字段名
    }
    
    payload_str = json.dumps(payload, ensure_ascii=False)
    print(f"  {field_name} 内容: {json.dumps(img_list, ensure_ascii=False)}")
    print(f"  payload 长度: {len(payload_str)} bytes")
    
    url = 'https://aldsidle.agiso.com/api/GoodsManage/Publish'
    
    try:
        response = requests.post(
            url,
            cookies=AGISO_COOKIES,
            headers=PUBLISH_HEADERS,
            data=payload_str,
            verify=False,
            proxies=PROXIES,
            timeout=30,
        )
        
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:1500]}")
        
        if response.status_code == 200:
            data = response.json()
            data_field = data.get('data', {})
            is_success = data_field.get('isSuccess', False)
            error_msg = data_field.get('errorMsg', '') or data.get('message', '')
            
            if is_success:
                print(f"  ✅✅✅ 成功! 这个格式可行!")
                return True
            else:
                print(f"  ❌ 失败: {error_msg}")
                return False
        else:
            print(f"  ❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        return False


def main():
    print("=" * 60)
    print("Agiso API 独立测试 — 找出正确的 imagesList 格式")
    print("=" * 60)
    
    # 步骤1: 上传图片
    img_info = test_upload()
    if not img_info:
        print("\n❌ 图片上传失败，无法继续测试")
        return
    
    # 步骤2: 尝试各种格式
    results = []
    
    # 格式1: imagesList + 对象列表 (当前代码)
    r = test_publish_with_format(img_info, 'imagesList', 'object_list', 
                                  'imagesList + 对象列表(string id)')
    results.append(('imagesList + 对象(string)', r))
    
    # 格式2: imgList + 对象列表 (原始反汇编字段名)
    r = test_publish_with_format(img_info, 'imgList', 'object_list',
                                  'imgList + 对象列表(string id)')
    results.append(('imgList + 对象(string)', r))
    
    # 格式3: images + 对象列表
    r = test_publish_with_format(img_info, 'images', 'object_list',
                                  'images + 对象列表(string id)')
    results.append(('images + 对象(string)', r))
    
    # 格式4: imgList + 字符串列表
    r = test_publish_with_format(img_info, 'imgList', 'string_list',
                                  'imgList + 字符串ID列表')
    results.append(('imgList + 字符串列表', r))
    
    # 格式5: imagesList + 对象列表(int id)
    r = test_publish_with_format(img_info, 'imagesList', 'object_list_int_id',
                                  'imagesList + 对象列表(int id)')
    results.append(('imagesList + 对象(int)', r))
    
    # 格式6: imgList + 对象列表(无 agisoImgUrl)
    r = test_publish_with_format(img_info, 'imgList', 'object_list_no_url',
                                  'imgList + 对象(无url)')
    results.append(('imgList + 对象(无url)', r))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    for label, r in results:
        status = "✅ 成功" if r else "❌ 失败"
        print(f"  {status}  {label}")
    
    # 找到成功的格式
    success_formats = [label for label, r in results if r]
    if success_formats:
        print(f"\n🎉 可用格式: {success_formats[0]}")
    else:
        print(f"\n⚠️ 所有格式均失败，可能需要进一步调查")


if __name__ == '__main__':
    main()
