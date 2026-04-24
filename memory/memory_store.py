# memory/memory_store.py
import json
import os
from datetime import datetime

MEMORY_FILE = "memory/memory.json"

def _load():
    if not os.path.exists(MEMORY_FILE):
        return {"current_goal": None, "tasks": [], "history": [], "context": {}, "all_goals": []}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def _save(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_goal(goal: str):
    data = _load()
    data["current_goal"] = goal
    # Keep history of all goals
    if "all_goals" not in data:
        data["all_goals"] = []
    data["all_goals"].append({
        "goal": goal,
        "timestamp": datetime.now().isoformat()
    })
    data["history"].append({
        "type": "goal",
        "content": goal,
        "timestamp": datetime.now().isoformat()
    })
    _save(data)

def get_goal():
    return _load().get("current_goal")

def save_tasks(tasks: list):
    data = _load()
    data["tasks"] = [{"id": i, "task": t, "status": "pending"} for i, t in enumerate(tasks)]
    _save(data)

def get_tasks():
    return _load().get("tasks", [])

def update_task_status(task_id: int, status: str):
    data = _load()
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
    _save(data)

def save_context(key: str, value):
    data = _load()
    data["context"][key] = value
    _save(data)

def get_context(key: str):
    return _load()["context"].get(key)

def get_full_memory():
    return _load()

def get_all_goals():
    return _load().get("all_goals", [])

def log_interaction(role: str, content: str):
    data = _load()
    data["history"].append({
        "type": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    _save(data)

def clear_memory():
    _save({"current_goal": None, "tasks": [], "history": [], "context": {}, "all_goals": []})