from classifier import classify_task
from tools import execute_tool
from tools.retriever import retrieve

def run_tasks(tasks):

    results = []

    print("\nExecutor Started\n")

    for i, task in enumerate(tasks):

        print(f"Task {i+1}: {task}")

        task_type = classify_task(task)

        print(f"Classified as: {task_type}")
        if task_type == "research":
            result = retrieve(task)
            print(f"Result: [RAG] {result}\n")
        else:
            result = execute_tool(task_type, task)
            print(f"Result: {result}\n")

        results.append({
            "task": task,
            "type": task_type,
            "result": result
        })

    return results

