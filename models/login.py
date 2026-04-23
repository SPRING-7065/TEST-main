"""
登录模板数据模型
通过录制+回放实现各类站点的自动登录，凭据走 keyring 加密存储。

设计要点：
- LoginAction 是 Step 的子集（只支持 click/input/wait/open_url）
- 用户名/密码 *不存* 在这里，只存 ${username}/${password} 占位符
- 真实凭据由 storage/credentials.py 写入系统密钥库
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class LoginAction:
    """登录流程中的一步操作"""
    action_type: str = "click"     # click | input | wait | open_url
    selector: str = ""
    selector_type: str = "css"     # css | xpath
    value: str = ""                # input 的值；支持 ${username} ${password} 占位符
    wait_after_ms: int = 500       # 此步骤完成后等待毫秒数

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "selector": self.selector,
            "selector_type": self.selector_type,
            "value": self.value,
            "wait_after_ms": self.wait_after_ms,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoginAction":
        return cls(
            action_type=data.get("action_type", "click"),
            selector=data.get("selector", ""),
            selector_type=data.get("selector_type", "css"),
            value=data.get("value", ""),
            wait_after_ms=int(data.get("wait_after_ms", 500)),
        )


@dataclass
class LoginTemplate:
    """登录模板配置"""
    enabled: bool = False
    actions: List[LoginAction] = field(default_factory=list)
    skip_check_selector: str = ""        # 已登录标志元素（找不到 = 未登录）
    skip_check_type: str = "exists"      # exists | text_contains
    skip_check_value: str = ""           # text_contains 时的目标文本
    skip_check_timeout_sec: int = 5      # 检测超时

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "actions": [a.to_dict() for a in self.actions],
            "skip_check_selector": self.skip_check_selector,
            "skip_check_type": self.skip_check_type,
            "skip_check_value": self.skip_check_value,
            "skip_check_timeout_sec": self.skip_check_timeout_sec,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoginTemplate":
        return cls(
            enabled=bool(data.get("enabled", False)),
            actions=[LoginAction.from_dict(a) for a in data.get("actions", [])],
            skip_check_selector=data.get("skip_check_selector", ""),
            skip_check_type=data.get("skip_check_type", "exists"),
            skip_check_value=data.get("skip_check_value", ""),
            skip_check_timeout_sec=int(data.get("skip_check_timeout_sec", 5)),
        )

    def is_configured(self) -> bool:
        """启用且至少有一个动作 + 一个 skip_check 元素"""
        return (
            self.enabled
            and bool(self.actions)
            and bool(self.skip_check_selector)
        )
