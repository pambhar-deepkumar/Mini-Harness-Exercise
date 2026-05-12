# Todo API

A minimal FastAPI backend for an in-memory todo list. Used as a sample project
for the Mini-Harness coding agent to operate on.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open:

- <http://127.0.0.1:8000/> — the HTML UI for managing todos
- <http://127.0.0.1:8000/docs> — the interactive Swagger UI

## Endpoints

| Method | Path              | Description       |
| ------ | ----------------- | ----------------- |
| GET    | `/todos`          | List all todos    |
| POST   | `/todos`          | Create a todo     |
| GET    | `/todos/{id}`     | Get a single todo |
| PATCH  | `/todos/{id}`     | Update a todo     |
| DELETE | `/todos/{id}`     | Delete a todo     |

Storage is in-memory and resets on every restart.
