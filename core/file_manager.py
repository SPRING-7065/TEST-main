"""
文件管理模块
负责：下载路径生成、防覆盖文件命名、目录创建
"""
import os
import sys
import datetime
import re
from typing import Optional
 
def get_app_root() -> str:
    """
    获取程序根目录
    - PyInstaller打包后：exe所在目录
    - 开发模式：项目根目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后，sys.executable是exe路径
        return os.path.dirname(sys.executable)
    else:
        # 开发模式，返回项目根目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 
def get_download_dir(custom_dir: str = "") -> str:
    """
    获取今日下载目录
    默认路径：<程序根目录>/下载数据库/YYYY-MM-DD/
    如果custom_dir不为空，则使用自定义路径下的YYYY-MM-DD子目录
    """
    today_str = datetime.date.today().strftime("%Y-%m-%d")
 
    if custom_dir and os.path.isdir(os.path.dirname(custom_dir)):
        base = custom_dir
    else:
        base = os.path.join(get_app_root(), "下载数据库")
 
    target_dir = os.path.join(base, today_str)
    os.makedirs(target_dir, exist_ok=True)
    return target_dir
 
def generate_safe_filename(task_name: str, original_filename: str = "",
                           extension: str = "") -> str:
    """
    生成防覆盖的安全文件名
    格式：{任务名称}_{时间戳}.{后缀}
    例如：销售报表下载_20231024_153022.xlsx
 
    Args:
        task_name: 任务名称
        original_filename: 原始文件名（用于提取后缀）
        extension: 强制指定后缀（优先级高于original_filename）
    """
    # 清理任务名称中的非法字符
    safe_task_name = re.sub(r'[\\/:*?"<>|]', '_', task_name)
 
    # 确定文件后缀
    if extension:
        ext = extension if extension.startswith('.') else f'.{extension}'
    elif original_filename:
        _, ext = os.path.splitext(original_filename)
        ext = ext.lower() if ext else '.bin'
    else:
        ext = '.bin'
 
    # 生成时间戳
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
 
    return f"{safe_task_name}_{timestamp}{ext}"
 
def get_full_save_path(task_name: str, original_filename: str = "",
                       extension: str = "", custom_dir: str = "") -> str:
    """
    获取完整的文件保存路径（目录+文件名）
    """
    download_dir = get_download_dir(custom_dir)
    filename = generate_safe_filename(task_name, original_filename, extension)
    return os.path.join(download_dir, filename)
 
def ensure_dir_exists(path: str) -> None:
    """确保目录存在，不存在则创建"""
    os.makedirs(path, exist_ok=True)
 
def get_extension_from_content_type(content_type: str) -> str:
    """从HTTP Content-Type推断文件后缀"""
    mapping = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
        "application/vnd.ms-excel": ".xls",
        "application/pdf": ".pdf",
        "text/csv": ".csv",
        "application/zip": ".zip",
        "application/x-zip-compressed": ".zip",
        "application/json": ".json",
        "text/plain": ".txt",
        "application/octet-stream": ".bin",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/msword": ".doc",
    }
    # 处理带参数的content-type，如 "application/json; charset=utf-8"
    base_type = content_type.split(";")[0].strip().lower()
    return mapping.get(base_type, ".bin")
