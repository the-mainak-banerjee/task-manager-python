from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Literal
from contextlib import asynccontextmanager
import json
import asyncio

FILE_NAME = "tasks.json"


class DueDateMixin(BaseModel):
    due_date: date | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, value):
        if value is not None and value < date.today():
            raise ValueError("due_date cannot be in the past")
        return value


class TaskCreate(DueDateMixin):
    title: str
    # This syntax with a value tells pydantic that these fields are non requiered fields
    priority: Literal["Low", "Medium", "High"] = "Medium"


class TaskUpdate(DueDateMixin):
    title: str | None = None
    priority: Literal["Low", "Medium", "High"] | None = None
    completed: bool | None = None


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


async def check_overdue_tasks():
    while True:
        tasks = load_tasks()
        for task in tasks:
            if task.is_overdue():
                print(f"Task {task.id} is overdue: {task.title}")
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: fire off the background task
    asyncio.create_task(check_overdue_tasks())
    yield
    # Shutdown: nothing to clean up for now


app = FastAPI(lifespan=lifespan)

@app.get("/tasks")
def get_tasks():
    try:
        tasks = load_tasks()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load tasks")
    return [task.to_dict() for task in tasks]


# This is the part where FastAPI's magic kicks in: just by typing the parameter as TaskCreate, FastAPI automatically reads the incoming JSON request body, validates it against the Pydantic model, and hands back a proper TaskCreate instance (not a raw dict) — or automatically returns a 422 Unprocessable Entity error to the client if validation fails, without manually writing any validation code
@app.post("/tasks")
def create_task(task: TaskCreate):
    created_task = add_task(title=task.title, priority=task.priority, due_date=task.due_date)
    return created_task.to_dict()


@app.delete("/tasks/{task_id}")
def delete_task_handler(task_id:int):
    deleted = delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return {"message": f"Task with id {task_id} deleted successfully"}


@app.patch("/tasks/{task_id}")
def update_task_handler(task_id:int, updates:TaskUpdate):
    updated_task = update_task(task_id, updates)

    if not updated_task:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return updated_task.to_dict()


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
        return False

    updated_task = list(filter(lambda task: task.id != task_id, tasks))
    save_tasks(updated_task)
    return True


def update_task(task_id, updates):
    tasks = load_tasks()
    task = next((task for task in tasks if task.id == task_id), None)

    if task is None:
        return False

    update_data = updates.model_dump(exclude_unset = True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # setattr() is a built-in Python function that lets you set an object's attribute dynamically. Other related functions are -
    # getattr(obj, "name")  get an attribute
    # setattr(obj, "name", value)   # set an attribute
    # hasattr(obj, "name")          # check if attribute exists
    # delattr(obj, "name")          # delete an attribute

    save_tasks(tasks)
    return task
