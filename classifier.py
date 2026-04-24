import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

VALID_TYPES = [
    "communication", "document_work", "meeting_management",
    "research", "planning", "hr_task", "data_processing", "general"
]

def classify_task(task):

    prompt = f"""
You are a workforce AI classifier.

Classify this task into exactly ONE of these categories:
communication, document_work, meeting_management, research, planning, hr_task, data_processing, general

Return ONLY valid JSON, no explanation, no markdown:
{{"type": "category_here"}}

Task: {task}
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
        task_type = data.get("type", "general").lower()
        if task_type not in VALID_TYPES:
            return "general"
        return task_type
    except json.JSONDecodeError:
        return "general"  # Safe fallback