# 闲鱼转卖助手 2.0（鱼小铺版） | Xianyu Reseller Assistant

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
pip install -r requirements.txt

# 运行程序
python main.py
```

### 重新打包为 EXE

```bash
# 安装 pyinstaller
pip install pyinstaller

# 执行编译脚本
# Windows:
build.bat
# Linux/Mac:
bash build.sh
```

## 使用说明

1. 启动程序后，点击 **「验证Cookie」** 按钮
2. 按提示依次输入：
   - **闲鱼 Cookie**（从浏览器 F12 开发者工具获取）
   - **阿奇索 Cookie**
   - **阿奇索 Authorization**
3. 验证通过后，输入关键词点击 **「抓取数据」**
4. 选择商品后可进行：
   - **打开链接** → 查看原商品详情
   - **下载图片** → 批量下载商品图
   - **导出 CSV/Excel** → 导出抓取的数据

## 项目结构

```
├── main.py                 # 主程序源码（已恢复）
├── requirements.txt        # Python 依赖清单
├── build_config.ini        # PyInstaller 编译配置
├── build.bat               # Windows 编译脚本
├── build.sh                # Linux/Mac 编译脚本
├── assets/                 # 资源文件
├── config/                 # 配置文件目录
├── fetch_data_recovery.py  # 核心抓取函数独立恢复文件
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

## 许可证

MIT License

## 免责声明

本项目仅供学习研究使用。请遵守相关平台的用户协议和法律法规。
