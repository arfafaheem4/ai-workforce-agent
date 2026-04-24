# state_manager.py

execution_state = {
    "leave_applied": False,
    "handover_logged": False,
    "email_sent": False,
    "document_created": False,
    "meeting_scheduled": False,
}

# Track which states are relevant for current goal
relevant_states = set()

def set_state(key: str, value: bool):
    execution_state[key] = value
    relevant_states.add(key)  # Mark as relevant when used

def get_state(key: str) -> bool:
    return execution_state.get(key, False)

def get_full_state() -> dict:
    # Only return states that were actually used
    if relevant_states:
        return {k: v for k, v in execution_state.items() if k in relevant_states}
    return execution_state.copy()

def reset_state():
    for key in execution_state:
        execution_state[key] = False
    relevant_states.clear()  # Clear relevance tracking

def get_state_summary() -> str:
    lines = []
    for key, value in execution_state.items():
        status = "✅ Done" if value else "❌ Not done"
        lines.append(f"  {key}: {status}")
    return "\n".join(lines)