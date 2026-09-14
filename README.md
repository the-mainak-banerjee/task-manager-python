# Task Manager API

A backend where you can create tasks, mark them done, set priorities/due dates, and it auto-flags overdue ones in the background — built as a hands-on learning project to practice file handling, JSON, classes/OOP, Pydantic, FastAPI, and asyncio.

## Features

- Create, read, update, and delete tasks
- Each task has a title, priority (`Low` / `Medium` / `High`), an optional due date, and a completion status
- Request validation via Pydantic, including a custom rule rejecting due dates in the past
- Tasks persisted to a local `tasks.json` file
- A background async task that periodically scans for and flags overdue tasks, independent of any incoming request

## Tech Stack

- Python 3
- FastAPI
- Pydantic
- Uvicorn (ASGI server)
- `asyncio` (standard library)

## Project Structure

```
task_manager/
├── main.py        # Task class, persistence functions, FastAPI app and routes
└── tasks.json      # created automatically on first write
```

## Setup

```bash
pip install fastapi uvicorn
```

## Running the App

```bash
uvicorn main:app --reload
```

- API base URL: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/tasks` | List all tasks |
| POST | `/tasks` | Create a new task |
| PATCH | `/tasks/{task_id}` | Partially update a task (any subset of fields) |
| DELETE | `/tasks/{task_id}` | Delete a task |

### Task fields

| Field | Type | Notes |
|---|---|---|
| `id` | int | Assigned by the server |
| `title` | str | Required on create |
| `priority` | `"Low"` \| `"Medium"` \| `"High"` | Defaults to `"Medium"` |
| `due_date` | date or `null` | Optional; cannot be in the past |
| `completed` | bool | Defaults to `false` on create |

## How It Was Built

This project was built incrementally, in four phases, deliberately delaying FastAPI until the underlying logic was solid.

### Phase 1 — Plain Python (no files, no JSON, no FastAPI)

Goal: get the core `Task` behavior right in isolation before involving persistence or a web framework.

- **Step 1:** Modeled `Task` as a plain class with an `__init__` taking `title`, `priority`, `due_date`, and `completed` (default `False`).
- **Step 2:** Added behavior methods — `mark_completed()` and `is_overdue()` (comparing `due_date` against `date.today()`, first exposure to the `datetime` module).
- **Step 3:** Added `__repr__` so printing a `Task` shows readable output instead of a default object reference.
- **Step 4:** Held multiple `Task` objects in a plain Python list, looped through them, and printed which were overdue — no persistence yet, just proving the class logic worked.

### Phase 2 — File Handling + JSON (still no FastAPI)

Goal: get comfortable with serialization and file I/O before adding a web layer on top.

- **Step 5:** Added `to_dict()` to convert a `Task` into a plain dictionary, since JSON can't serialize custom objects directly.
- **Step 6:** Wrote the full task list to `tasks.json` using `json.dump()`.
- **Step 7:** Read `tasks.json` back and reconstructed `Task` objects using a `from_dict()` classmethod, confirming the save/load round-trip preserved all data correctly (including converting date strings back to real `date` objects).
- **Step 8:** Wrapped the read/write logic into reusable functions — `load_tasks()`, `save_tasks()`, `add_task()`, `delete_task()` — each reading the JSON file, performing an operation, and writing it back. This became the persistence layer FastAPI would later call into directly, and included handling for tasks not found (returning a clear success/failure signal rather than an ambiguous string).

### Phase 3 — Introduce FastAPI (wrap what was already built)

Goal: expose the existing logic over HTTP without duplicating it.

- **Step 9:** Stood up a bare FastAPI app with a single `GET /` endpoint returning `{"status": "ok"}`, confirmed via browser and `/docs`.
- **Step 10:** Wired `GET /tasks` to the existing `load_tasks()` function.
- **Step 11:** Defined a `TaskCreate` Pydantic model (`title`, `priority`, `due_date`) — deliberately separate from the internal `Task` class, since a class representing internal domain logic and a schema representing what a client is allowed to send are different responsibilities.
- **Step 12:** Wired `POST /tasks`, accepting a validated `TaskCreate` body and passing its fields into `add_task()`.
- **Step 13:** Added `PATCH /tasks/{id}` and `DELETE /tasks/{id}`, including a `TaskUpdate` model (all fields optional) and `update_task()`, which applies only the fields actually present in the request using `model_dump(exclude_unset=True)` — so a client can update a single field without resending the whole task.
- **Step 14:** Added real validation: a `Literal["Low", "Medium", "High"]` constraint on `priority`, and a custom `@field_validator` rejecting any `due_date` in the past — shared across `TaskCreate` and `TaskUpdate` via a common `DueDateMixin` base class to avoid duplicating the same rule twice.

### Phase 4 — Asyncio

Goal: add a background process that runs independently of the request/response cycle.

- **Step 15:** Wrote an `async def check_overdue_tasks()` coroutine that loads all tasks, checks each with `is_overdue()`, and pauses with `await asyncio.sleep(10)` between checks — using `await` instead of a blocking `time.sleep()` so it doesn't freeze the rest of the app. Wired it up via FastAPI's `lifespan` context manager and `asyncio.create_task(...)`, so it starts automatically the moment the app launches and keeps running in the background for the app's entire lifetime.

## Known Limitations / Possible Next Steps

- `tasks.json` is a flat file — fine for a single-user learning project, but not safe under concurrent writes. A real database (starting with SQLite) would be the natural next step.
- The background overdue-check currently only prints to the console; it could instead update each task's status in the file.
- No automated tests yet — `pytest` with FastAPI's `TestClient` would be a good addition before further refactors.