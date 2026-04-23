# WebAutoDownloader

网页自动取数助手是一个 Windows 桌面网页自动取数工具，支持任务配置、动态变量、定时执行和后台下载。

## 前置依赖

- **Google Chrome**：必须预先安装（程序通过 CDP 协议驱动系统已安装的 Chrome）。下载：https://www.google.cn/chrome/
- **系统密钥库**（v1.2.0+ 登录模板功能用，普通使用不需要）：Windows 自带 Credential Manager，macOS 自带 Keychain，无需额外配置
- **openpyxl**（v1.3.0+ Excel 读写步骤用，requirements.txt 已包含）

## 运行

1. 安装依赖：
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
2. 启动程序：
   ```bash
   python main.py
   ```

## 打包

Windows 下使用 PyInstaller：

```bash
pyinstaller build.spec
```

打包后生成目录：`dist/WebAutoDownloader`。

## 开发与 CI

本仓库已配置 GitHub Actions 云端打包流程：
- 触发条件：`push` 到 `main` 分支，或手动 workflow_dispatch
- 构建产物：`WebAutoDownloader_v1.3.0_*.zip`

## 目录说明

- `main.py`：程序入口
- `core/`：核心逻辑（执行引擎、日志、路径、调度）
- `gui/`：界面实现
- `storage/`：任务持久化存储
- `build.spec`：PyInstaller 打包配置
- `.github/workflows/build_windows.yml`：Windows 云打包流程
