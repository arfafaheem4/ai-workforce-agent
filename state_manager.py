# state_manager.py

execution_state = {
    "leave_applied": False,
    "handover_logged": False,
    "email_sent": False,
    "document_created": False,
    "meeting_scheduled": False,
}

relevant_states = set()
_current_goal = ""          # ← add this
_last_action = None
_last_action_params = {}

def set_current_goal(goal: str):
    global _current_goal
    _current_goal = goal

def get_current_goal() -> str:
    return _current_goal

def set_state(key: str, value: bool):
    execution_state[key] = value
    relevant_states.add(key)

def get_state(key: str) -> bool:
    return execution_state.get(key, False)

def get_full_state() -> dict:
    if relevant_states:
        return {k: v for k, v in execution_state.items() if k in relevant_states}
    return execution_state.copy()

def reset_state():
    for key in execution_state:
        execution_state[key] = False
    relevant_states.clear()

def set_last_action(action: str, params: dict):
    global _last_action, _last_action_params
    _last_action = action
    _last_action_params = params

def get_last_action():
    return _last_action, _last_action_params