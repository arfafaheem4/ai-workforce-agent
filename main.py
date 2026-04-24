# main.py
from planner import plan_goal
from executor import run_tasks
from memory.memory_store import save_goal, save_tasks, update_task_status, log_interaction, get_full_memory
from tools.retriever import load_documents, retrieve
from reflector import reflect, print_reflection
from state_manager import reset_state, get_full_state, get_last_action, set_current_goal

MAX_RETRIES = 2

if __name__ == "__main__":

    load_documents()

    goal = input("\nEnter your goal: ")
    goal_lower = goal.lower()

    # ── Memory Recall ──────────────────────────────────────────
    if any(phrase in goal_lower for phrase in [
        "what was i working on", "continue", "what did i do",
        "previous goal", "last task", "what were we doing",
        "remind me", "what was i doing", "show my tasks"
    ]):
        memory = get_full_memory()
        last_goal = memory.get("current_goal")
        last_tasks = memory.get("tasks", [])

        if last_goal:
            print(f"\n📋 Last Goal: {last_goal}\n")
            print("Tasks:")
            for t in last_tasks:
                status_icon = "✅" if t["status"] == "done" else "⏳"
                print(f"  {status_icon} [{t['status']}] {t['task']}")
        else:
            print("\n⚠️ No previous goal found in memory.")

    # ── Direct Knowledge Query ─────────────────────────────────
    elif any(phrase in goal_lower for phrase in [
        "what is", "what are", "tell me about", "explain",
        "how many", "what does", "policy", "rules", "guidelines"
    ]):
        print("\n🔍 Searching knowledge base...\n")
        result = retrieve(goal)
        print(f"📄 Answer:\n{result}")
        log_interaction("user", goal)
        log_interaction("agent", result)

    # ── Follow-up / Context Update ─────────────────────────────
    elif any(phrase in goal_lower for phrase in [
        "actually", "change it to", "make it", "update it",
        "instead", "correction", "modify", "change to"
    ]):
        last_action, last_params = get_last_action()

        if last_action == "apply_leave":
            # Extract new number of days
            days = None
            words = goal_lower.split()
            for word in words:
                if word.isdigit():
                    days = int(word)
                    break
            if "one" in goal_lower: days = 1
            if "two" in goal_lower: days = 2
            if "three" in goal_lower: days = 3
            if "four" in goal_lower: days = 4
            if "five" in goal_lower: days = 5
            if "week" in goal_lower: days = 5

            if days:
                from tools.tools import update_leave
                result = update_leave(goal, days)
                print(f"\n{result}")
                log_interaction("user", goal)
                log_interaction("agent", result)
            else:
                print("\n⚠️ Could not detect number of days. Try: 'make it 3 days leave'")
        else:
            print("\n⚠️ No previous action to update. Please state your full goal.")

    # ── New Goal Flow ──────────────────────────────────────────
    else:
        reset_state()
        set_current_goal(goal)
        save_goal(goal)
        log_interaction("user", goal)

        tasks = plan_goal(goal)
        save_tasks(tasks)

        print("\nGenerated Tasks:\n")
        for i, task in enumerate(tasks):
            print(f"{i+1}. {task}")

        results = run_tasks(tasks)

        for i in range(len(results)):
            update_task_status(i, "done")

        log_interaction("agent", f"Completed {len(results)} tasks for: {goal}")

        print("\nFinal Execution Summary:\n")
        for r in results:
            print(f"- {r['task']} → {r['result']}")

        print(f"\n✅ Goal saved to memory!")

        attempt = 0
        while attempt < MAX_RETRIES:
            print(f"\n⏳ Reflecting on execution... (Attempt {attempt + 1})")
            current_state = get_full_state()
            reflection = reflect(goal, tasks, results, current_state)
            print_reflection(reflection)

            if reflection["goal_achieved"] or reflection["overall_status"] == "Complete":
                print("\n🎯 Goal fully achieved! No further action needed.")
                break

            gaps = reflection.get("gaps", [])
            suggestions = reflection.get("suggestions", [])

            if not gaps:
                print("\n✅ No gaps found. Goal complete!")
                break

            attempt += 1
            if attempt >= MAX_RETRIES:
                print("\n⚠️ Max retries reached. Some gaps may remain.")
                break

            print(f"\n🔄 Gaps found — re-planning to fix them...\n")
            gap_goal = f"Fix these gaps for original goal '{goal}': {', '.join(gaps)}. Suggestions: {', '.join(suggestions)}"
            new_tasks = plan_goal(gap_goal)

            if not new_tasks:
                break

            print("New Tasks to Fix Gaps:\n")
            for i, task in enumerate(new_tasks):
                print(f"{i+1}. {task}")

            new_results = run_tasks(new_tasks)
            tasks = tasks + new_tasks
            results = results + new_results
            save_tasks(tasks)
            for i in range(len(tasks)):
                update_task_status(i, "done")
            log_interaction("agent", f"Re-executed {len(new_tasks)} gap tasks")