"""
凭据加密存储（keyring 包装）

平台后端：
- Windows: Credential Manager (DPAPI 加密，per-user 绑定)
- macOS:   Keychain
- Linux:   Secret Service (GNOME Keyring / KWallet)

存储格式：每个 task_id 对应两条记录
  service = "WebAutoDownloader"
  key     = f"{task_id}:username"  / f"{task_id}:password"
"""
from typing import Optional, Tuple

SERVICE_NAME = "WebAutoDownloader"

# 延迟导入：keyring 在某些极端环境下可能不可用，
# 包内其他模块按需求容错
try:
    import keyring as _keyring
    _AVAILABLE = True
except Exception:
    _keyring = None
    _AVAILABLE = False


def is_available() -> bool:
    """系统密钥库后端是否可用。
    Windows/Mac 上几乎总是 True；CI 容器或精简 Linux 可能 False。
    """
    if not _AVAILABLE:
        return False
    try:
        backend = _keyring.get_keyring()
        # 用模块路径而不是类名判断（Mac/fail/null 后端类名都叫 Keyring）
        mod = type(backend).__module__
        return mod not in ("keyring.backends.fail", "keyring.backends.null")
    except Exception:
        return False


def _u_key(task_id: str) -> str:
    return f"{task_id}:username"


def _p_key(task_id: str) -> str:
    return f"{task_id}:password"


def save_credentials(task_id: str, username: str, password: str) -> bool:
    """保存账号密码到系统密钥库。失败返回 False。"""
    if not _AVAILABLE:
        return False
    try:
        _keyring.set_password(SERVICE_NAME, _u_key(task_id), username or "")
        _keyring.set_password(SERVICE_NAME, _p_key(task_id), password or "")
        return True
    except Exception:
        return False


def get_credentials(task_id: str) -> Optional[Tuple[str, str]]:
    """读取凭据。无任何记录时返回 None；username 或 password 缺失也返回 None。"""
    if not _AVAILABLE:
        return None
    try:
        u = _keyring.get_password(SERVICE_NAME, _u_key(task_id))
        p = _keyring.get_password(SERVICE_NAME, _p_key(task_id))
    except Exception:
        return None
    if u is None or p is None:
        return None
    return (u, p)


def has_credentials(task_id: str) -> bool:
    return get_credentials(task_id) is not None


def delete_credentials(task_id: str) -> None:
    """删除凭据；不存在的记录吞掉异常不报错。"""
    if not _AVAILABLE:
        return
    for key in (_u_key(task_id), _p_key(task_id)):
        try:
            _keyring.delete_password(SERVICE_NAME, key)
        except Exception:
            pass
