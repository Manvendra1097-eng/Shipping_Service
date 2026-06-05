# Async, Concurrency & the Event Loop

Understanding how Python handles concurrency is one of the most important topics for building fast, scalable APIs. This page covers everything from the fundamentals of blocking vs non-blocking code, to `asyncio`, `async`/`await`, and how FastAPI uses all of it.

---

## Part 1: The Problem — Blocking I/O

Imagine your API receives 1,000 requests per second, and each request fetches data from a database that takes 50ms to respond. In a **synchronous (blocking)** server, here's what happens:

```
Request 1 → DB Query (wait 50ms) → Response
Request 2 → DB Query (wait 50ms) → Response  ← Has to wait for Request 1
Request 3 → DB Query (wait 50ms) → Response  ← Has to wait for Requests 1 & 2
```

The server is **idle for 50ms on every request**, waiting for the database. With 1 worker, it can only serve ~20 requests/sec even though the CPU is doing almost nothing.

This is called **I/O-bound work** — work where the bottleneck is waiting for an external system (database, disk, network) rather than the CPU.

!!! info "I/O-bound vs CPU-bound"
    | Type | Bottleneck | Example | Solution |
    |------|------------|---------|----------|
    | **I/O-bound** | Waiting for external systems | DB queries, HTTP calls, file reads | `async/await` |
    | **CPU-bound** | Computation | Image processing, encryption, ML | Multiprocessing, threads |

---

## Part 2: Concurrency vs Parallelism

These two terms are often confused:

```
Concurrency:  Task A ──→ pause → Task B ──→ pause → Task A resumes
              (One worker, switching between tasks during waiting time)

Parallelism:  Task A ──────────────→
              Task B ──────────────→
              (Multiple workers, tasks run simultaneously)
```

| | Concurrency | Parallelism |
|-|-------------|-------------|
| Workers | 1 thread | Multiple threads/processes |
| Use case | I/O-bound | CPU-bound |
| Python tool | `asyncio` | `threading`, `multiprocessing` |
| FastAPI tool | `async def` endpoints | Background tasks, workers |

Python's **Global Interpreter Lock (GIL)** means true thread-level parallelism is limited for CPU-bound tasks. But for I/O-bound work (like API servers), `asyncio`'s concurrency model is extremely efficient.

---

## Part 3: The Event Loop

`asyncio` at its core is an **event loop** — a single-threaded loop that manages a queue of tasks and switches between them whenever one is waiting.

```
                    ┌─────────────────────────────────────┐
                    │           Event Loop                 │
                    │                                      │
 Request 1 → add ──▶  Task 1: DB query → WAITING          │
 Request 2 → add ──▶  Task 2: DB query → WAITING    ◀─────┤ Polls tasks
 Request 3 → add ──▶  Task 3: compute → RUNNING           │ continuously
                    │                                      │
                    │  Task 1: DB responded → RESUME       │
                    └─────────────────────────────────────┘
```

The event loop never blocks. When Task 1 starts waiting for the database, it **yields control** back to the loop, which immediately starts Task 2. When the DB responds, Task 1 is put back in the ready queue.

This is how a **single thread** can handle thousands of concurrent connections.

---

## Part 4: `async` and `await` in Python

### `async def` — Define a Coroutine

A function defined with `async def` is a **coroutine function**. Calling it doesn't execute the function — it returns a **coroutine object**.

```python
async def fetch_shipment(id: int):
    # This function can pause and resume
    result = await database.get(id)  # Pauses here
    return result
```

```python
# Calling it returns a coroutine object, NOT the result
coro = fetch_shipment(1)  # Not executed yet!

# You must await it or run it via the event loop
result = await fetch_shipment(1)  # Now it executes
```

### `await` — Suspend and Resume

`await` can only be used inside an `async def` function. It does two things:

1. **Suspends** the current coroutine (gives up control to the event loop)
2. **Resumes** when the awaited operation completes

```python
async def my_endpoint():
    # ❌ This blocks the event loop — never do this!
    import time
    time.sleep(1)

    # ✅ This suspends and lets other tasks run
    import asyncio
    await asyncio.sleep(1)
```

!!! warning "The Golden Rule"
    **Never call blocking code from an `async def` function.** If you use a synchronous blocking library (like standard `sqlite3` or `requests`) inside `async def`, you block the entire event loop and kill your server's concurrency. Use async-compatible libraries instead:

    | Blocking (❌ in async) | Async alternative (✅) |
    |-----------------------|----------------------|
    | `requests` | `httpx`, `aiohttp` |
    | `sqlite3` | `aiosqlite` |
    | `time.sleep()` | `asyncio.sleep()` |
    | `open()` / `read()` | `aiofiles` |
    | `sqlalchemy` (sync) | `sqlalchemy[asyncio]` + `create_async_engine` |

---

## Part 5: `asyncio` Primitives

### `asyncio.sleep()`

The async version of `time.sleep()`. Suspends the coroutine without blocking the event loop:

```python
import asyncio

async def process():
    print("Starting...")
    await asyncio.sleep(2)  # Event loop is free for 2 seconds
    print("Done!")
```

### `asyncio.gather()` — Run Tasks Concurrently

Run multiple coroutines **at the same time** and wait for all of them:

```python
import asyncio

async def fetch_user(id: int):
    await asyncio.sleep(0.1)  # Simulate DB call
    return {"id": id, "name": "User"}

async def main():
    # ❌ Sequential — takes 0.3 seconds
    u1 = await fetch_user(1)
    u2 = await fetch_user(2)
    u3 = await fetch_user(3)

    # ✅ Concurrent — takes ~0.1 seconds (all run at once)
    u1, u2, u3 = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3),
    )
```

### `asyncio.create_task()` — Fire and Forget

Create a task that runs in the background without blocking the current coroutine:

```python
async def send_email(address: str):
    await asyncio.sleep(2)  # Simulate slow email sending
    print(f"Email sent to {address}")

async def create_shipment():
    # Start email task but don't wait for it
    task = asyncio.create_task(send_email("user@example.com"))
    
    # Continue immediately — shipment is created while email sends
    return {"id": 12703}
```

### `asyncio.timeout()` — Set Deadlines (Python 3.11+)

```python
import asyncio

async def fetch_with_timeout():
    try:
        async with asyncio.timeout(5.0):  # Fail if takes > 5 seconds
            result = await slow_database_query()
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Database timeout")
```
### `asyncio.wait()` — Wait With Control

`asyncio.wait()` is a lower-level alternative to `gather()` that gives you more control over how you wait — you get back two sets: `done` and `pending`:

```python
import asyncio

async def server():
    tasks = [asyncio.create_task(endpoints(route)) for route in test_routes]
    
    # Returns (done, pending) sets
    finished, pending = await asyncio.wait(tasks)
    
    for task in finished:
        print(task.result())
```

| | `gather()` | `wait()` |
|-|------------|----------|
| Returns | Ordered list of results | `(done, pending)` sets |
| Error handling | First exception cancels all (default) | You handle per-task |
| Use case | All tasks must succeed | Fine-grained control |

### `asyncio.TaskGroup` — Structured Concurrency (Python 3.11+)

`TaskGroup` is the modern, recommended way to run multiple tasks concurrently. It guarantees that if **any** task fails, all others are automatically cancelled — preventing silent orphaned tasks.

Here's the exact pattern from [`async.py`](../../async.py):

```python
import asyncio
from rich import print

async def endpoints(route: str):
    print("=" * 30)
    print(f"Start executing route {route}")
    await asyncio.sleep(1)          # Simulates a real I/O call (e.g. DB query)
    print(f"Stop executing route {route}")
    print("=" * 30)
    return route

test_routes = ["/test1", "/test2", "test3"]

async def server():
    start = time.perf_counter()

    async with asyncio.TaskGroup() as task_group:
        tasks = [
            task_group.create_task(endpoints(route))  # Task starts immediately
            for route in test_routes
        ]
        # You can await an individual task's result INSIDE the group
        print("Task[0] Result: ", await tasks[0])

    # All tasks are guaranteed complete here
    delay = time.perf_counter() - start
    print(f"Time taken: {delay:.3f} seconds")   # ~1 second, not 3!
```

**What makes `TaskGroup` special:**

1. `task_group.create_task()` schedules the coroutine immediately — all three routes start at the same time.
2. The `async with` block **waits for all tasks** to complete before exiting.
3. If any task raises an exception, the group cancels the rest and re-raises as an `ExceptionGroup`.
4. You can `await` individual tasks *inside* the block to get their results early.

!!! tip "TaskGroup vs gather() vs wait()"
    ```
    asyncio.gather()      → Simple, all-or-nothing, most common choice
    asyncio.wait()        → Low-level, fine-grained control over done/pending sets  
    asyncio.TaskGroup     → Structured, safe, exception-aware — preferred in Python 3.11+
    ```

### `asyncio.run()` — Entry Point

Everything async needs an entry point — a place to start the event loop. That's `asyncio.run()`:

```python
import asyncio

async def main():
    await asyncio.sleep(1)
    print("Done!")

# Correct: creates a new event loop, runs the coroutine, closes the loop
asyncio.run(main())

# In FastAPI, Uvicorn calls asyncio.run() for you — you never call it manually.
```

!!! warning "Only one `asyncio.run()` per program"
    Never call `asyncio.run()` inside an already-running event loop (like inside FastAPI or a Jupyter notebook). In those contexts, the loop is already running — just `await` your coroutines directly.

---

## Part 5b: Measuring Performance — `timing` Decorator

When learning async patterns, it's useful to measure how long things take. A reusable `timing` decorator (also in [`async.py`](../../async.py)) uses `functools.wraps` to preserve the wrapped function's name and docstring:

```python
import time
from functools import wraps

def timing(func):
    @wraps(func)           # Copies __name__, __doc__ etc from func to wrapper
    def wrapper(*args, **kwargs):
        start = time.perf_counter()    # High-resolution timer
        result = func(*args, **kwargs)
        delay = time.perf_counter() - start
        print(f"Time taken: {delay:.3f} seconds")
        return result
    return wrapper

@timing
def slow_operation():
    time.sleep(1)

slow_operation()  # prints: Time taken: 1.001 seconds
```

!!! note "Why `@wraps(func)`?"
    Without `@wraps`, the wrapped function loses its identity:
    ```python
    slow_operation.__name__  # → "wrapper"  ❌
    # With @wraps:
    slow_operation.__name__  # → "slow_operation"  ✅
    ```
    FastAPI uses `__name__` to generate operation IDs in OpenAPI docs — so this matters!

---


## Part 6: `async def` vs `def` in FastAPI

FastAPI supports **both** `def` and `async def` endpoints. The distinction is critical:


```python
# FastAPI runs this in a thread pool — safe for blocking code
@app.get("/sync-endpoint")
def get_sync():
    time.sleep(1)  # OK here — runs in a worker thread
    return {"message": "sync"}

# FastAPI runs this directly on the event loop — must NOT block
@app.get("/async-endpoint")
async def get_async():
    await asyncio.sleep(1)  # Must use async I/O
    return {"message": "async"}
```

!!! tip "FastAPI is smart about this"
    When you use a regular `def` endpoint, FastAPI automatically runs it in an **external thread pool** using `run_in_executor`, so it doesn't block the event loop. This is why plain `def` endpoints work fine with blocking code like `sqlite3`.

    When you use `async def`, FastAPI runs it **directly on the event loop**, so any blocking call will freeze the entire server.

### Decision Guide

| Use `def` | Use `async def` |
|-----------|----------------|
| Using `sqlite3`, `psycopg2` (sync) | Using `aiosqlite`, `asyncpg` (async) |
| Using `requests` library | Using `httpx`, `aiohttp` |
| Calling CPU-intensive code | Calling async DB sessions, async HTTP |
| Simple prototypes | Production with high I/O concurrency |

---

## Part 7: `asynccontextmanager` — The Lifespan Pattern

You already use this in `app.py`:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def life_span(app: FastAPI):
    print("Server started .......")   # Runs on startup
    init_db()
    yield                              # Server is running here
    print("Server stopping ...")      # Runs on shutdown

app = FastAPI(lifespan=life_span)
```

`@asynccontextmanager` turns an `async def` generator function into an async context manager. The `yield` divides it into:
- **Before `yield`**: startup logic (create DB tables, load ML models, connect to Redis)
- **After `yield`**: shutdown logic (close connections, flush caches, save state)

This replaces the older `@app.on_event("startup")` / `@app.on_event("shutdown")` decorators.

---

## Part 8: What's Coming — Async SQLModel

Currently in Chapter 6, we use a **synchronous** SQLAlchemy engine with `Session`:

```python
engine = create_engine("sqlite:///sqlite.db")  # Sync

def get_session():
    with Session(engine) as session:
        yield session
```

This means our `def` endpoints run in thread pools. The async upgrade is now live in **Chapter 7**! Here's the real code:

```python
# database/session.py — Chapter 7 (current)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    url="postgresql+asyncpg://user:pass@localhost/fastship",
    echo=True,
)

# sessionmaker creates a factory for AsyncSession instances
async def get_session():
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False   # Keep objects usable after commit!
    )
    async with async_session() as session:
        yield session

# Endpoints are now async def
@shipment_router.get("/{id}")
async def get_shipment(id: int, service: ShipmentServiceDep):
    shipment = await service.get(id)   # Non-blocking DB call
    return shipment

# init_db() is also async now
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

!!! tip "Key differences from sync engine"
    | Sync (Ch6) | Async (Ch7) |
    |------------|-------------|
    | `create_engine()` | `create_async_engine()` |
    | `Session` | `AsyncSession` |
    | `def get_session()` | `async def get_session()` |
    | `with Session() as s:` | `async with async_session() as s:` |
    | `session.get(Model, id)` | `await session.get(Model, id)` |
    | `SQLite` | `PostgreSQL via asyncpg` |
    | `def` endpoints | `async def` endpoints |

---

## Key Takeaways

| Concept | One-line Summary |
|---------|-----------------|
| **Event loop** | Single-threaded loop that switches between tasks during I/O waits |
| **`async def`** | Defines a coroutine — a function that can pause and resume |
| **`await`** | Pauses the current coroutine and yields control to the event loop |
| **`asyncio.gather()`** | Runs multiple coroutines concurrently, waits for all |
| **`asyncio.wait()`** | Lower-level gather — returns `(done, pending)` sets |
| **`asyncio.TaskGroup`** | Structured concurrency (Python 3.11+) — cancels siblings on failure |
| **`asyncio.create_task()`** | Runs a coroutine in the background without waiting |
| **`asyncio.run()`** | Entry point — creates and runs the event loop |
| **`def` in FastAPI** | Runs in a thread pool — safe for blocking I/O |
| **`async def` in FastAPI** | Runs on the event loop — must use only async I/O |
| **`asynccontextmanager`** | Turns an async generator into a context manager (used for lifespan) |
| **`create_async_engine`** | Non-blocking DB access via `asyncpg` (PostgreSQL) or `aiosqlite` |
| **`AsyncSession`** | All session operations (`get`, `add`, `delete`) become `await`-able |

---

## Further Reading

- [Python `asyncio` docs](https://docs.python.org/3/library/asyncio.html)
- [FastAPI: Concurrency and async/await](https://fastapi.tiangolo.com/async/)
- [SQLAlchemy Async I/O](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Real Python: Async IO](https://realpython.com/async-io-python/)

---

**[← Back to Home](../index.md)**
