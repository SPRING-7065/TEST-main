"""
动态变量解析引擎
支持 [TODAY]、[TODAY-X]、[TODAY+X] 等时间占位符
"""
import re
import datetime
from typing import Optional, Dict
 
# 支持的日期格式选项
DATE_FORMATS = {
    "yyyy-MM-dd HH:mm:ss": "%Y-%m-%d %H:%M:%S",
    "yyyy-MM-dd": "%Y-%m-%d",
    "yyyy/MM/dd": "%Y/%m/%d",
    "yyyyMMdd": "%Y%m%d",
    "MM/dd/yyyy": "%m/%d/%Y",
    "dd/MM/yyyy": "%d/%m/%Y",
    "yyyy年MM月dd日": "%Y年%m月%d日",
}
 
# 默认格式
DEFAULT_DATE_FORMAT = "yyyy-MM-dd"
 
def parse_variables(text: str, date_format: str = DEFAULT_DATE_FORMAT,
                    execution_date: Optional[datetime.date] = None,
                    runtime_vars: Optional[Dict[str, str]] = None) -> str:
    """
    解析文本中的所有动态变量占位符

    支持的占位符：
    - [TODAY]           → 今天日期
    - [TODAY-X]         → 今天往前推X天
    - [TODAY+X]         → 今天往后推X天
    - [YESTERDAY]       → 昨天（等同于 [TODAY-1]）
    - [MONTH_START]     → 本月第一天
    - [MONTH_END]       → 本月最后一天
    - [YEAR_START]      → 今年第一天
    - [NOW_TIMESTAMP]   → 当前时间戳（yyyyMMdd_HHmmss格式，用于文件命名）
    - [NOW]             → 当前时间（yyyy-MM-dd HH:mm:ss，v1.3.0 起用于 Excel 归档）
    - ${var_name}       → 运行时变量插值（v1.3.0 起，包括 ${last_download} ${download_N} 与 EXTRACT_DOM/READ_EXCEL 写入的变量）

    Args:
        text: 包含占位符的原始文本
        date_format: 日期输出格式（使用DATE_FORMATS中的key）
        execution_date: 执行日期（默认为今天，测试时可指定）
        runtime_vars: 运行时变量字典（v1.3.0），用于 ${name} 插值；
                      未命中的 ${name} 原样保留，方便用户发现拼写错误

    Returns:
        替换后的文本
    """
    if not text:
        return text

    # v1.3.0：先做 ${name} 插值（让插值结果再经过 [XXX] 时间占位替换）
    if runtime_vars:
        def _sub_runtime(m: re.Match) -> str:
            key = m.group(1)
            if key in runtime_vars:
                return str(runtime_vars[key])
            return m.group(0)
        text = re.sub(r'\$\{([\w\u4e00-\u9fa5]+)\}', _sub_runtime, text)

    today = execution_date or datetime.date.today()
    fmt = DATE_FORMATS.get(date_format, "%Y-%m-%d")
 
    # 处理 [TODAY-X] 和 [TODAY+X]
    def replace_today_offset(match: re.Match) -> str:
        operator = match.group(1)  # + 或 -
        days = int(match.group(2))
        if operator == "-":
            target_date = today - datetime.timedelta(days=days)
        else:
            target_date = today + datetime.timedelta(days=days)
        return _format_date(target_date, fmt)
 
    # 先处理带偏移的 [TODAY±X]
    text = re.sub(
        r'\[TODAY([+\-])(\d+)\]',
        replace_today_offset,
        text,
        flags=re.IGNORECASE
    )
 
    # 处理 [TODAY] 本身
    text = re.sub(
        r'\[TODAY\]',
        _format_date(today, fmt),
        text,
        flags=re.IGNORECASE
    )
 
    # 处理 [YESTERDAY]
    yesterday = today - datetime.timedelta(days=1)
    text = re.sub(
        r'\[YESTERDAY\]',
        _format_date(yesterday, fmt),
        text,
        flags=re.IGNORECASE
    )
 
    # 处理 [MONTH_START] - 本月第一天
    month_start = today.replace(day=1)
    text = re.sub(
        r'\[MONTH_START\]',
        _format_date(month_start, fmt),
        text,
        flags=re.IGNORECASE
    )
 
    # 处理 [MONTH_END] - 本月最后一天
    if today.month == 12:
        month_end = today.replace(day=31)
    else:
        month_end = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)
    text = re.sub(
        r'\[MONTH_END\]',
        _format_date(month_end, fmt),
        text,
        flags=re.IGNORECASE
    )
 
    # 处理 [YEAR_START] - 今年第一天
    year_start = today.replace(month=1, day=1)
    text = re.sub(
        r'\[YEAR_START\]',
        _format_date(year_start, fmt),
        text,
        flags=re.IGNORECASE
    )
 
    # 处理 [NOW_TIMESTAMP] - 精确时间戳
    now_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    text = re.sub(r'\[NOW_TIMESTAMP\]', now_ts, text, flags=re.IGNORECASE)

    # 处理 [NOW] - 可读时间戳，便于 Excel 归档
    now_readable = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = re.sub(r'\[NOW\]', now_readable, text, flags=re.IGNORECASE)

    return text
 
def _format_date(date: datetime.date, fmt: str) -> str:
    """将date对象格式化为字符串，支持datetime格式（补充00:00:00）"""
    if "%H" in fmt or "%M" in fmt or "%S" in fmt:
        # 需要时间部分，补充00:00:00
        dt = datetime.datetime.combine(date, datetime.time.min)
        return dt.strftime(fmt)
    return date.strftime(fmt)
 
def preview_variables(text: str, date_format: str = DEFAULT_DATE_FORMAT) -> str:
    """
    预览变量解析结果（用于GUI实时预览）
    """
    try:
        return parse_variables(text, date_format)
    except Exception as e:
        return f"[预览失败: {e}]"
 
def get_available_placeholders() -> list:
    """返回所有可用占位符的说明列表"""
    return [
        ("[TODAY]", "今天的日期，例如：2024-01-15"),
        ("[TODAY-1]", "昨天的日期，例如：2024-01-14"),
        ("[TODAY-7]", "7天前的日期，例如：2024-01-08"),
        ("[TODAY-30]", "30天前的日期"),
        ("[TODAY+1]", "明天的日期"),
        ("[YESTERDAY]", "昨天（同 [TODAY-1]）"),
        ("[MONTH_START]", "本月第一天，例如：2024-01-01"),
        ("[MONTH_END]", "本月最后一天，例如：2024-01-31"),
        ("[YEAR_START]", "今年第一天，例如：2024-01-01"),
        ("[NOW_TIMESTAMP]", "当前时间戳，例如：20240115_093022（用于文件命名）"),
        ("[NOW]", "当前时间，例如：2024-01-15 09:30:22（用于 Excel 归档）"),
        ("${last_download}", "最近一次下载到的文件绝对路径（v1.3.0）"),
        ("${download_1}", "第 1 个下载文件路径，依次类推 ${download_2} ${download_3}（v1.3.0）"),
        ("${自定义变量名}", "EXTRACT_DOM/READ_EXCEL 步骤写入的变量；中文变量名也支持（v1.3.0）"),
    ]