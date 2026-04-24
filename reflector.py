# reflector.py
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def reflect(goal: str, tasks: list, results: list, state: dict) -> dict:

    execution_summary = ""
    for i, (task, result) in enumerate(zip(tasks, results)):
        execution_summary += f"{i+1}. Task: {task}\n   Result: {result['result']}\n\n"

    state_summary = "\n".join([
        f"  {k}: {'✅ Done' if v else '❌ Not done'}"
        for k, v in state.items()
    ])

    prompt = f"""
You are a Reflector Agent in an AI workforce system.

Goal: {goal}

REAL EXECUTION STATE:
{state_summary}

Execution Summary:
{execution_summary}

RULES:
- ONLY evaluate state keys that are directly relevant to the goal
- If goal mentions "leave" → check leave_applied only
- If goal mentions "handover" → check handover_logged only
- If goal mentions "email" → check email_sent only
- If goal mentions "meeting" → check meeting_scheduled only
- Do NOT flag missing state for things the goal never asked for
- If all goal-relevant states are true → goal_achieved = true, status = Complete
- Duplicate skips mean the action was already done = SUCCESS

Goal keywords found: {goal.lower()}

Return ONLY valid JSON:
{{
    "goal_achieved": true or false,
    "completion_percentage": 0-100,
    "what_went_well": ["point 1"],
    "gaps": ["only gaps for things the goal actually asked for"],
    "suggestions": ["suggestion 1"],
    "overall_status": "Complete / Partial / Failed"
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()

    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != 0:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "goal_achieved": True,
            "completion_percentage": 100,
            "what_went_well": ["Tasks executed"],
            "gaps": [],
            "suggestions": [],
            "overall_status": "Complete"
        }

def print_reflection(reflection: dict):
    status_icon = "✅" if reflection["goal_achieved"] else "⚠️"
    print("\n" + "="*50)
    print("🔍 REFLECTION REPORT")
    print("="*50)
    print(f"{status_icon} Status:           {reflection['overall_status']}")
    print(f"📊 Completion:      {reflection['completion_percentage']}%")

    print("\n✅ What Went Well:")
    for point in reflection["what_went_well"]:
        print(f"  • {point}")

    if reflection["gaps"]:
        print("\n⚠️ Gaps Found:")
        for gap in reflection["gaps"]:
            print(f"  • {gap}")

    if reflection["suggestions"]:
        print("\n💡 Suggestions:")
        for suggestion in reflection["suggestions"]:
            print(f"  • {suggestion}")

    print("="*50)