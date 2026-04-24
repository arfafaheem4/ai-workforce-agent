# app.py
import streamlit as st
from planner import plan_goal
from executor import run_tasks
from memory.memory_store import save_goal, save_tasks, update_task_status, log_interaction, get_full_memory, clear_memory
from tools.retriever import load_documents, retrieve
from reflector import reflect
from state_manager import reset_state, get_full_state
from classifier import classify_task
from tools.tools import execute_tool

# ── Page Config ────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Workforce Agent",
    page_icon="🤖",
    layout="wide"
)

# ── Load Knowledge Base Once ───────────────────────────────────
@st.cache_resource
def init_knowledge_base():
    load_documents()

init_knowledge_base()

# ── Session State Init ─────────────────────────────────────────
if "results_visible" not in st.session_state:
    st.session_state.results_visible = False
if "output" not in st.session_state:
    st.session_state.output = {}

# ── Header ─────────────────────────────────────────────────────
st.title("🤖 Autonomous AI Workforce Agent")
st.caption("Plan → Execute → Reflect | Powered by Groq + LLaMA 3.3")
st.divider()

# ── Sidebar ────────────────────────────────────────────────────
# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.header("🧠 Memory")

    memory = get_full_memory()
    last_goal = memory.get("current_goal")
    last_tasks = memory.get("tasks", [])
    all_goals = memory.get("all_goals", [])

    if last_goal:
        st.subheader("📋 Current Goal")
        st.info(last_goal)

        if last_tasks:
            st.subheader("📝 Tasks")
            for t in last_tasks:
                icon = "✅" if t["status"] == "done" else "⏳"
                st.write(f"{icon} {t['task']}")
    else:
        st.info("No previous goal in memory.")

    # Show all past goals
    if all_goals and len(all_goals) > 1:
        st.divider()
        st.subheader("📚 Goal History")
        for g in reversed(all_goals[-5:]):  # Show last 5
            st.caption(f"🕐 {g['timestamp'][:16].replace('T', ' ')}")
            st.write(f"• {g['goal']}")

    st.divider()
    if st.button("🗑️ Clear Memory"):
        clear_memory()
        st.session_state.results_visible = False
        st.session_state.output = {}
        st.success("Memory cleared!")

# ── Main Input ─────────────────────────────────────────────────
st.subheader("💬 Enter Your Goal")
goal = st.text_input(
    label="goal",
    placeholder="e.g. prepare client meeting / apply leave for Monday / what is leave policy",
    label_visibility="collapsed"
)
run_button = st.button("🚀 Run Agent", type="primary", use_container_width=True)

# ── Run Agent ──────────────────────────────────────────────────
if run_button and goal.strip():

    goal_lower = goal.lower()
    st.session_state.results_visible = True
    st.session_state.output = {"goal": goal, "type": None}

    # ── Memory Recall ──────────────────────────────────────────
    if any(phrase in goal_lower for phrase in [
        "what was i working on", "continue", "what did i do",
        "previous goal", "last task", "remind me",
        "what was i doing", "show my tasks"
    ]):
        memory = get_full_memory()
        st.session_state.output["type"] = "recall"
        st.session_state.output["last_goal"] = memory.get("current_goal")
        st.session_state.output["last_tasks"] = memory.get("tasks", [])

    # ── Knowledge Query ────────────────────────────────────────
    elif any(phrase in goal_lower for phrase in [
        "what is", "what are", "tell me about", "explain",
        "how many", "what does", "policy", "rules", "guidelines"
    ]):
        result = retrieve(goal)
        log_interaction("user", goal)
        log_interaction("agent", result)
        st.session_state.output["type"] = "knowledge"
        st.session_state.output["answer"] = result

    # ── New Goal ───────────────────────────────────────────────
    else:
        reset_state()
        from state_manager import set_current_goal
        set_current_goal(goal)
        save_goal(goal)
        log_interaction("user", goal)

        # Plan
        tasks = plan_goal(goal)
        save_tasks(tasks)

        # Execute
        results = []
        for i, task in enumerate(tasks):
            task_type = classify_task(task)
            result = execute_tool(task_type, task)
            results.append({
                "task": task,
                "type": task_type,
                "result": result
            })

        for i in range(len(results)):
            update_task_status(i, "done")

        log_interaction("agent", f"Completed {len(results)} tasks for: {goal}")

        # Reflect
        current_state = get_full_state()
        reflection = reflect(goal, tasks, results, current_state)

        st.session_state.output["type"] = "goal"
        st.session_state.output["tasks"] = tasks
        st.session_state.output["results"] = results
        st.session_state.output["reflection"] = reflection

# ── Display Results (stays visible) ───────────────────────────
if st.session_state.results_visible and st.session_state.output:

    out = st.session_state.output
    st.divider()

    # ── Recall Output ──────────────────────────────────────────
    if out["type"] == "recall":
        st.subheader("🧠 Memory Recall")
        if out.get("last_goal"):
            st.success(f"**Last Goal:** {out['last_goal']}")
            for t in out.get("last_tasks", []):
                icon = "✅" if t["status"] == "done" else "⏳"
                st.write(f"{icon} {t['task']}")
        else:
            st.warning("No previous goal found in memory.")

    # ── Knowledge Output ───────────────────────────────────────
    elif out["type"] == "knowledge":
        st.subheader("🔍 Knowledge Base Answer")
        st.markdown(out["answer"])

    # ── Goal Output ────────────────────────────────────────────
    elif out["type"] == "goal":
        col1, col2 = st.columns(2)

        # Planning
        with col1:
            st.subheader("🗂️ Plan")
            for i, task in enumerate(out["tasks"]):
                st.write(f"**{i+1}.** {task}")

        # State
        with col2:
            st.subheader("📊 Execution State")
            current_state = get_full_state()  # Now only returns relevant states
            # FIXED - else is outside the for loop
            if current_state:
                for k, v in current_state.items():
                    icon = "✅" if v else "❌"
                    st.write(f"{icon} {k.replace('_', ' ').title()}")
            else:
                st.info("No tracked actions for this goal.")
        st.divider()

        # Execution Results
        st.subheader("⚙️ Execution Results")
        for i, r in enumerate(out["results"]):
            with st.expander(f"Task {i+1}: {r['task']}"):
                st.caption(f"🏷️ Type: `{r['type']}`")
                st.write(r["result"])

        st.divider()

        # Reflection
        st.subheader("🔍 Reflection Report")
        reflection = out["reflection"]

        col1, col2 = st.columns(2)
        with col1:
            if reflection["goal_achieved"]:
                st.success(f"✅ {reflection['overall_status']}")
            else:
                st.warning(f"⚠️ {reflection['overall_status']}")
        with col2:
            st.metric("Completion", f"{reflection['completion_percentage']}%")

        if reflection["what_went_well"]:
            st.markdown("**✅ What Went Well:**")
            for point in reflection["what_went_well"]:
                st.write(f"  • {point}")

        if reflection.get("gaps"):
            st.markdown("**⚠️ Gaps Found:**")
            for gap in reflection["gaps"]:
                st.write(f"  • {gap}")

        if reflection.get("suggestions"):
            st.markdown("**💡 Suggestions:**")
            for s in reflection["suggestions"]:
                st.write(f"  • {s}")

        if reflection["goal_achieved"]:
            st.success("🎯 Goal fully achieved!")