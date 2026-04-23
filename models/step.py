"""
步骤数据模型
定义每一个自动化操作步骤的数据结构
"""
import os
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
 
class StepType(str, Enum):
    """步骤类型枚举"""
    OPEN_URL = "open_url"           # 打开网址
    CLICK = "click"                 # 点击元素
    INPUT = "input"                 # 输入文本
    SELECT = "select"               # 下拉选择
    WAIT = "wait"                   # 等待秒数
    WAIT_ELEMENT = "wait_element"   # 等待元素出现
    DOWNLOAD_CLICK = "download_click"  # 点击并拦截下载
    SCROLL = "scroll"               # 滚动页面
    CLEAR_INPUT = "clear_input"     # 清空输入框
    # v1.3.0
    UPLOAD_FILE = "upload_file"     # 上传文件（智能查找隐藏 input）
    EXTRACT_DOM = "extract_dom"     # 抽取页面元素到变量
    READ_EXCEL = "read_excel"       # 读取 Excel 内容到变量
    APPEND_EXCEL = "append_excel"   # 追加一行/多行到 Excel

# 步骤类型的中文显示名
STEP_TYPE_LABELS = {
    StepType.OPEN_URL: "🌐 打开网址",
    StepType.CLICK: "🖱️ 点击元素",
    StepType.INPUT: "⌨️ 输入文本",
    StepType.SELECT: "📋 下拉选择",
    StepType.WAIT: "⏱️ 等待秒数",
    StepType.WAIT_ELEMENT: "👁️ 等待元素出现",
    StepType.DOWNLOAD_CLICK: "⬇️ 点击下载",
    StepType.SCROLL: "📜 滚动页面",
    StepType.CLEAR_INPUT: "🗑️ 清空输入框",
    StepType.UPLOAD_FILE: "📤 上传文件",
    StepType.EXTRACT_DOM: "🔎 抽取元素到变量",
    StepType.READ_EXCEL: "📊 读取 Excel",
    StepType.APPEND_EXCEL: "📝 追加 Excel",
}
 
@dataclass
class Step:
    """单个操作步骤"""
    step_type: str = StepType.CLICK          # 步骤类型
    description: str = ""                    # 用户自定义描述（中文）
    selector: str = ""                       # CSS选择器（由可视化拾取自动填入）
    selector_type: str = "css"               # 选择器类型: css / xpath / text
    value: str = ""                          # 输入值/URL/等待秒数
    timeout: int = 120                       # 超时秒数
    optional: bool = False                   # 是否可选步骤（失败不中断）
    # v1.3.0：类型特定配置（UPLOAD_FILE/EXTRACT_DOM/READ_EXCEL/APPEND_EXCEL 用）
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_type": self.step_type,
            "description": self.description,
            "selector": self.selector,
            "selector_type": self.selector_type,
            "value": self.value,
            "timeout": self.timeout,
            "optional": self.optional,
            "extra": dict(self.extra) if self.extra else {},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Step":
        return cls(
            step_type=data.get("step_type", StepType.CLICK),
            description=data.get("description", ""),
            selector=data.get("selector", ""),
            selector_type=data.get("selector_type", "css"),
            value=data.get("value", ""),
            timeout=data.get("timeout", 120),
            optional=data.get("optional", False),
            extra=dict(data.get("extra") or {}),
        )

    def get_display_name(self) -> str:
        """获取步骤的中文显示名称"""
        label = STEP_TYPE_LABELS.get(self.step_type, self.step_type)
        if self.description:
            return f"{label}：{self.description}"
        if self.value and self.step_type == StepType.OPEN_URL:
            return f"{label}：{self.value[:50]}"
        # v1.3.0 新类型按 extra 拼摘要
        if self.step_type == StepType.UPLOAD_FILE:
            fp = (self.extra.get("file_path") or "").strip()
            if fp:
                return f"{label}：{fp[:40]}"
        if self.step_type == StepType.EXTRACT_DOM:
            vn = (self.extra.get("var_name") or "").strip()
            attr = self.extra.get("attribute") or "innerText"
            if vn:
                return f"{label}：{self.selector[:24]} → ${{{vn}}} ({attr})"
        if self.step_type == StepType.READ_EXCEL:
            fp = os.path.basename((self.extra.get("file_path") or "").strip()) or "?"
            rng = self.extra.get("range") or "all"
            vn = self.extra.get("var_name") or ""
            return f"{label}：{fp}!{rng} → ${{{vn}}}"
        if self.step_type == StepType.APPEND_EXCEL:
            fp = os.path.basename((self.extra.get("file_path") or "").strip()) or "?"
            n = len(self.extra.get("mappings") or [])
            return f"{label}：{fp}（{n} 列）"
        if self.selector:
            return f"{label}（{self.selector[:30]}）"
        return label