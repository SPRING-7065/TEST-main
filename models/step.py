"""
步骤数据模型
定义每一个自动化操作步骤的数据结构
"""
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
 
    def to_dict(self) -> dict:
        return {
            "step_type": self.step_type,
            "description": self.description,
            "selector": self.selector,
            "selector_type": self.selector_type,
            "value": self.value,
            "timeout": self.timeout,
            "optional": self.optional,
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
        )
 
    def get_display_name(self) -> str:
        """获取步骤的中文显示名称"""
        label = STEP_TYPE_LABELS.get(self.step_type, self.step_type)
        if self.description:
            return f"{label}：{self.description}"
        if self.value and self.step_type == StepType.OPEN_URL:
            return f"{label}：{self.value[:50]}"
        if self.selector:
            return f"{label}（{self.selector[:30]}）"
        return label