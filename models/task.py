"""
任务数据模型
定义一个完整自动化任务的数据结构
"""
from dataclasses import dataclass, field
from typing import List, Optional
from models.step import Step
import uuid
 
@dataclass
class ScheduleConfig:
    """调度配置"""
    enabled: bool = False
    schedule_type: str = "once"      # once / daily / weekly / monthly
    run_time: str = "09:00"          # HH:MM格式
    weekdays: List[int] = field(default_factory=list)   # 0=周一...6=周日
    monthdays: List[int] = field(default_factory=list)  # 1-31
 
    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "schedule_type": self.schedule_type,
            "run_time": self.run_time,
            "weekdays": self.weekdays,
            "monthdays": self.monthdays,
        }
 
    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleConfig":
        return cls(
            enabled=data.get("enabled", False),
            schedule_type=data.get("schedule_type", "once"),
            run_time=data.get("run_time", "09:00"),
            weekdays=data.get("weekdays", []),
            monthdays=data.get("monthdays", []),
        )
 
@dataclass
class Task:
    """完整任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "新建任务"
    description: str = ""
    steps: List[Step] = field(default_factory=list)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    max_retries: int = 3
    timeout_per_step: int = 120
    save_dir_override: str = ""      # 留空则使用默认路径
    fresh_session: bool = False      # True=每次运行前清除Cookie，避免登录状态残留导致第二次失败
    last_run_time: str = ""
    last_run_status: str = ""        # success / failed / running / never
 
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "schedule": self.schedule.to_dict(),
            "max_retries": self.max_retries,
            "timeout_per_step": self.timeout_per_step,
            "save_dir_override": self.save_dir_override,
            "last_run_time": self.last_run_time,
            "last_run_status": self.last_run_status,
        }
 
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        steps = [Step.from_dict(s) for s in data.get("steps", [])]
        schedule = ScheduleConfig.from_dict(data.get("schedule", {}))
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())[:8]),
            name=data.get("name", "新建任务"),
            description=data.get("description", ""),
            steps=steps,
            schedule=schedule,
            max_retries=data.get("max_retries", 3),
            timeout_per_step=data.get("timeout_per_step", 120),
            save_dir_override=data.get("save_dir_override", ""),
            last_run_time=data.get("last_run_time", ""),
            last_run_status=data.get("last_run_status", "never"),
        )