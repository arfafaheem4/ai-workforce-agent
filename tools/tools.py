# tools/tools.py
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from tools.retriever import retrieve
from state_manager import set_state, get_state, set_last_action

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

def apply_leave(task: str, context: str = "") -> str:
    if get_state("leave_applied"):
        return "[HR Tool] ℹ️ Leave already applied — skipping duplicate."

    # ── Use original goal for day detection ───────────────────
    from state_manager import get_current_goal
    combined = (task + " " + context + " " + get_current_goal()).lower()

    if "3 days" in combined or "three days" in combined: days = 3
    elif "2 days" in combined or "two days" in combined: days = 2
    elif "4 days" in combined or "four days" in combined: days = 4
    elif "5 days" in combined or "five days" in combined: days = 5
    elif "week" in combined: days = 5
    else:
        days = 1
        for word in combined.split():
            if word.isdigit():
                days = int(word)
                break

    if "emergency" in combined: leave_type = "Emergency"
    elif "sick" in combined: leave_type = "Sick"
    elif "annual" in combined: leave_type = "Annual"
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

    set_state("leave_applied", True)
    set_last_action("apply_leave", {"days": days, "leave_type": leave_type})

    return (
        f"[HR Tool] ✅ Leave Applied Successfully!\n"
        f"   📋 ID: {leave_request['id']}\n"
        f"   🏖️  Type: {leave_type}\n"
        f"   📅 Days: {days}\n"
        f"   ✅ Status: Approved"
    )

def update_leave(task: str, days: int) -> str:
    """Updates the most recent leave request with new duration."""
    requests = _load_json(LEAVE_FILE)

    if not requests:
        return "[HR Tool] ⚠️ No previous leave request found to update."

    last = requests[-1]
    old_days = last["days_requested"]
    last["days_requested"] = days
    last["updated_at"] = datetime.now().isoformat()
    last["status"] = "Updated & Approved"

    _save_json(LEAVE_FILE, requests)

    set_state("leave_applied", True)
    set_last_action("apply_leave", {"days": days})

    return (
        f"[HR Tool] ✅ Leave Updated Successfully!\n"
        f"   📋 ID: {last['id']}\n"
        f"   📅 Changed: {old_days} day(s) → {days} day(s)\n"
        f"   ✅ Status: Updated & Approved"
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

    set_state("handover_logged", True)
    set_last_action("log_handover", {"task": task})  # ← track action

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
        