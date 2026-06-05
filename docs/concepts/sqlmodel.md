# SQLModel — Databases as Python Classes

Raw SQL strings work, but they're hard to maintain: no autocomplete, no type checking, and refactoring a column name means a text search across your whole codebase. **SQLModel** solves this by letting you define your database tables as Python classes.

## What is SQLModel?

[SQLModel](https://sqlmodel.tiangolo.com/) is a library built by Sebastián Ramírez (the creator of FastAPI) that combines two powerful libraries:

| Library | Role |
|---------|------|
| **Pydantic** | Data validation and serialization (API layer) |
| **SQLAlchemy** | Database ORM (persistence layer) |

The magic is that a single class can act as both a **Pydantic model** AND a **database table definition**, eliminating the need to duplicate your data structure.

---

## Defining a Table

```python
from sqlmodel import SQLModel, Field

class Shipment(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    content: str
    weight: float = Field(le=25)
    status: str
```

The only addition compared to a regular Pydantic model is `table=True`. This tells SQLModel to register this class as a real database table.

| Pydantic `BaseModel` | SQLModel `table=True` |
|----------------------|-----------------------|
| In-memory validation | In-memory validation + database persistence |
| No `primary_key` concept | Has primary key, foreign keys, indexes |
| Not tracked by SQLAlchemy | Tracked — can query, insert, update, delete |

---

## The Engine

The engine is your connection to the database. You create it once at application startup:

```python
from sqlalchemy import create_engine

engine = create_engine(
    url="sqlite:///sqlite.db",
    echo=True,  # Logs all SQL to console
    connect_args={"check_same_thread": False}
)
```

### Connection URL Format

```
dialect://user:password@host:port/database
```

| URL | Meaning |
|-----|---------|
| `sqlite:///sqlite.db` | SQLite, relative path (3 slashes = relative) |
| `sqlite:////abs/path/db.db` | SQLite, absolute path (4 slashes) |
| `postgresql://user:pass@localhost/mydb` | PostgreSQL |

---

## Creating Tables

```python
def init_db():
    from app.database.models import Shipment  # noqa

    SQLModel.metadata.create_all(bind=engine)
```

`metadata.create_all()` scans all classes registered with `table=True` and issues `CREATE TABLE IF NOT EXISTS` for each one. You call this once at server startup using the **lifespan** pattern.

---

## The Session

A **Session** is the unit of work. Every query or write operation goes through a session:

```python
from sqlmodel import Session

with Session(engine) as session:
    shipment = session.get(Shipment, 1)
    session.add(new_shipment)
    session.commit()
    session.refresh(new_shipment)
```

| Method | Purpose |
|--------|---------|
| `session.get(Model, id)` | Fetch one row by primary key → returns model or `None` |
| `session.add(obj)` | Stage an object for INSERT or UPDATE |
| `session.commit()` | Flush all staged changes to the database |
| `session.refresh(obj)` | Re-read the object from DB (needed to get auto-generated ID after insert) |
| `session.delete(obj)` | Stage an object for DELETE |

---

## FastAPI Session Dependency

In FastAPI, you inject the session into your endpoints using a **dependency**:

```python
from typing import Annotated
from fastapi import Depends

def get_session():
    with Session(engine) as session:
        yield session  # FastAPI handles cleanup after the request

SessionDep = Annotated[Session, Depends(get_session)]
```

Then in your endpoint:

```python
@app.post("/shipment")
def create_shipment(data: ShipmentCreate, session: SessionDep):
    shipment = Shipment(**data.model_dump())
    session.add(shipment)
    session.commit()
    session.refresh(shipment)
    return shipment
```

`SessionDep` is a shorthand type alias for `Annotated[Session, Depends(get_session)]`. Writing it once and reusing it keeps your endpoint signatures clean.

---

## Partial Updates with `sqlmodel_update`

When handling `PATCH` requests, you only want to update the fields the client explicitly sent. The pattern is:

```python
update_data = req_body.model_dump(exclude_none=True)  # Drop None fields
shipment.sqlmodel_update(update_data)                   # Merge into existing object
session.add(shipment)
session.commit()
session.refresh(shipment)
```

`sqlmodel_update()` is SQLModel's helper method that applies a dictionary of changes onto an existing model instance — no manual field-by-field assignment required.

---

## Schema vs Model: The Key Distinction

| | Pydantic Schema (`schema.py`) | SQLModel Table (`database/models.py`) |
|-|-------------------------------|--------------------------------------|
| **Purpose** | Defines API request/response shapes | Defines database table structure |
| **Inheritance** | `BaseModel` | `SQLModel, table=True` |
| **Fields** | Only what the client sees | All persisted columns |
| **Example** | `ShipmentCreate` has no `status` | `Shipment` DB model has `status` |

This separation is intentional. The Pydantic schemas control what clients can send/receive. The SQLModel table controls what is stored. They share enums (like `ShipmentStatus`) but are otherwise independent.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| `table=True` | Turns a Pydantic model into a DB table |
| `create_engine()` | One engine per application, shared globally |
| `SQLModel.metadata.create_all()` | Creates all registered tables at startup |
| `Session` | Unit of work for all DB operations |
| `SessionDep` | FastAPI DI shorthand for injecting sessions |
| `session.refresh()` | Required after commit to get DB-generated values (e.g., `id`) |
| `sqlmodel_update()` | Clean way to apply partial updates from a dict |

---

**[← Back to Home](../index.md)**
