
from flask import Flask, render_template, request, redirect, url_for
import json
from pathlib import Path
from datetime import date

app = Flask(__name__)
DATA_FILE = Path(__file__).with_name("tasks.json")

PRIORITIES = {"High", "Medium", "Low"}


def load_tasks():
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            return []

        for task in data:
            if not isinstance(task, dict):
                continue

            task.setdefault("completed", False)
            task.setdefault("priority", "Medium")
            task.setdefault("due_date", "")

        return data

    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_tasks(tasks):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=4)


def valid_due_date(value):
    if not value:
        return ""

    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def normalize_priority(value):
    return value if value in PRIORITIES else "Medium"


@app.route("/")
def dashboard():
    all_tasks = load_tasks()

    query = request.args.get("q", "").strip()
    status = request.args.get("status", "all").lower()

    if status not in ("all", "pending", "completed"):
        status = "all"

    today = date.today().isoformat()

    total = len(all_tasks)
    completed = sum(
        1 for task in all_tasks if task.get("completed", False)
    )
    pending = total - completed
    overdue = sum(
        1 for task in all_tasks
        if not task.get("completed", False)
        and task.get("due_date", "")
        and task["due_date"] < today
    )
    progress = round(completed / total * 100) if total else 0

    filtered_tasks = []

    for task_id, task in enumerate(all_tasks):
        title = str(task.get("task", ""))
        is_completed = bool(task.get("completed", False))

        matches_search = query.lower() in title.lower()
        matches_status = (
            status == "all"
            or (status == "completed" and is_completed)
            or (status == "pending" and not is_completed)
        )

        if matches_search and matches_status:
            filtered_tasks.append((task_id, task))

    return render_template(
        "index.html",
        tasks=filtered_tasks,
        total=total,
        completed=completed,
        pending=pending,
        overdue=overdue,
        progress=progress,
        query=query,
        status=status,
        today=today
    )


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("task", "").strip()
    due_date = valid_due_date(request.form.get("due_date", ""))
    priority = normalize_priority(request.form.get("priority", "Medium"))

    if title and len(title) <= 200 and due_date is not None:
        tasks = load_tasks()
        tasks.append({
            "task": title,
            "completed": False,
            "priority": priority,
            "due_date": due_date
        })
        save_tasks(tasks)

    return redirect(url_for("dashboard"))


@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    tasks = load_tasks()

    if not 0 <= task_id < len(tasks):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("task", "").strip()
        due_date = valid_due_date(request.form.get("due_date", ""))
        priority = normalize_priority(
            request.form.get("priority", "Medium")
        )

        if title and len(title) <= 200 and due_date is not None:
            tasks[task_id]["task"] = title
            tasks[task_id]["priority"] = priority
            tasks[task_id]["due_date"] = due_date
            save_tasks(tasks)
            return redirect(url_for("dashboard"))

    task = tasks[task_id]

    return render_template(
        "edit.html",
        task=task,
        task_id=task_id,
        priorities=["High", "Medium", "Low"]
    )


@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
    tasks = load_tasks()

    if 0 <= task_id < len(tasks):
        tasks[task_id]["completed"] = not tasks[task_id].get(
            "completed", False
        )
        save_tasks(tasks)

    return redirect(url_for("dashboard"))


@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    tasks = load_tasks()

    if 0 <= task_id < len(tasks):
        tasks.pop(task_id)
        save_tasks(tasks)

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
