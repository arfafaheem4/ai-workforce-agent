import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def plan_goal(goal):

    prompt = f"""
You are an AI Planner Agent.

Break the goal into small, clear, actionable steps.

Return ONLY valid JSON in this format, no explanation, no markdown:
{{"tasks": ["task 1", "task 2", "task 3"]}}

Goal: {goal}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()

    # Clean markdown if model adds it
    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()

    # Extract JSON safely
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end != 0:
        text = text[start:end]

    try:
        data = json.loads(text)
        return data["tasks"]
    except json.JSONDecodeError:
        print("Failed to parse JSON from planner:")
        print(text)
        return []