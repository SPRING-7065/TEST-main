"""
任务持久化存储
负责将任务列表读写到 tasks.json
"""
import json
import os
from typing import List
from models.task import Task
 
def get_tasks_file_path() -> str:
    """获取tasks.json的绝对路径（与exe同级）"""
    import sys

    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "tasks.json")
 
def load_tasks() -> List[Task]:
    """从JSON文件加载所有任务"""
    path = get_tasks_file_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Task.from_dict(t) for t in data.get("tasks", [])]
    except Exception as e:
        print(f"[警告] 读取任务配置文件失败：{e}，将使用空任务列表")
        return []
 
def save_tasks(tasks: List[Task]) -> None:
    """将任务列表保存到JSON文件"""
    path = get_tasks_file_path()
    data = {"tasks": [t.to_dict() for t in tasks]}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[错误] 保存任务配置文件失败：{e}")
 
def update_task_status(task_id: str, status: str, run_time: str) -> None:
    """更新单个任务的运行状态（不重写整个文件逻辑，直接reload+save）"""
    tasks = load_tasks()
    for t in tasks:
        if t.task_id == task_id:
            t.last_run_status = status
            t.last_run_time = run_time
            break
    save_tasks(tasks)