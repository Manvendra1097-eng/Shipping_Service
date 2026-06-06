# Chapter 6: SQLModel — Tables as Python Classes

In Chapter 5, we used Python's built-in `sqlite3` to persist data. It worked, but it had real limitations: we wrote raw SQL strings, had no type safety on columns, and had to manually map dictionaries to queries.

In this chapter, we upgrade to **SQLModel** — a library by the same author as FastAPI (Sebastián Ramírez) that combines **SQLAlchemy** (the most popular Python ORM) with **Pydantic** (which we already know). The result: you define your database tables as Python classes, and get automatic validation, IDE autocomplete, and zero raw SQL.

!!! note "Code Evolution — New Structure"
    We've reorganised the project further. The `database.py` single file is now a **package**:

    ```
    app/
    ├── schema.py              # Pydantic models (request/response shapes)
    ├── database/              # NEW: database package
    │   ├── __init__.py
    │   ├── models.py          # SQLModel table definitions
    │   └── session.py         # Engine, session factory, lifespan, SessionDep
    └── app.py                 # FastAPI endpoints
    ```

    Notice the split: **schemas** describe API data shapes, **models** describe database tables. They share the `ShipmentStatus` enum.

---

## Lesson 6.1: The Database Model (`database/models.py`)

```python
from datetime import datetime
from sqlmodel import SQLModel, Field
from app.schema import ShipmentStatus

class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"
    id: int = Field(default=None, primary_key=True)
    content: str
    weight: float = Field(le=25)
    destination: int
    status: ShipmentStatus
    estimated_delivery: datetime
```

### Breaking It Down

| Code | What it means |
|------|--------------|
| `SQLModel, table=True` | This class represents a real database table |
| `__tablename__ = "shipment"` | Sets the table name in SQLite |
| `id: int = Field(default=None, primary_key=True)` | Auto-generated primary key. `default=None` tells SQLModel the DB will assign it |
| `weight: float = Field(le=25)` | Column with a validation constraint — weight ≤ 25 |
| `status: ShipmentStatus` | SQLModel stores this Enum as its string value |
| `estimated_delivery: datetime` | SQLModel handles Python `datetime` ↔ SQLite TEXT conversion automatically |

!!! tip "SQLModel = Pydantic + SQLAlchemy"
    Because `SQLModel` inherits from `BaseModel`, every instance of `Shipment` is also a Pydantic model. You get validation, `.model_dump()`, and IDE autocomplete for free. When `table=True`, SQLModel *also* registers it as a SQLAlchemy ORM table — no duplication!

!!! note "Schema vs Model"
    - **`schema.py` → Pydantic `BaseModel`**: Defines the *API contract* — what the client sends/receives.
    - **`database/models.py` → SQLModel `table=True`**: Defines the *database table* — what is stored.

    They deliberately have slightly different fields. For example, `ShipmentCreate` doesn't have `status` or `estimated_delivery` (the API auto-sets them). But the `Shipment` DB model has both.

---

## Lesson 6.2: Engine & Session (`database/session.py`)

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

engine = create_engine(
    url="sqlite:///sqlite.db",
    echo=True,
    connect_args={"check_same_thread": False}
)
```

| Parameter | What it does |
|-----------|-------------|
| `"sqlite:///sqlite.db"` | Connection URL — three slashes = relative path from project root |
| `echo=True` | Prints every SQL statement to the console — great for learning, turn off in production |
| `check_same_thread=False` | Allows sharing the engine across multiple FastAPI request threads |

### Initialising the Database

```python
def init_db():
    from app.database.models import Shipment  # noqa: F401

    SQLModel.metadata.create_all(bind=engine)
```

`SQLModel.metadata.create_all()` looks at all classes registered with `table=True` and creates their tables if they don't exist. The local import of `Shipment` is required so SQLModel's metadata knows the table exists before creating it.

!!! warning "Why the local import?"
    If you import `Shipment` at the top of `session.py`, Python may hit a circular import (session → models → session). Importing inside the function body breaks the cycle safely.

### The Session Factory

```python
def get_session():
    with Session(bind=engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

A **Session** is the unit-of-work in SQLAlchemy/SQLModel. All queries, inserts, and commits happen through a session. Using `yield` makes it a **generator** — FastAPI will:

1. Call `get_session()`, which opens a session
2. `yield` it into your endpoint function
3. After the endpoint returns, resume after `yield` — closing the session automatically

`SessionDep` is a convenience type alias using `Annotated`. Instead of writing `session: Session = Depends(get_session)` in every endpoint, you write `session: SessionDep`.

---

## Lesson 6.3: The Lifespan — Startup & Shutdown

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def life_span(app: FastAPI):
    print("Server started .......")
    init_db()
    yield
    print("Server stopping ...")

app = FastAPI(lifespan=life_span)
```

The **lifespan** context manager replaces the older `@app.on_event("startup")` pattern. Everything **before** `yield` runs when the server starts. Everything **after** `yield` runs when it shuts down.

This is where we call `init_db()` to ensure the database table exists before any request comes in.

---

## Lesson 6.4: Endpoints With Dependency Injection

Now look at how clean the endpoints are:

### POST — Create a Shipment

```python
@app.post("/shipment", response_model=None)
def submit_shipment(req_body: ShipmentCreate, session: SessionDep):
    shipment = Shipment(
        **req_body.model_dump(),
        estimated_delivery=datetime.now() + timedelta(days=3),
        status=ShipmentStatus.PLACED,
    )
    session.add(shipment)
    session.commit()
    session.refresh(shipment)
    return {"id": shipment.id}
```

Step by step:
1. `**req_body.model_dump()` — Spreads the Pydantic model fields into the `Shipment` constructor
2. We inject server-side fields (`estimated_delivery`, `status`) that the client never sends
3. `session.add(shipment)` — Stages the new row
4. `session.commit()` — Writes to the database
5. `session.refresh(shipment)` — Reloads the object from DB to populate the auto-generated `id`

### GET — Fetch a Shipment

```python
@app.get("/shipment/{id}", response_model=ShipmentRead)
def get_shipment(id: int, session: Session = Depends(get_session)):
    shipment = session.get(Shipment, id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Given ID doesn't exits")
    return shipment
```

`session.get(Shipment, id)` is the SQLModel way to do `SELECT * FROM shipment WHERE id = ?`. It returns a `Shipment` object or `None` — no raw SQL needed.

### PATCH — Update a Shipment

```python
@app.patch("/shipment/{id}", response_model=ShipmentRead)
def update_shipment(id: int, req_body: ShipmentUpdate, session: SessionDep):
    update_data = req_body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    shipment = session.get(Shipment, id)
    shipment.sqlmodel_update(update_data)

    session.add(shipment)
    session.commit()
    session.refresh(shipment)
    return shipment
```

`model_dump(exclude_none=True)` gives us only the fields the client explicitly set. `sqlmodel_update()` merges those fields into the existing `Shipment` object in one call — no manual field-by-field assignment.

### DELETE — Remove a Shipment

```python
@app.delete("/shipment/{id}")
def cancel_shipment(id: int, session: SessionDep) -> dict[str, str]:
    session.delete(session.get(Shipment, id))
    session.commit()
    return {"detail": f"Shipment with id {id} is deleted"}
```

---

## 🏋️ Try It Yourself

```bash
uvicorn app.main:app --reload
```

Watch the terminal on startup — you'll see `init_db()` running and SQLAlchemy printing the `CREATE TABLE` SQL (because `echo=True`).

1. Create a shipment via `POST /shipment`. Notice the response includes an auto-generated `id`.
2. Fetch it with `GET /shipment/{id}`.
3. Update just the status with `PATCH /shipment/{id}` — try sending an empty body and see the 400 error.
4. Delete it, then try to GET it — you'll get a 404.

---

## What You Learned

In this chapter, you:

- ✅ Defined a **SQLModel table** (`table=True`) that doubles as a Pydantic model
- ✅ Created a **SQLAlchemy engine** and understood the connection URL
- ✅ Used `SQLModel.metadata.create_all()` to auto-create tables
- ✅ Built a **session factory** with `yield` for automatic resource cleanup
- ✅ Used `SessionDep` (`Annotated[Session, Depends(...)]`) to inject the session via FastAPI DI
- ✅ Implemented the **lifespan** pattern for startup/shutdown logic
- ✅ Used `session.get()`, `session.add()`, `session.commit()`, `session.refresh()`, `session.delete()`
- ✅ Used `.sqlmodel_update()` for clean partial updates

## Next Steps

We're using a synchronous SQLAlchemy engine. In the next chapter we upgrade to **PostgreSQL with a fully async engine**, split our endpoints into an `APIRouter`, add a **Service layer** to hold business logic, and manage configuration with **`pydantic-settings`**!

**[Chapter 7: PostgreSQL, Async Engine & Application Architecture →](ch07-postgres-async.md)**
