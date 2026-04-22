"""
全局任务并发控制
基于 BoundedSemaphore，可在运行时动态调整上限。
"""
import threading

_DEFAULT_LIMIT = 2
_MAX_LIMIT = 8
_MIN_LIMIT = 1

_lock = threading.Lock()
_semaphore = threading.Semaphore(_DEFAULT_LIMIT)
_current_limit = _DEFAULT_LIMIT


def get_limit() -> int:
    return _current_limit


def set_limit(new_limit: int) -> None:
    """运行时调整并发上限。
    通过释放/获取差额槽位实现，正在执行中的任务不受影响。
    """
    global _semaphore, _current_limit
    new_limit = max(_MIN_LIMIT, min(_MAX_LIMIT, int(new_limit)))
    with _lock:
        delta = new_limit - _current_limit
        if delta > 0:
            for _ in range(delta):
                _semaphore.release()
        elif delta < 0:
            # 后续任务需要 acquire 时自然受新上限约束；
            # 不强制 acquire 已有槽位，避免阻塞调整线程
            for _ in range(-delta):
                # 非阻塞，能拿就拿走，拿不到说明槽位已被占用，
                # 待占用线程 release 时新上限自动生效
                _semaphore.acquire(blocking=False)
        _current_limit = new_limit


def acquire() -> None:
    _semaphore.acquire()


def release() -> None:
    try:
        _semaphore.release()
    except ValueError:
        pass
