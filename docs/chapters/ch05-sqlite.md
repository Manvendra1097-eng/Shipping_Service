# Chapter 5: SQLite Database (Raw SQL)

!!! warning "Superseded by Chapter 6"
    This chapter shows the **raw `sqlite3` approach** we used as a stepping stone. In [Chapter 6](ch06-sqlmodel.md), we replaced all of this with **SQLModel**, which is more Pythonic, type-safe, and production-ready. Read this chapter to understand *why* SQLModel is better, or skip straight to Chapter 6 if you're in a hurry!

So far, our data has lived in a Python dictionary. Every time you restart the server, all data is lost. That is fine for learning, but not for any real application.

In this chapter, we replace the in-memory dictionary with a **SQLite database** — a real, file-backed database that persists data across restarts. We'll do this using Python's built-in `sqlite3` module and a custom `DB` class that wraps all database operations cleanly.

!!! note "Code Evolution"
    We have a new file: `app/database.py`. This file owns the entire relationship with SQLite so that `app/main.py` stays clean. In **Chapter 6**, we'll swap this raw `sqlite3` code for **SQLModel**, which makes this even more Pythonic!

    **Project structure now:**
    ```
    app/
    ├── schema.py       # Pydantic models (from Chapter 4)
    ├── database.py     # NEW: All SQLite database operations
    └── app.py          # FastAPI endpoints
    ```

---

## Lesson 5.1: The Database Class (`database.py`)

All SQLite interactions are encapsulated in the `DB` class. Let's read through it section by section.

### Connecting to SQLite

```python
import sqlite3

class DB:
    def __init__(self):
        self.conn = sqlite3.connect("sqlite.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.create_table("shipment")
```

| Line | What it does |
|------|-------------|
| `sqlite3.connect("sqlite.db")` | Opens (or creates) a file called `sqlite.db` in your project root |
| `check_same_thread=False` | Allows the same connection to be used from multiple FastAPI request threads |
| `conn.row_factory = sqlite3.Row` | Makes query results behave like dictionaries (access by column name, not index) |
| `conn.cursor()` | Creates a cursor — the object used to execute SQL statements |
| `create_table("shipment")` | Immediately ensures the table exists when the app starts |

### Creating the Table

```python
def create_table(self, name: str):
    self.cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {name} (
            id      INTEGER PRIMARY KEY,
            content TEXT,
            weight  REAL,
            status  TEXT
        )
    """)
```

`CREATE TABLE IF NOT EXISTS` is safe to run every time — it only creates the table if it doesn't already exist. Our shipment table has four columns that directly mirror the Pydantic `ShipmentRead` model.

!!! warning "SQL Injection Note"
    Using an f-string here (`f"...{name}..."`) is acceptable because `name` comes from our own trusted code, not from user input. For user-supplied data, **always** use parameterized queries with `?` placeholders. You'll see this in the methods below.

---

## Lesson 5.2: CRUD Operations

### CREATE — Inserting a New Shipment

```python
def create(self, shipment: ShipmentCreate) -> int:
    self.cur.execute("SELECT MAX(id) FROM shipment")
    row = self.cur.fetchone()
    new_id = (row[0] or 0) + 1

    self.cur.execute(
        """
        INSERT INTO shipment
        VALUES (:id, :content, :weight, :status)
        """,
        {"id": new_id, **shipment.model_dump(), "status": "placed"},
    )
    self.conn.commit()
    return self.cur.lastrowid
```

Key details:
- We manually calculate the next `id` using `SELECT MAX(id)`. SQLite's `AUTOINCREMENT` is another option, but this keeps us in full control.
- **`shipment.model_dump()`** converts the Pydantic `ShipmentCreate` object to a dict (`{"content": ..., "weight": ..., "destination": ...}`). We spread it with `**` and override the status.
- Named placeholders (`:id`, `:content`) are used instead of positional `?` for clarity.
- **`self.conn.commit()`** must be called to actually persist the changes. Without it, the insert is only in a pending transaction.

### READ — Fetching a Shipment

```python
def get(self, id: int) -> dict[str, Any] | None:
    self.cur.execute(
        "SELECT * FROM shipment WHERE id = ?",
        (id,),
    )
    result = self.cur.fetchone()

    if result is None:
        return None
    return dict(result)
```

- The positional `?` placeholder safely prevents SQL injection. **Never** build SQL strings with f-strings when using user data.
- `fetchone()` returns a single `sqlite3.Row` (or `None` if not found).
- Because we set `row_factory = sqlite3.Row`, we can convert it to a standard dictionary with `dict(result)`, which FastAPI and Pydantic can easily work with.

### UPDATE — Changing the Status

```python
def update(self, id: int, shipment: ShipmentUpdate) -> dict[str, Any] | None:
    self.cur.execute(
        "UPDATE shipment SET status = ? WHERE id = ?",
        (shipment.status, id),
    )
    self.conn.commit()
    return self.get(id)
```

After updating, we call `self.get(id)` to return the full updated record. This is a common pattern that avoids returning stale data.

### DELETE — Removing a Shipment

```python
def delete(self, id: int):
    self.cur.execute(
        "DELETE FROM shipment WHERE id = ?",
        (id,),
    )
    self.conn.commit()
```

---

## Lesson 5.3: Wiring It Up in `app.py`

The endpoints in `app.py` are now dramatically simpler because all the database logic lives in `database.py`.

```python
from app.database import DB
from app.schema import ShipmentCreate, ShipmentRead, ShipmentUpdate

app = FastAPI()
db = DB()  # Single DB instance shared across all requests
```

!!! tip "Dependency Injection"
    Creating `db = DB()` as a global is simple and works fine for now. In **Chapter 13**, we'll use FastAPI's Dependency Injection system to manage this more robustly, which also makes it easier to replace with a test database during testing.

### GET

```python
@app.get("/shipment/{id}", response_model=ShipmentRead)
def get_shipment(id: int):
    shipment = db.get(id)
    if shipment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="...")
    return shipment
```

### POST

```python
@app.post("/shipment", response_model=None)
def submit_shipment(req_body: ShipmentCreate):
    new_id = db.create(req_body)
    return {"id": new_id}
```

### PATCH

```python
@app.patch("/shipment/{id}", response_model=ShipmentRead)
def update_shipment(id: int, req_body: ShipmentUpdate):
    shipment = db.update(id, req_body)
    return shipment
```

### DELETE

```python
@app.delete("/shipment/{id}")
def cancel_shipment(id: int) -> dict[str, str]:
    db.delete(id)
    return {"detail": f"Shipment with id {id} is deleted"}
```

Notice how each endpoint is now just **one or two lines**. The `DB` class handles all complexity.

---

## 🏋️ Try It Yourself

```bash
uvicorn app.main:app --reload
```

1. **Create** a shipment via `POST /shipment`. Then **restart the server** and `GET` it back — it's still there! That's the power of a real database.
2. Look in your project folder — you'll see a new `sqlite.db` file has been created. This is your database.
3. Try creating multiple shipments and deleting one. Notice the IDs don't reset on restart.

---

## What You Learned

In this chapter, you:

- ✅ Replaced the in-memory dictionary with a **SQLite database** that persists data.
- ✅ Wrote a `DB` class to **encapsulate** all database operations.
- ✅ Used **parameterized queries** (`?`) to prevent SQL injection.
- ✅ Used `conn.row_factory = sqlite3.Row` to get dictionary-like results.
- ✅ Learned the commit/fetch pattern for INSERT, UPDATE, SELECT, DELETE.
- ✅ Saw how clean endpoints become when database logic is in a separate class.

## Next Steps

We're using raw `sqlite3` which means we're writing SQL strings by hand. In the next chapter, we'll upgrade to **SQLModel** — which lets you define your tables as Python classes (combining Pydantic + SQLAlchemy) and never write raw SQL again!

**[Chapter 6: SQLModel →](ch06-sqlmodel.md)**
