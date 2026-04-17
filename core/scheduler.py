"""
任务调度器模块
负责：根据任务调度配置触发任务执行
"""

import datetime
import threading
from typing import Callable, Dict, List, Optional

from models.task import Task
from core import logger


class TaskScheduler:
    """简单的任务调度器，用于定时触发任务执行"""

    def __init__(self, task_runner: Callable[[Task], None], poll_interval: float = 15.0):
        self.task_runner = task_runner
        self.poll_interval = poll_interval
        self._tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_run_at: Dict[str, datetime.date] = {}

    def start(self) -> None:
        """启动后台调度线程"""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="TaskScheduler")
        self._thread.start()
        logger.log_info("调度器已启动")

    def stop(self) -> None:
        """停止后台调度线程"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.log_info("调度器已停止")

    def register_all_tasks(self, tasks: List[Task]) -> None:
        """注册所有启用调度的任务"""
        with self._lock:
            self._tasks = {task.task_id: task for task in tasks if task.schedule.enabled}
            logger.log_info(f"调度器已注册 {len(self._tasks)} 个启用任务")

    def register_task(self, task: Task) -> None:
        """注册单个任务"""
        with self._lock:
            if task.schedule.enabled:
                self._tasks[task.task_id] = task
                logger.log_info(f"调度器已注册任务：{task.name}")
            else:
                self._tasks.pop(task.task_id, None)

    def unregister_task(self, task_id: str) -> None:
        """取消注册任务"""
        with self._lock:
            if self._tasks.pop(task_id, None) is not None:
                self._last_run_at.pop(task_id, None)
                logger.log_info(f"调度器已取消注册任务：{task_id}")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._check_due_tasks()
            except Exception as exc:
                logger.log_error(f"调度器检查任务时发生异常：{exc}")
            self._stop_event.wait(self.poll_interval)

    def _check_due_tasks(self) -> None:
        now = datetime.datetime.now()
        tasks = []
        with self._lock:
            tasks = list(self._tasks.values())

        for task in tasks:
            if self._is_task_due(task, now):
                logger.log_info(f"调度器触发任务：{task.name}")
                try:
                    self.task_runner(task)
                except Exception as exc:
                    logger.log_error(f"调度器执行任务异常：{exc}")
                self._last_run_at[task.task_id] = now.date()

    def _is_task_due(self, task: Task, now: datetime.datetime) -> bool:
        schedule = task.schedule
        if not schedule.enabled:
            return False

        try:
            run_time = datetime.datetime.strptime(schedule.run_time, "%H:%M").time()
        except Exception:
            return False

        run_dt = datetime.datetime.combine(now.date(), run_time)
        delta = now - run_dt
        if delta < datetime.timedelta(0) or delta > datetime.timedelta(minutes=self.poll_interval + 1):
            return False

        last_run_date = self._last_run_at.get(task.task_id)
        if last_run_date == now.date():
            return False

        if schedule.schedule_type == "once":
            if task.last_run_time:
                return False
            return delta >= datetime.timedelta(0)

        if schedule.schedule_type == "daily":
            return delta >= datetime.timedelta(0)

        if schedule.schedule_type == "weekly":
            if now.weekday() not in schedule.weekdays:
                return False
            return delta >= datetime.timedelta(0)

        if schedule.schedule_type == "monthly":
            if now.day not in schedule.monthdays:
                return False
            return delta >= datetime.timedelta(0)

        return False
