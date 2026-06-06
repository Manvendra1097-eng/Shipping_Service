# Chapter 7: PostgreSQL, Async Engine & Application Architecture

This chapter covers two major upgrades that happened in parallel:

1. **Database upgrade**: SQLite → PostgreSQL with a fully async engine
2. **Architecture upgrade**: monolithic `app.py` → layered, modular structure (Router → Service → Database)

These changes transform our project from a prototype into a **production-ready application structure**.

!!! note "What Changed"
    ```
    Before (Chapter 6)          After (Chapter 7)
    ────────────────────        ──────────────────────────────
    app/                        app/
    ├── app.py  (all-in-one)    ├── app.py         (thin entry point)
    ├── schema.py               ├── api/
    └── database/               │   ├── router.py  (HTTP endpoints)
        ├── models.py           │   └── schema/
        └── session.py          │       └── shipment_schema.py
                                ├── database/
                                │   ├── config.py  (pydantic-settings + .env)
                                │   ├── models.py  (SQLModel table)
                                │   └── session.py (async engine + DI chain)
                                └── services/
                                    └── shipment_service.py (business logic)
    ```
    Also: SQLite replaced by **PostgreSQL** via **asyncpg**.

---

## Lesson 7.1: Configuration Management (`database/config.py`)

Hard-coding database credentials is a security risk. The solution is **environment variables** managed by `pydantic-settings`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Setting(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    model_config = SettingsConfigDict(env_file="./.env")

    @property
    def POSTGRES_URL(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

config = Setting()
```

### How it works

`BaseSettings` automatically reads values from:
1. **Environment variables** (e.g., `export POSTGRES_HOST=myserver`)
2. **`.env` file** (specified by `SettingsConfigDict(env_file="./.env")`)

Your `.env` file looks like:
```ini
POSTGRES_HOST = localhost
POSTGRES_PORT = 5432
POSTGRES_USER = postgres
POSTGRES_PASSWORD = root
POSTGRES_DB = fastship
```

!!! warning "Never commit `.env` to git!"
    Add `.env` to your `.gitignore`. It contains secrets. Provide a `.env.example` with placeholder values for other developers instead.

The `POSTGRES_URL` property assembles the **asyncpg connection string**:
```
postgresql+asyncpg://postgres:root@localhost:5432/fastship
│            │        │        │    │         │    │
protocol     driver   user     pw   host      port  database
```

The `+asyncpg` part tells SQLAlchemy to use the **asyncpg** driver instead of the default sync `psycopg2`.

---

## Lesson 7.2: The Async Engine (`database/session.py`)

### From sync to async

**Chapter 6 (sync):**
```python
from sqlalchemy import create_engine
from sqlmodel import Session

engine = create_engine("sqlite:///sqlite.db", echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

**Chapter 7 (async):**
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(url=config.POSTGRES_URL, echo=True)

async def get_session():
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
```

| Change | Why |
|--------|-----|
| `create_engine` → `create_async_engine` | Non-blocking DB connections |
| `Session` → `AsyncSession` | All operations are `await`-able |
| `sessionmaker(class_=AsyncSession)` | Factory that creates `AsyncSession` instances |
| `expire_on_commit=False` | Objects stay usable after commit (important for async — avoids lazy-load errors) |
| `def` → `async def get_session()` | Session yield must be async |

### Async `init_db()`

```python
async def init_db():
    async with engine.begin() as conn:
        from app.database.models import Shipment  # noqa: F401
        await conn.run_sync(SQLModel.metadata.create_all)
```

`engine.begin()` gives an async connection with an open transaction. `run_sync()` is the async adapter for running synchronous SQLAlchemy operations (like `create_all`) inside an async context.

---

## Lesson 7.3: The Service Layer (`services/shipment_service.py`)

Previously, business logic (creating a shipment with a default status, computing delivery date) lived inside endpoint functions. Now it lives in a dedicated **Service class**:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Shipment
from app.api.schema.shipment_schema import ShipmentCreate, ShipmentStatus, ShipmentUpdate
from datetime import datetime, timedelta

class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Shipment:
        return await self.session.get(Shipment, id)

    async def add(self, shipment_create: ShipmentCreate):
        shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.PLACED,
            estimated_delivery=datetime.now() + timedelta(days=3),
        )
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment.id

    async def update(self, id: int, shipment_update: dict) -> Shipment:
        shipment = await self.session.get(Shipment, id)
        shipment.sqlmodel_update(shipment_update)
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def delete(self, id: int) -> None:
        shipment = await self.session.get(Shipment, id)
        await self.session.delete(shipment)
        await self.session.commit()
```

**Why a Service layer?**

| Without Service | With Service |
|-----------------|-------------|
| Business logic in endpoints | Business logic is isolated and reusable |
| Hard to test endpoints | Test `ShipmentService` independently |
| Duplicate code if multiple routes need same logic | Single place to change delivery logic |
| Endpoint functions are long | Endpoints become 1-2 line delegators |

---

## Lesson 7.4: Wiring the DI Chain (`database/session.py`)

The dependency injection chain goes three levels deep:

```
HTTP Request
    │
    ▼
get_session()          → yields AsyncSession
    │
    ▼
get_shipment_service() → wraps session in ShipmentService
    │
    ▼
Endpoint function      → receives ShipmentService, calls it
```

```python
# Step 1: Session dependency
async def get_session():
    async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Step 2: Service dependency (depends on session)
async def get_shipment_service(session: SessionDep):
    return ShipmentService(session)

ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]
```

FastAPI resolves this chain automatically — each endpoint just declares `service: ShipmentServiceDep` and gets a fully configured service instance.

---

## Lesson 7.5: The API Router (`api/router.py`)

Endpoints are no longer in `app.py`. They live in `api/router.py` using FastAPI's `APIRouter`:

```python
from fastapi import HTTPException, status, APIRouter

shipment_router = APIRouter(prefix="/shipment", tags=["Shipment"])

@shipment_router.get("/{id}", response_model=ShipmentRead)
async def get_shipment(id: int, service: ShipmentServiceDep):
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Given ID doesn't exits")
    return shipment

@shipment_router.post("/", response_model=None)
async def submit_shipment(req_body: ShipmentCreate, service: ShipmentServiceDep):
    id = await service.add(req_body)
    return {"id": id}

@shipment_router.patch("/{id}", response_model=ShipmentRead)
async def update_shipment(id: int, req_body: ShipmentUpdate, service: ShipmentServiceDep):
    update_data = req_body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No data provided to update")
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(status_code=404, detail=f"Shipment with id {id} not found")
    shipment = await service.update(id, update_data)
    return shipment

@shipment_router.delete("/{id}")
async def cancel_shipment(id: int, service: ShipmentServiceDep) -> dict[str, str]:
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(status_code=404, detail=f"Shipment with id {id} not found")
    await service.delete(id)
    return {"detail": f"Shipment with id {id} is deleted"}
```

Key points:
- `prefix="/shipment"` means all routes are under `/shipment/...`
- `tags=["Shipment"]` groups them in the Scalar/Swagger UI
- All endpoints are `async def` — they `await` the service

### Registering the Router in `app.py`

```python
from app.api.router import shipment_router

app = FastAPI(lifespan=life_span)
app.include_router(shipment_router)
```

`app.py` is now just 28 lines. All it does is register the router and the lifespan.

---

## Lesson 7.6: Setting Up PostgreSQL Locally

To run this chapter, you need a running PostgreSQL instance.

**Option 1: Docker (Recommended)**
```bash
docker run --name fastship-pg \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=fastship \
  -p 5432:5432 \
  -d postgres:16
```

**Option 2: Local PostgreSQL install**
- Download from [postgresql.org](https://www.postgresql.org/download/)
- Create a database named `fastship`

**Install asyncpg driver:**
```bash
pip install asyncpg
```

**Run the server:**
```bash
uvicorn app.main:app --reload
```

On startup, watch the terminal — `init_db()` will auto-create the `shipment` table in PostgreSQL.

---

## What You Learned

In this chapter, you:

- ✅ Managed configuration with **`pydantic-settings`** and `.env` files
- ✅ Upgraded to a **PostgreSQL async engine** (`create_async_engine` + `asyncpg`)
- ✅ Made `init_db()` and `get_session()` fully **`async def`**
- ✅ Built a **Service layer** to separate business logic from endpoints
- ✅ Created a **DI chain** that auto-wires session → service → endpoint
- ✅ Used **`APIRouter`** to split endpoints into their own module
- ✅ Reduced `app.py` to a thin entry point

## Next Steps

The architecture is now production-grade. In the next chapter we add **full authentication** — a Seller model, bcrypt password hashing, JWT tokens, OAuth2 login/logout, and a Redis token blacklist so only authorized sellers can create or modify shipments!

**[Chapter 8: Authentication →](ch08-authentication.md)**

