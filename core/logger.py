"""
日志系统
支持：GUI实时显示（通过Qt信号）+ 文件持久化写入
所有日志文案均为中文人话，不暴露技术异常
"""
import os
import datetime
from typing import Optional, Callable
 
# 全局日志回调（由GUI注册）
_gui_callback: Optional[Callable[[str], None]] = None
 
def get_log_file_path() -> str:
    """获取run_log.txt的路径（与exe同级）"""
    # 兼容PyInstaller打包后的路径
    if hasattr(__import__('sys'), '_MEIPASS'):
        import sys
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "run_log.txt")
 
def register_gui_callback(callback: Callable[[str], None]) -> None:
    """注册GUI日志回调函数"""
    global _gui_callback
    _gui_callback = callback
 
def _format_message(level: str, message: str) -> str:
    """格式化日志消息"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{now}] [{level}] {message}"
 
def log_info(message: str) -> None:
    """记录普通信息日志"""
    _write_log("信息", message)
 
def log_success(message: str) -> None:
    """记录成功日志"""
    _write_log("✅ 成功", message)
 
def log_warning(message: str) -> None:
    """记录警告日志"""
    _write_log("⚠️ 警告", message)
 
def log_error(message: str) -> None:
    """记录错误日志"""
    _write_log("❌ 错误", message)
 
def _write_log(level: str, message: str) -> None:
    """实际写入日志的内部函数"""
    formatted = _format_message(level, message)
 
    # 写入文件
    try:
        log_path = get_log_file_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass  # 日志写入失败不应该影响主流程
 
    # 推送到GUI
    if _gui_callback:
        try:
            _gui_callback(formatted)
        except Exception:
            pass
 
    # 同时打印到控制台（开发调试用）
    print(formatted)
 
def translate_exception(e: Exception) -> str:
    """
    将技术异常翻译为用户能看懂的中文描述
    这是核心的"人话转换器"
    """
    error_str = str(e).lower()
    error_type = type(e).__name__.lower()
 
    # 超时类
    if "timeout" in error_type or "timeout" in error_str:
        return "网页太卡，等待超过120秒仍未响应"
 
    # 元素未找到
    if "notfound" in error_type or "no such element" in error_str or \
       "element not found" in error_str or "cannot find" in error_str:
        return "在网页上找不到指定的按钮或输入框（可能网页结构已变化）"
 
    # 网络连接
    if "connection" in error_str or "connectionrefused" in error_type or \
       "networkerror" in error_type:
        return "无法连接到目标网站，请检查网络是否正常"
 
    # 浏览器崩溃
    if "browser" in error_str and ("closed" in error_str or "crash" in error_str):
        return "浏览器意外关闭，可能是内存不足"
 
    # 权限问题
    if "permission" in error_str or "access denied" in error_str:
        return "文件保存失败，没有写入权限，请检查保存目录"
 
    # 磁盘空间
    if "disk" in error_str or "no space" in error_str:
        return "磁盘空间不足，无法保存文件"
 
    # 登录失效
    if "login" in error_str or "unauthorized" in error_str or "401" in error_str:
        return "登录状态已失效，请检查账号密码是否正确"
 
    # 默认
    return f"遇到了未知问题（技术细节：{type(e).__name__}）"