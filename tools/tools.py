# tools/tools.py
import json
import os
from datetime import datetime
from tools.retriever import retrieve
from state_manager import set_state, get_state

LEAVE_FILE = "memory/leave_requests.json"
TASKS_LOG_FILE = "memory/tasks_log.json"

def _load_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)

def _save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

def apply_leave(task: str) -> str:
    # Check state — not session flag
    if get_state("leave_applied"):
        return "[HR Tool] ℹ️ Leave already applied — skipping duplicate."

    task_lower = task.lower()

    days = 1
    for word in task_lower.split():
        if word.isdigit():
            days = int(word)
            break
    if "3 days" in task_lower: days = 3
    elif "2 days" in task_lower: days = 2
    elif "week" in task_lower: days = 5

    if "emergency" in task_lower: leave_type = "Emergency"
    elif "sick" in task_lower: leave_type = "Sick"
    elif "annual" in task_lower: leave_type = "Annual"
    else: leave_type = "General"

    leave_request = {
        "id": f"LR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "task_description": task,
        "leave_type": leave_type,
        "days_requested": days,
        "status": "Approved",
        "submitted_at": datetime.now().isoformat()
    }

    requests = _load_json(LEAVE_FILE)
    requests.append(leave_request)
    _save_json(LEAVE_FILE, requests)

    # Update state
    set_state("leave_applied", True)

    return (
        f"[HR Tool] ✅ Leave Applied Successfully!\n"
        f"   📋 ID: {leave_request['id']}\n"
        f"   🏖️  Type: {leave_type}\n"
        f"   📅 Days: {days}\n"
        f"   ✅ Status: Approved"
    )

def log_handover_task(task: str) -> str:
    if get_state("handover_logged"):
        return "[Task Manager] ℹ️ Handover already logged — skipping duplicate."

    handover = {
        "id": f"HO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "task": task,
        "type": "Handover",
        "status": "Logged",
        "created_at": datetime.now().isoformat()
    }

    logs = _load_json(TASKS_LOG_FILE)
    logs.append(handover)
    _save_json(TASKS_LOG_FILE, logs)

    # Update state
    set_state("handover_logged", True)

    return (
        f"[Task Manager] ✅ Handover Task Logged!\n"
        f"   📋 ID: {handover['id']}\n"
        f"   📝 Task: {task}\n"
        f"   ✅ Status: Logged"
    )

def execute_tool(task_type: str, task: str) -> str:
    task_lower = task.lower()

    if task_type == "communication":
        set_state("email_sent", True)
        return f"[Email Tool] 📧 Drafted communication for: {task}"

    elif task_type == "document_work":
        set_state("document_created", True)
        return f"[Doc Tool] 📄 Created/updated document for: {task}"

    elif task_type == "meeting_management":
        set_state("meeting_scheduled", True)
        return f"[Calendar Tool] 📅 Scheduled/organized meeting for: {task}"

    elif task_type == "research":
        return retrieve(task)

    elif task_type == "planning":
        return f"[Planner Tool] 🗂️ Created structured plan for: {task}"

    elif task_type == "hr_task":
        if any(w in task_lower for w in ["leave", "day off", "vacation", "sick"]):
            return apply_leave(task)
        elif any(w in task_lower for w in ["handover", "hand over", "log task", "delegate"]):
            return log_handover_task(task)
        else:
            return f"[HR Tool] 📋 Processed HR request: {task}"

    elif task_type == "data_processing":
        return f"[Data Tool] 📊 Processed data for: {task}"

    else:
        if "handover" in task_lower:
            return log_handover_task(task)
        return f"[General Tool] ⚙️ Handled: {task}"