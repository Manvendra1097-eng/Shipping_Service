# Chapter 3: How FastAPI Works Under the Hood

You've built endpoints and tested them in the browser. But what actually happens between the moment you hit Enter on a URL and the moment JSON appears on screen? In this chapter, we'll peel back the layers.

---

## Lesson 3.1: The Request-Response Lifecycle

Every API call follows this journey:

```
 ┌──────────┐     HTTP Request      ┌──────────┐     ASGI       ┌──────────┐
 │  Client  │ ──────────────────►   │  Uvicorn │ ───────────►   │  FastAPI │
 │ (Browser │                       │ (Server) │                │  (App)   │
 │  / curl) │ ◄──────────────────   │          │ ◄───────────   │          │
 └──────────┘     HTTP Response     └──────────┘   Response     └──────────┘
```

Here's what happens step by step when you visit `http://localhost:8000/shipment/latest`:

### Step 1: Client Sends Request

Your browser creates an HTTP request:
```http
GET /shipment/latest HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Step 2: Uvicorn Receives It

Uvicorn is listening on port 8000. It receives the raw HTTP bytes and converts them into a structured ASGI message that FastAPI can understand.

### Step 3: FastAPI Routes the Request

FastAPI looks at the **path** (`/shipment/latest`) and the **method** (`GET`) and finds the matching function:

```python
@app.get("/shipment/latest")  # ← This matches!
def get_latest_shipment() -> dict[str, Any]:
```

!!! info "Route Matching Order"
    FastAPI checks routes **in the order they are defined**. This is why `/shipment/latest` is defined **before** `/shipment/{id}` in `main.py`. If they were reversed, visiting `/shipment/latest` would match `{id}` first, with `id = "latest"`!

### Step 4: Function Executes

The matched function runs and returns a Python dictionary:
```python
{"id": 12702, "content": "Wooden Chai", "status": "Ordered"}
```

### Step 5: FastAPI Serializes the Response

FastAPI automatically:

1. Converts the dictionary to **JSON** using `jsonable_encoder`
2. Sets the `Content-Type` header to `application/json`
3. Sets the status code to `200 OK`

### Step 6: Client Receives JSON

```json
{
    "id": 12702,
    "content": "Wooden Chai",
    "status": "Ordered"
}
```

!!! note "This lifecycle gets richer"
    As we add features in later chapters, new steps will be inserted into this lifecycle:

    - **Chapter 4**: Pydantic validates and serializes the response model
    - **Chapter 6**: SQLModel runs a database query in Step 4 instead of a dict lookup
    - **Chapter 9**: OAuth2 middleware checks JWT tokens between Steps 2 and 3
    - **Chapter 12**: Custom middleware can add logging, CORS headers, etc.

---

## Lesson 3.2: ASGI & Uvicorn

### What is ASGI?

**ASGI** (Asynchronous Server Gateway Interface) is a standard that defines how a Python web server communicates with a Python web application. It's the modern replacement for **WSGI** (used by Flask and Django).

| Feature | WSGI (old) | ASGI (new) |
|---------|-----------|-----------|
| Async support | ❌ | ✅ |
| WebSockets | ❌ | ✅ |
| HTTP/2 | ❌ | ✅ |
| Used by | Flask, Django | FastAPI, Starlette |

### What Does `--reload` Do?

When you run:
```bash
uvicorn app.main:app --reload
```

The `--reload` flag starts a **file watcher** (using the `watchfiles` library). When you save a change to any `.py` file, Uvicorn:

1. Detects the file change
2. Stops the running server process
3. Starts a new server process with the updated code

!!! warning "Development Only!"
    Never use `--reload` in production. It adds overhead from file watching and can cause brief downtime during restarts. For production, run without it:
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000
    ```
    We'll cover production deployment with Docker in Chapters 17-18.

---

## Lesson 3.3: Type Hints Power Everything

FastAPI's superpower is its use of **Python type hints**. They're not just documentation — FastAPI reads them at startup and uses them to power validation, serialization, and docs.

### Return Type Hints

Look at this function signature:

```python
def get_latest_shipment() -> dict[str, Any]:
```

The `-> dict[str, Any]` tells FastAPI:

- The response will be a **dictionary**
- Keys are **strings**, values can be **anything**
- FastAPI uses this to generate the response schema in the OpenAPI docs

### Parameter Type Hints

```python
def get_shipment(id: str) -> dict[str, Any]:
```

The `id: str` tells FastAPI:

- Extract `id` from the path
- It should be a **string**
- If conversion fails, return a `422 Validation Error` automatically

!!! tip "The Power of Type Hints"
    Change `id: str` to `id: int` and you get **automatic integer validation for free**:

    - `/shipment/12701` → ✅ `id = 12701` (auto-converted to int)
    - `/shipment/abc` → ❌ `422 Validation Error` (auto-rejected)

    No `if` statements, no `try/except`, no manual parsing. FastAPI handles it all.

!!! note "Type hints get even more powerful"
    In Chapter 4, we'll use **Pydantic models** as type hints. Instead of `dict[str, Any]`, you'll write `Shipment` — and FastAPI will validate every field, generate detailed schemas, and provide IDE autocomplete. In Chapter 6, **SQLModel** takes this further by making those same models work as database tables too!

---

## Lesson 3.4: The Auto-Generated OpenAPI Schema

One of FastAPI's most impressive features is **automatic API documentation**. It reads your code and generates a complete OpenAPI specification.

### What is OpenAPI?

OpenAPI (formerly Swagger) is an **industry standard** for describing REST APIs. It's a JSON/YAML file that describes:

- All your endpoints (paths, methods)
- Request parameters and their types
- Response formats
- Error responses

### See It Yourself

Visit `http://localhost:8000/openapi.json` while your server is running. You'll see something like:

```json
{
    "openapi": "3.1.0",
    "info": {
        "title": "FastAPI",
        "version": "0.1.0"
    },
    "paths": {
        "/shipment/latest": {
            "get": {
                "summary": "Get Latest Shipment",
                "operationId": "get_latest_shipment_shipment_latest_get",
                "responses": {
                    "200": {
                        "description": "Successful Response"
                    }
                }
            }
        },
        "/shipment/{id}": {
            "get": {
                "summary": "Get Shipment",
                "operationId": "get_shipment_shipment__id__get",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": { "type": "string" }
                    }
                ]
            }
        }
    }
}
```

### How FastAPI Builds This

FastAPI inspects your code **at startup** and extracts:

| Your Code | Becomes in OpenAPI |
|-----------|-------------------|
| `@app.get("/shipment/latest")` | Path + method |
| `def get_latest_shipment` | `operationId` and `summary` |
| `id: str` | Parameter with `type: string` |
| `-> dict[str, Any]` | Response schema |

!!! info "This is why type hints matter so much"
    In Flask, type hints are optional documentation. In FastAPI, they're **functional** — they drive validation, serialization, AND documentation generation. One source of truth for everything.

### Three Documentation UIs

FastAPI gives you three ways to view these docs:

| URL | UI | Notes |
|-----|----|-------|
| `/docs` | Swagger UI | Built into FastAPI, interactive |
| `/redoc` | ReDoc | Built into FastAPI, clean layout |
| `/scalar` | Scalar | Added via `scalar-fastapi` package, modern design |

All three read from the same `/openapi.json` — they're just different frontends for the same data.

---

## What You Learned

In this chapter, you:

- ✅ Traced the full **request → response lifecycle** from browser to JSON
- ✅ Understood **ASGI** and how Uvicorn serves your app
- ✅ Learned why **route order matters** in FastAPI
- ✅ Discovered how **type hints** power validation, serialization, and docs simultaneously
- ✅ Explored the **OpenAPI schema** that FastAPI auto-generates from your code

---

## What's Next? — Tutorial Roadmap

You now understand the fundamentals of FastAPI. Here's the full roadmap of upcoming chapters:

| Chapter | Topic | What You'll Learn | Status |
|---------|-------|-------------------|--------|
| ~~Ch 1~~ | ~~Getting Started~~ | ~~Project setup, virtual environments~~ | ✅ Done |
| ~~Ch 2~~ | ~~Building Endpoints~~ | ~~GET routes, path parameters, error handling~~ | ✅ Done |
| ~~Ch 3~~ | ~~Under the Hood~~ | ~~Request lifecycle, ASGI, type hints, OpenAPI~~ | ✅ Done |
| **Ch 4** | **Pydantic Models** | Request/response schemas, data validation | 🔜 Coming |
| **Ch 5** | **Full CRUD** | POST, PUT, DELETE — complete shipment lifecycle | 🔜 Coming |
| **Ch 6** | **SQLModel & SQLite** | Replace in-memory dict with SQLModel ORM + SQLite | 🔜 Coming |
| **Ch 7** | **DB Relationships** | One-to-Many, Many-to-Many relationships | 🔜 Coming |
| **Ch 8** | **PostgreSQL & Alembic** | Upgrade to PostgreSQL, schema migrations | 🔜 Coming |
| **Ch 9** | **OAuth2 & JWT** | Login/logout, JWT tokens, password hashing | 🔜 Coming |
| **Ch 10** | **Protecting Endpoints** | Dependency injection for auth, role-based access | 🔜 Coming |
| **Ch 11** | **Async & Background Tasks** | `async/await`, background jobs | 🔜 Coming |
| **Ch 12** | **Error Handling & Middleware** | Custom exceptions, CORS, request/response hooks | 🔜 Coming |
| **Ch 13** | **Dependency Injection** | Cleaner code with FastAPI's DI system | 🔜 Coming |
| **Ch 14-15** | **Testing with Pytest** | Unit tests, TestClient, dependency overrides | 🔜 Coming |
| **Ch 16** | **React Integration** | Connecting a React frontend to your API | 🔜 Coming |
| **Ch 17-18** | **Docker & Deployment** | Containerize, Docker Compose, production deploy | 🔜 Coming |

!!! tip "Want to dive deeper now?"
    Check out the [Python Decorators](../concepts/decorator.md) concept page to understand the magic behind `@app.get()`.

---

## Further Reading

- [FastAPI Official Tutorial](https://fastapi.tiangolo.com/tutorial/) — The official, comprehensive guide
- [Uvicorn Documentation](https://www.uvicorn.org/) — ASGI server configuration
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html) — The standard behind API docs
