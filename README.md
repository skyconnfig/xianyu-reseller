# 闲鱼转卖助手 2.0 | Xianyu Reseller Assistant

> 基于 PyInstaller 打包的 Python 桌面应用逆向工程 —— 从 `.exe` 反编译恢复完整源码并重新构建

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能特性

- **闲鱼商品数据抓取**：通过关键词搜索闲鱼商品，支持分页抓取
- **Cookie 验证管理**：支持闲鱼 Cookie 和阿奇索（Agiso）平台认证
- **一键转卖上架**：对接阿奇索（Aldsidle Agiso）API 实现商品自动上架
- **多格式导出**：支持 CSV / Excel 数据导出
- **图片批量下载**：多线程下载商品图片
- **配置持久化**：保存/加载 Cookie 和搜索配置
- **页数可调搜索**：支持自定义搜索页数（默认 20 页），进度实时显示
- **试用过期机制**：首次运行起 30 天试用期，过期前 5 天弹窗提醒

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.13 | 核心运行时 |
| Tkinter/ttk | GUI 界面 |
| Requests | HTTP 网络请求 |
| imageio / Pillow | 图片处理 |
| openpyxl | Excel 导出（可选） |

## 项目背景

本项目是从 `咸鱼转卖助手2.0【鱼小铺版】.exe` （PyInstaller 打包）通过以下步骤逆向恢复：

1. **解包**：使用 `pyinstxtractor.py` 解压 EXE
2. **定位主程序**：找到主入口文件 `cest.pyc`
3. **修复文件头**：修正 Magic Number 使其可被 Python 加载
4. **反汇编分析**：利用 `dis` + `marshal` 模块逐函数反汇编字节码
5. **源码重建**：基于反汇编输出手工恢复完整源码

## 快速开始

### 环境要求

- Python 3.13+
- Windows / Linux / macOS

### 安装与运行

```bash
# 克隆仓库
git clone https://github.com/skyconnfig/xianyu-reseller.git
cd xianyu-reseller

# 创建虚拟环境
python -m venv venv

# Windows 激活
venv\Scripts\activate
# Linux/Mac 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 运行程序
python main.py
```

### 打包为 EXE

```bash
# 确保已激活虚拟环境
pip install pyinstaller

# 编译单文件 EXE（无控制台窗口）
pyinstaller --onefile --windowed --name "闲鱼转卖助手" \
  --collect-all imageio \
  --hidden-import requests --hidden-import urllib3 \
  --hidden-import imageio --hidden-import PIL \
  --hidden-import asyncio --hidden-import concurrent.futures \
  main.py
```

> 输出文件在 `dist/闲鱼转卖助手.exe`，可直接分发给 Windows 用户运行。

## 使用说明

1. 启动程序后，点击 **「验证Cookie」** 按钮
2. 按提示依次输入：
   - **闲鱼 Cookie**（从浏览器 F12 开发者工具获取）
   - **阿奇索 Cookie**
   - **阿奇索 Authorization**
3. 在关键词输入框输入搜索词，**页数**框设置抓取页数（默认 20）
4. 点击 **「搜索全部」** 开始抓取，进度条实时显示
5. 选择商品后可进行：
   - **打开链接** → 查看原商品详情
   - **下载图片** → 批量下载商品图
   - **导出 CSV/Excel** → 导出抓取的数据
   - **一键转卖（选中项）** → 批量上架到阿奇索

## 项目结构

```
├── main.py                 # 主程序源码
├── requirements.txt        # Python 依赖清单
├── build_config.ini        # PyInstaller 编译配置
├── build.bat               # Windows 编译脚本
├── build.sh                # Linux/Mac 编译脚本
├── fetch_data_recovery.py  # 核心抓取函数独立恢复文件
├── publish_functions.py    # 发布 / 转卖函数
├── test_*.py               # API 测试脚本
└── README.md               # 本文件
```

## 核心模块说明

| 函数 | 功能 |
|------|------|
| `validate_xianyu_cookies()` | 验证闲鱼 Cookie 有效性 |
| `validate_agiso_cookies()` | 验证阿奇索 Cookie + Token |
| `get_and_validate_cookies()` | 三步验证流程（闲鱼→阿奇索→Auth） |
| `fetch_data()` | 核心数据抓取（签名+分页+解析） |
| `build_payload()` | 构建 API 请求参数 |
| `download_images()` | 多线程图片下载 |
| `export_to_csv/excel()` | 数据导出 |
| `batch_resell_selected()` | 批量转卖上架 |
| `check_license()` | 试用期 30 天过期检查 |

## 常见问题

### Q: 验证阿奇索时报 ProxyError？
**A**: 这是网络代理导致的连接问题。代码中已设置 `proxies={'http': None, 'https': None}` 绕过系统代理。如果仍有问题，请检查：
- 本地代理服务是否正常运行
- 阿奇索平台是否需要特殊网络环境

### Q: Cookie 如何获取？
**A**: 
1. 浏览器登录对应平台
2. F12 打开开发者工具 → Network（网络）
3. 刷新页面，任选一个请求 → Headers → Cookie 字段
4. 复制完整 Cookie 字符串粘贴到程序中

### Q: 打包 EXE 运行时提示 "No package metadata found for imageio"？
**A**: 这是 PyInstaller 没有打包 imageio 元数据导致的。编译时加上 `--collect-all imageio` 参数即可解决。

## 许可证

MIT License

## 免责声明

本项目仅供学习研究使用。请遵守相关平台的用户协议和法律法规。
