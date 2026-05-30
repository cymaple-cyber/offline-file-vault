# 离线文件保险箱

本地离线运行的文件隐私工具箱。无需登录账号、不连接服务器、不上传任何文件，所有操作在本地完成。

## 功能说明

| 功能 | 说明 |
|------|------|
| **文件加密** | AES-256-GCM 加密，PBKDF2HMAC-SHA256 密钥派生，生成 .cysafe 加密文件 |
| **文件解密** | 解密 .cysafe 文件，密码错误或文件篡改时拒绝解密 |
| **哈希校验** | 计算 MD5、SHA-1、SHA-256 哈希值，支持一键复制 |
| **密码生成器** | 使用 secrets 模块生成安全随机密码，支持自定义长度和字符类型 |

## 加密方案

- **算法**: AES-256-GCM（认证加密）
- **密钥派生**: PBKDF2HMAC-SHA256，迭代次数 600,000（符合 OWASP 推荐）
- **随机性**: 每次加密使用随机 Salt（128-bit）和随机 Nonce（96-bit）
- **文件格式**: 自定义 .cysafe 格式，包含 magic header、版本号、salt、nonce、原始文件名、密文和认证标签

## 安装方法

### 环境要求

- Python 3.11+
- 操作系统：Windows 10/11、macOS、Linux

### 安装依赖

```bash
cd 离线文件保险箱
/opt/miniconda3/bin/pip install -r requirements.txt
```

## 运行方法

```bash
/opt/miniconda3/bin/python3 main.py
```

> **macOS 注意**：如果 `python` 命令指向的是托管版 Python（如 WorkBuddy 环境），会因代码签名冲突导致 Qt 插件加载失败。请使用 `/opt/miniconda3/bin/python3`。

## 打包方法

### Windows

```bash
pyinstaller --onefile --windowed --name "离线文件保险箱" --add-data "src:src" main.py
```

### macOS

```bash
pyinstaller --onefile --windowed --name "离线文件保险箱" --add-data "src:src" main.py
```

打包后的可执行文件位于 `dist/` 目录。

## 运行测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
离线文件保险箱/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖清单
├── README.md               # 本文件
├── src/
│   ├── __init__.py
│   ├── app.py              # 应用程序初始化
│   ├── crypto_utils.py     # 加密解密核心模块
│   ├── hash_utils.py       # 哈希校验模块
│   ├── password_utils.py   # 密码生成器模块
│   └── ui/
│       ├── __init__.py
│       └── main_window.py  # 主窗口界面
└── tests/
    ├── __init__.py
    ├── test_crypto_utils.py    # 加密解密测试
    ├── test_hash_utils.py      # 哈希校验测试
    └── test_password_utils.py  # 密码生成器测试
```

## 安全说明

- 本软件完全离线运行，不连接网络，不上传任何文件
- 不保存用户密码，密码仅用于派生加密密钥
- 不使用硬编码密钥
- 使用经过密码学界验证的成熟算法（AES-256-GCM + PBKDF2HMAC-SHA256）
- 不自创加密算法
- 加密文件含认证标签，任何篡改都会导致解密失败

## 用户注意事项

1. **密码丢失无法恢复加密文件。** 请妥善保管密码，本软件不提供密码找回功能。
2. 建议定期备份加密文件和密码。
3. 加密后的 .cysafe 文件可以在不同设备间安全传输。
4. 「加密后删除原文件」选项默认关闭，请在确认加密成功后再手动删除原文件。
5. 当前仅支持文件加密，不支持文件夹加密。

## 许可证

本项目采用 [MIT License](LICENSE) 开源。

## 作者

**Cymaple** — [github.com/cymaple-cyber](https://github.com/cymaple-cyber)
