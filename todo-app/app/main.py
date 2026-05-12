from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.db import get_db_connection

app = FastAPI(title="Todo API")

STATIC_DIR = Path(__file__).resolve().parent / "static"


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


from datetime import date


class TodoIn(BaseModel):
    title: str
    done: bool = False
    due_date: date | None = None


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None
    due_date: date | None = None


class Todo(TodoIn):
    id: int




@app.get("/todos", response_model=list[Todo])
def list_todos() -> list[Todo]:
    conn = get_db_connection()
    todos = conn.execute("SELECT * FROM todos").fetchall()
    conn.close()
    return [Todo(**todo) for todo in todos]




@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(payload: TodoIn) -> Todo:
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO todos (title, done) VALUES (?, ?)",
        (payload.title, payload.done),
    )
    conn.commit()
    todo_id = cursor.lastrowid
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return Todo(**todo)




@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int) -> Todo:
    conn = get_db_connection()
    todo = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return Todo(**todo)




@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, payload: TodoUpdate) -> Todo:
    conn = get_db_connection()
    existing_todo = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if existing_todo is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        conn.close()
        return Todo(**existing_todo)  # No fields to update

    set_clauses = []
    values = []
    for key, value in update_data.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)
    
    values.append(todo_id)
    
    conn.execute(
        f"UPDATE todos SET {', '.join(set_clauses)} WHERE id = ?",
        tuple(values),
    )
    conn.commit()
    updated_todo = conn.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    conn.close()
    return Todo(**updated_todo)




@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> None:
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Todo not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

