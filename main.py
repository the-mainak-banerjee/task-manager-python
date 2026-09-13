from datetime import date
import json

FILE_NAME = "tasks.json"


class Task:
    def __init__(self, id, title, priority="Medium", due_date=None, completed=False):
        self.id = id
        self.title = title
        self.priority = priority
        self.due_date = due_date
        self.completed = completed

    def mark_completed(self):
        self.completed = True

    def is_overdue(self):
        if self.completed or self.due_date is None:
            return False
        else:
            return self.due_date < date.today()

    def to_dict(self):
        task_dict = {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "completed": self.completed,
            "due_date": None if self.due_date is None else self.due_date.isoformat(),
        }
        return task_dict

    @classmethod
    def from_dict(cls, data):
        due_date = (
            None if data["due_date"] is None else date.fromisoformat(data["due_date"])
        )
        return cls(
            id=data["id"],
            title=data["title"],
            priority=data["priority"],
            due_date=due_date,
            completed=data["completed"],
        )

    def __repr__(self):
        status = "✅" if self.completed else "❌"
        return (
            f"[{status}] {self.title} (priority={self.priority}, due={self.due_date})"
        )


task1 = Task(
    1, "Read Python", priority="High", due_date=date(2026, 9, 20), completed=False
)
task2 = Task(2, "Read AI", priority="High", due_date=None, completed=False)
task3 = Task(3, "Read AI", priority="High", due_date=date(2026, 9, 10), completed=False)

task_list = [task1, task2, task3]


def load_tasks():
    try:
        # Read the tasks from JSON file
        with open(FILE_NAME) as file:
            tasks = json.load(file)

        # This will convert the JSON file data to original task object and return the list
        return [Task.from_dict(task) for task in tasks]
    except FileNotFoundError:
        return []


def save_tasks(task_list):
    # Using list comprehension to covert the tasks to dict
    dict_task_list = [task.to_dict() for task in task_list]

    # Store the tasks in a JSON file
    # Using "w" as we want to rewrite the whole list to the file
    # Using json.dump() and passing the full list as we want to store the full list as a JSON object
    # No need to do file.write if we are doing json.dump
    with open(FILE_NAME, "w") as file:
        json.dump(dict_task_list, file, indent=4)
    return "Tasks saved successfully"


def add_task(title, priority, due_date):
    tasks = load_tasks()
    new_id = max((task.id for task in tasks), default=0) + 1
    print(new_id)
    new_task = Task(
        id=new_id,
        title=title,
        priority=priority,
        due_date=due_date,
        completed=False,
    )
    tasks.append(new_task)
    save_tasks(tasks)
    return new_task


def delete_task(task_id):
    tasks = load_tasks()

    # checks whether at least one task in tasks has an ID equal to task_id.
    task_exists = any(task.id == task_id for task in tasks)
    if not task_exists:
        return f"Task with id {task_id} not found"

    updated_task = list(filter(lambda task: task.id != task_id, tasks))
    save_tasks(updated_task)
    return f"Task with id {task_id} deleted successfully"


# print(add_task("Fun", "High", date(2026,9,15)))
print(delete_task(1))
