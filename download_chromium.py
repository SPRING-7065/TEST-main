"""
下载便携版 Chromium 供 PyInstaller 打包使用。

使用 Chromium 官方 snapshot 而非复制系统 Chrome，优势：
  - 自带所有依赖 DLL，不依赖用户机器的 VC++ Runtime 版本
  - 真正的便携包，在任意 Windows 机器上解压即用
  - 版本固定，行为可预期，不受用户 Chrome 更新影响
"""
import os
import sys
import shutil
import urllib.request
import zipfile

SNAPSHOT_BASE = (
    "https://commondatastorage.googleapis.com"
    "/chromium-browser-snapshots/Win_x64"
)
DEST_DIR = os.path.join(os.getcwd(), "browser")
ZIP_PATH = os.path.join(os.getcwd(), "chrome-win.zip")


def get_latest_version() -> str:
    url = f"{SNAPSHOT_BASE}/LAST_CHANGE"
    print(f"Fetching latest Chromium version from: {url}")
    with urllib.request.urlopen(url, timeout=30) as resp:
        version = resp.read().decode().strip()
    print(f"Latest snapshot: {version}")
    return version


def download_with_progress(url: str, dest: str):
    print(f"Downloading: {url}")

    def reporthook(count, block_size, total_size):
        downloaded = count * block_size
        if total_size > 0:
            pct = min(downloaded * 100 // total_size, 100)
            mb = downloaded / 1024 / 1024
            total_mb = total_size / 1024 / 1024
            print(f"\r  {pct}%  {mb:.1f}/{total_mb:.1f} MB", end="", flush=True)

    urllib.request.urlretrieve(url, dest, reporthook)
    print()


def main():
    # 获取最新版本号
    version = get_latest_version()
    zip_url = f"{SNAPSHOT_BASE}/{version}/chrome-win.zip"

    # 清理旧目录
    if os.path.exists(DEST_DIR):
        print(f"Removing old browser dir: {DEST_DIR}")
        shutil.rmtree(DEST_DIR)

    # 下载
    download_with_progress(zip_url, ZIP_PATH)
    print(f"Downloaded: {ZIP_PATH}")

    # 解压
    print("Extracting...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(os.getcwd())

    # chrome-win.zip 解压后是 chrome-win/ 文件夹，重命名为 browser/
    extracted = os.path.join(os.getcwd(), "chrome-win")
    if os.path.exists(extracted):
        os.rename(extracted, DEST_DIR)
    else:
        # 兜底：找任何 chrome 开头的目录
        for name in os.listdir(os.getcwd()):
            full = os.path.join(os.getcwd(), name)
            if name.startswith("chrome") and os.path.isdir(full) and full != DEST_DIR:
                os.rename(full, DEST_DIR)
                break

    # 清理 zip
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    # 验证
    chrome_exe = os.path.join(DEST_DIR, "chrome.exe")
    if not os.path.exists(chrome_exe):
        print(f"ERROR: chrome.exe not found in {DEST_DIR}")
        if os.path.exists(DEST_DIR):
            print("Contents:", os.listdir(DEST_DIR))
        sys.exit(1)

    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, dn, fn in os.walk(DEST_DIR)
        for f in fn
    )
    print(f"Done. Chromium {version} ready at: {DEST_DIR}  ({total/1024/1024:.1f} MB)")


if __name__ == "__main__":
    main()
