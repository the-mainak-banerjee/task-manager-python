# Python Backend Development — Revision Notes

Reference notes covering Classes/OOP, File Handling, JSON, Pydantic, FastAPI, Context Managers, and Asyncio. Written for revision — each topic explained standalone with syntax, reasoning, and gotchas.

---

## 1. Classes & OOP

### What a class is
A class is a blueprint for creating objects that bundle **data** (attributes) and **behavior** (methods) together.

```python
class Task:
    def __init__(self, id, title, priority="Medium", due_date=None, completed=False):
        self.id = id
        self.title = title
        self.priority = priority
        self.due_date = due_date
        self.completed = completed
```

- `__init__` is the **constructor** — it runs automatically when you create an object (`Task(1, "Read")`), and sets up the initial state.
- `self` refers to the specific instance being created/used. Every method needs `self` as its first parameter so it knows which object's data to work with.
- Parameters with `=` (like `priority="Medium"`) are **default values** — optional at call time.

### Instance methods
Methods are functions defined inside a class that operate on `self`.

```python
def mark_completed(self):
    self.completed = True

def is_overdue(self):
    if self.completed or self.due_date is None:
        return False
    return self.due_date < date.today()
```

These read/modify the specific instance's attributes. Two different `Task` objects each have their own independent `completed`/`due_date`, so calling `task1.mark_completed()` never affects `task2`.

### `__repr__` — controlling how an object prints
By default, `print(some_object)` shows something unreadable like `<Task object at 0x7f...>`. Defining `__repr__` overrides that:

```python
def __repr__(self):
    status = "✅" if self.completed else "❌"
    return f"[{status}] {self.title} (priority={self.priority}, due={self.due_date})"
```

`__str__` is a related method — `print()` and `str()` prefer `__str__` if it exists, and fall back to `__repr__` otherwise. In practice, defining just `__repr__` is common enough for most small classes.

### `@classmethod` — alternate constructors
Normally you build an object by calling `Task(...)` directly. Sometimes you want a *different* way to build one — e.g., from a dictionary loaded from JSON.

```python
@classmethod
def from_dict(cls, data):
    due_date = None if data["due_date"] is None else date.fromisoformat(data["due_date"])
    return cls(
        id=data["id"],
        title=data["title"],
        priority=data["priority"],
        due_date=due_date,
        completed=data["completed"],
    )
```

- `cls` refers to the class itself (`Task`), not an instance — because at the point this runs, no instance exists yet; the method's whole job is to *create* one.
- Using `cls(...)` instead of `Task(...)` directly means this still works correctly if `Task` is ever subclassed.
- Call it as `Task.from_dict(some_dict)` — note it's called on the class, not an instance.

### `@staticmethod` vs `@classmethod`
- `@classmethod` receives `cls` (the class) — use for alternate constructors or logic tied to the class itself.
- `@staticmethod` receives neither `self` nor `cls` — it's just a regular function that happens to live inside the class namespace, because it's logically related but doesn't need any class/instance data.

```python
class MathHelper:
    @staticmethod
    def add(a, b):
        return a + b
```

### `setattr` / `getattr` — dynamic attribute access
Normally you access an attribute with a literal name: `task.title`. Sometimes the attribute name is only known at runtime (e.g., it came from a loop or user input) — that's what `setattr`/`getattr` are for.

```python
setattr(task, "title", "New title")   # same as: task.title = "New title"
getattr(task, "title", "default")     # same as: task.title, but returns "default" if missing
```

This is how you can loop over a dict of `{field_name: new_value}` pairs and apply all of them without writing a separate `if` for each field:

```python
for field, value in update_data.items():
    setattr(task, field, value)
```

### Separation of concerns (a design principle, not syntax)
Keep different responsibilities in different places:
- A domain class (`Task`) should only know about *itself* — its own data and behavior.
- Validation (Pydantic models) is a separate concern — the class shouldn't validate incoming API data itself.
- Persistence (reading/writing files or a database) is a separate concern — the class shouldn't know how it's stored.

This makes each piece independently testable and replaceable — e.g., you can swap JSON-file storage for a real database without touching the `Task` class at all.

### Other useful things to know (not required day-to-day, good to recognize)
- `@dataclass` (from the `dataclasses` module) auto-generates `__init__`, `__repr__`, and `__eq__` for simple data-holding classes — less boilerplate than writing them by hand.
- `__eq__` lets you define what makes two instances "equal" (by default, Python compares by identity/memory address, not by value).
- Inheritance (`class Child(Parent):`) lets a class reuse another class's fields/methods — used heavily in Pydantic (see below).

---

## 2. File Handling

### Opening files with `with`
```python
with open("tasks.json") as file:
    contents = file.read()
```

- `open(path, mode)` — default mode is read (`"r"`). Common modes: `"r"` (read), `"w"` (write, **overwrites** the whole file), `"a"` (append to the end).
- The `with` block guarantees the file is properly closed when the block ends — even if an exception occurs inside it. Without `with`, you'd need a manual `file.close()`, and forgetting it (or an exception preventing it) can leak file handles.

### Handling missing files
```python
try:
    with open("tasks.json") as file:
        ...
except FileNotFoundError:
    # handle the "file doesn't exist yet" case, e.g. return an empty default
```

Catching the **specific** exception (`FileNotFoundError`) rather than a bare `except:` is important — a bare `except` would silently swallow *any* error (including real bugs), making debugging much harder.

### `pathlib` (a more modern alternative)
```python
from pathlib import Path
p = Path("tasks.json")
p.exists()          # True/False
p.read_text()       # read whole file as a string
```
Worth learning as a cleaner alternative to plain string paths, especially once you're joining paths across folders.

---

## 3. JSON

### Why JSON needs conversion
JSON only understands a limited set of types: strings, numbers, booleans, `null`, arrays (`[]`), and objects (`{}`). Python objects like `date` or a custom class (`Task`) aren't natively JSON-serializable — trying to `json.dump()` them directly raises a `TypeError`.

### Reading and writing
```python
import json

# Write: Python object -> JSON file
with open("tasks.json", "w") as file:
    json.dump(python_list_of_dicts, file, indent=4)

# Read: JSON file -> Python object
with open("tasks.json") as file:
    data = json.load(file)   # returns a list/dict of plain Python types
```

- `json.dump(obj, file)` / `json.load(file)` — work directly with an open **file object**.
- `json.dumps(obj)` / `json.loads(string)` — the "s" versions work with **strings** instead (useful when you need the JSON text itself, e.g. to send over a network manually).
- `indent=4` makes the output human-readable (pretty-printed) — omit it for smaller file size in production.

### Bridging custom objects and JSON
Since `Task` isn't natively serializable, you convert manually:

```python
def to_dict(self):
    return {
        "id": self.id,
        "title": self.title,
        "priority": self.priority,
        "completed": self.completed,
        "due_date": None if self.due_date is None else self.due_date.isoformat(),
    }
```

- `.isoformat()` converts a `date` object to a standard string like `"2026-09-20"`.
- `date.fromisoformat("2026-09-20")` converts it back.
- Using `None` (which becomes JSON `null`) for "no value," instead of an empty string, keeps the check unambiguous later: `if data["due_date"] is None:` vs. having to also handle `""` as a separate special case.

### Common error to know
`json.JSONDecodeError` — raised when `json.load`/`json.loads` is given malformed/corrupted JSON text. Worth catching separately from `FileNotFoundError` in production code.

---

## 4. Pydantic

### What Pydantic is for
Pydantic defines **schemas** — the shape and rules for data coming into (or going out of) your application — and validates data against them automatically.

```python
from pydantic import BaseModel
from datetime import date

class TaskCreate(BaseModel):
    title: str
    priority: str = "Medium"
    due_date: date | None = None
```

- Every field needs a **type hint** (`str`, `date | None`, etc.) — this is what Pydantic validates incoming data against.
- A field **without** a default (`title: str`) is required — the client must send it, or Pydantic auto-generates a `422` error.
- A field **with** a default (`priority: str = "Medium"`) is optional — omitted by the client, it just falls back to the default.

### A key gotcha: type hint vs. default value
```python
due_date: date | None        # WRONG if you want this optional to omit
due_date: date | None = None # CORRECT — actually optional
```
`date | None` only says "the value, if provided, must be a date or None." It does **not** make the field optional to leave out entirely — that requires an explicit `= None`.

### Restricting to a fixed set of values — `Literal`
```python
from typing import Literal

priority: Literal["Low", "Medium", "High"] = "Medium"
```
Anything outside these exact strings is automatically rejected with a `422` — no custom code needed. Case-sensitive, so `"low"` ≠ `"Low"`.

### Custom validation — `@field_validator`
For rules `Literal` can't express (like "date can't be in the past"):

```python
from pydantic import field_validator
from datetime import date

class TaskCreate(BaseModel):
    due_date: date | None = None

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, value):
        if value is not None and value < date.today():
            raise ValueError("due_date cannot be in the past")
        return value
```
- Decorated with the field name it validates (`"due_date"`).
- Also needs `@classmethod` underneath — the validator receives `cls`, not `self`, since it runs during construction, before a full instance exists.
- Raising `ValueError` inside it is what Pydantic turns into an automatic `422` response with your message.

### Sharing fields/validators across models — inheritance
If two models need the exact same field + validation logic, don't copy-paste — inherit from a shared base:

```python
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
    priority: Literal["Low", "Medium", "High"] = "Medium"

class TaskUpdate(DueDateMixin):
    title: str | None = None
    priority: Literal["Low", "Medium", "High"] | None = None
    completed: bool | None = None
```
A fix to the shared logic only needs to happen once, in `DueDateMixin`.

### Partial updates — `model_dump(exclude_unset=True)`
For PATCH-style updates, you only want the fields the client *actually sent*, not ones that just fell back to their defaults:

```python
update_data = updates.model_dump(exclude_unset=True)
for field, value in update_data.items():
    setattr(task, field, value)
```
- `exclude_unset=True` — include only fields present in the original input.
- Related but different: `exclude_none=True` (drop fields currently `None`, regardless of whether sent) and `exclude_defaults=True` (drop fields still equal to their default value). These solve different problems — `exclude_unset` is almost always the right one for PATCH semantics.

### Pydantic v1 vs v2 — naming differs
| Concept | v2 | v1 |
|---|---|---|
| Dump to dict | `.model_dump()` | `.dict()` |
| Field validator | `@field_validator` | `@validator` |

Check `pip show pydantic` if code doesn't behave as expected — the two aren't interchangeable.

### Other things worth knowing
- `response_model=` on a FastAPI route can validate/shape the *outgoing* response the same way a request model shapes incoming data — removes the need to manually call `.to_dict()` in every route.
- `model_config` (or the old `class Config:`) lets you customize model-wide behavior, e.g. rejecting any field not explicitly declared in the schema.
- Fields can be other `BaseModel`s (nested models) once your data has structure beyond flat key-value pairs.

---

## 5. FastAPI

### The core object and routes
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/tasks")
def get_tasks():
    ...
```
- `app = FastAPI()` — the application instance everything attaches to.
- `@app.get(...)`, `@app.post(...)`, `@app.patch(...)`, `@app.delete(...)` — decorators mapping a URL + HTTP method to a Python function.
- HTTP methods carry semantic meaning: **GET** = read (no side effects), **POST** = create, **PATCH** = partial update, **PUT** = full replace (not used here), **DELETE** = remove.

### Path parameters
```python
@app.delete("/tasks/{task_id}")
def delete_task_handler(task_id: int):
    ...
```
- `{task_id}` in the route string marks part of the URL as a variable.
- Declaring `task_id: int` in the function signature tells FastAPI to extract it from the URL and convert it to an `int` automatically — sending a non-numeric value here gives an automatic `422`.

### Request bodies via Pydantic
```python
@app.post("/tasks")
def create_task(task: TaskCreate):
    ...
```
Typing a parameter as a Pydantic model tells FastAPI: parse the incoming JSON body, validate it against `TaskCreate`, and hand you back a real `TaskCreate` instance (or auto-return `422` if it fails validation). No manual parsing/validation code needed.

### Error handling — `HTTPException`
```python
from fastapi import HTTPException

if not found:
    raise HTTPException(status_code=404, detail="Task not found")
```
Without this, an unhandled Python exception produces a generic, opaque `500` error. `HTTPException` lets you return a specific, meaningful status code and message on purpose.

### Status codes worth knowing
| Code | Meaning | When |
|---|---|---|
| 200 | OK | Successful GET/PATCH/DELETE |
| 201 | Created | Successful POST that creates something (more precise than 200) |
| 204 | No Content | Success with nothing to return (e.g., DELETE) |
| 400 | Bad Request | Generic client error |
| 404 | Not Found | Requested resource doesn't exist |
| 422 | Unprocessable Entity | Body/params failed validation (Pydantic's default) |
| 500 | Internal Server Error | Unhandled server-side failure |

### Auto-generated docs
Visiting `/docs` on a running FastAPI app shows an interactive UI (built on the OpenAPI standard) listing every route, its expected inputs, and a "Try it out" button — generated automatically from your type hints and Pydantic models, no extra work required.

### The implicit serialization fallback (know it, avoid relying on it)
FastAPI can serialize a plain object it doesn't recognize by reading its attributes directly (via `jsonable_encoder`), even without a `to_dict()` method. This can make broken code "work by accident." Prefer explicit conversion (`task.to_dict()`) so you control the exact response shape.

### Things to learn next
- **Query parameters** — extra filters not in the path or body, e.g. `GET /tasks?completed=true`. Declared as normal function parameters without `{}` in the route.
- **`Depends`** — FastAPI's dependency injection system, for sharing setup logic (like a DB session) across multiple routes.
- **CORS** (`CORSMiddleware`) — required if a browser-based frontend on a different origin needs to call this API.

---

## 6. Context Managers

### The pattern
A context manager guarantees setup and cleanup happen together — cleanup runs even if an error occurs in between.

```python
with open("file.txt") as f:
    # setup: file opened
    ...
    # cleanup: file automatically closed here, even on exception
```

### What makes something a context manager
Any object implementing two special methods:
- `__enter__` — runs when entering the `with` block (setup).
- `__exit__` — runs when leaving the block, whether normally or via an exception (cleanup).

`open()` returns such an object, which is why `with open(...)` works.

### Writing your own — `@contextmanager` / `@asynccontextmanager`
Instead of writing a full class with `__enter__`/`__exit__`, `contextlib` lets you write a context manager as a single function using `yield`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # everything before yield = startup logic
    yield
    # everything after yield = shutdown logic

app = FastAPI(lifespan=lifespan)
```
- Code before `yield` runs once, when the app starts.
- Code after `yield` runs once, when the app shuts down.
- `@asynccontextmanager` is the async version (for use with `async def` + `await`); `@contextmanager` is the sync version.

### Why this pattern generalizes
The same "setup → do work → guaranteed cleanup" shape shows up everywhere: database connections, network sockets, locks, and application startup/shutdown. Recognizing the pattern helps you correctly use context managers in libraries you haven't seen before.

---

## 7. Asyncio

### The problem it solves
Normal (synchronous) Python code blocks — one line finishes completely before the next runs. If a function calls `time.sleep(10)`, the **entire program** freezes for 10 seconds, including a web server that should be handling other requests at the same time.

`asyncio` allows a function to pause at a specific point and let other code run during the wait, instead of blocking everything.

### `async def` and `await`
```python
import asyncio

async def check_overdue_tasks():
    while True:
        tasks = load_tasks()
        for task in tasks:
            if task.is_overdue():
                print(f"Task {task.id} is overdue: {task.title}")
        await asyncio.sleep(10)
```
- `async def` marks a function as a **coroutine** — a function that can be paused/resumed. `await` can only be used inside an `async def` function.
- `await asyncio.sleep(10)` pauses **this coroutine** for 10 seconds, but lets everything else (like FastAPI serving requests) continue running during that time — fundamentally different from `time.sleep(10)`, which blocks the whole program.
- Without `await asyncio.sleep(...)` inside a `while True:` loop, the loop would spin instantly and continuously with zero pause, maxing out the CPU and blocking everything else (since there'd be no point where control is handed back).

### Running a coroutine in the background
Defining a coroutine doesn't run it — you need to explicitly schedule it:
```python
asyncio.create_task(check_overdue_tasks())
```
This starts the coroutine running **without waiting** for it to finish, letting it run alongside the rest of the program. Since `check_overdue_tasks()` loops forever, it just keeps running in the background indefinitely.

### Tying it to FastAPI startup
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(check_overdue_tasks())
    yield

app = FastAPI(lifespan=lifespan)
```
This starts the background loop automatically the moment the app launches, with no manual trigger needed.

### The event loop (mental model)
Asyncio runs on a single-threaded **event loop** that juggles many coroutines, switching between them whenever one hits an `await` and is waiting on something. This is the core mental shift from synchronous code: instead of "one thing at a time, start to finish," it's "many things paused and resumed as they become ready."

### Related things worth knowing
- **`async def` route handlers**: FastAPI supports both plain `def` and `async def` routes. If a route needs to `await` something (e.g., an async database call), the route itself must be declared `async def`.
- **`asyncio.gather(coro1(), coro2())`**: runs multiple coroutines concurrently and waits for all of them — useful for independent async operations that don't need to happen one after another.
- **Cancelling tasks**: a background task created with `asyncio.create_task()` can be stopped with `.cancel()` — useful in the shutdown section (after `yield`) of a `lifespan` function, for graceful shutdown instead of leaving it running forever.
- **When *not* to use asyncio**: it helps with I/O-bound waiting (network calls, file access, timers). CPU-heavy work (heavy computation) doesn't benefit from asyncio the same way — that's a job for multiprocessing or threading instead.

---

## Quick Reference — Decorators Used

| Decorator | Purpose |
|---|---|
| `@classmethod` | Method receives the class (`cls`), not an instance — used for alternate constructors |
| `@staticmethod` | Method receives neither `self` nor `cls` — a plain function grouped inside a class |
| `@field_validator("field_name")` | Custom Pydantic validation for one field |
| `@app.get/post/patch/delete(...)` | Register a FastAPI route for a given HTTP method + path |
| `@contextmanager` / `@asynccontextmanager` | Turn a generator function into a context manager |
