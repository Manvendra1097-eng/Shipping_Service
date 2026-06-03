# Chapter 2: Building API Endpoints

In this chapter, you'll build real API endpoints for a Shipping API. You'll learn how to define routes, work with in-memory data, use path parameters, and handle errors — all concepts you'll use in every FastAPI project.

!!! note "Code Evolution"
    This chapter uses **in-memory dictionaries** as our data store. This is intentional — it lets us focus purely on FastAPI's routing and endpoint features. In later chapters, we'll progressively upgrade:

    - **Chapter 4**: Replace raw `dict` with **Pydantic models** for structured validation
    - **Chapter 5**: Add **POST, PUT, DELETE** endpoints for full CRUD
    - **Chapter 6**: Swap the dictionary for **SQLModel** + SQLite (SQLModel = SQLAlchemy + Pydantic, built by the FastAPI author!)
    - **Chapter 8**: Migrate to **PostgreSQL** with **Alembic** migrations for production

    Each upgrade builds on what you learn here, so these fundamentals stay relevant.

---

## The Goal

By the end of this chapter, your API will have these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/shipment/latest` | GET | Get the most recent shipment |
| `/shipment/{id}` | GET | Get a specific shipment by its ID |
| `/scalar` | GET | Interactive API documentation |

All of these are already implemented in your `app/main.py`. Let's walk through the code line by line.

---

## Lesson 2.1: In-Memory Data

Before connecting a database, it's common to start with **in-memory data** — a Python dictionary that acts as a temporary data store. Here's our shipment data:

```python
shipments = {
    12701: {
        "id": 12701,
        "content": "Wooden table",
        "status": "in-transit"
    },
    12702: {
        "id": 12702,
        "content": "Wooden Chai",
        "status": "Ordered"
    }
}
```

!!! info "Why a dictionary?"
    We use the shipment ID as the dictionary **key** for O(1) lookups. When you look up `shipments[12701]`, Python doesn't need to search through every item — it jumps directly to the right one. This mirrors how a database index works.

**Key points:**

- The data lives in memory — it resets every time you restart the server
- Each shipment has an `id`, `content` (what's being shipped), and `status`
- This is a great starting point for prototyping before adding a real database

!!! warning "This will change"
    In Chapter 6, we'll replace this dictionary with **SQLModel** + SQLite so data persists across server restarts. SQLModel is built by the same author as FastAPI and combines SQLAlchemy's database power with Pydantic's validation.

---

## Lesson 2.2: Your First GET Endpoint

Let's create an endpoint that returns the most recently added shipment:

```python
from fastapi import FastAPI
from typing import Any

app = FastAPI()

@app.get("/shipment/latest")
def get_latest_shipment() -> dict[str, Any]:
    id = max(shipments.keys())
    return shipments[id]
```

Let's break this down piece by piece:

### The Decorator: `@app.get("/shipment/latest")`

| Part | Meaning |
|------|---------|
| `@app` | Attach this route to our FastAPI application |
| `.get` | This endpoint responds to HTTP **GET** requests |
| `"/shipment/latest"` | The URL path for this endpoint |

!!! tip "HTTP Methods"
    FastAPI supports all standard HTTP methods: `@app.get()`, `@app.post()`, `@app.put()`, `@app.delete()`, `@app.patch()`. Each maps to a different type of operation. GET = read data, POST = create data, PUT = update data, DELETE = remove data. We'll use POST, PUT, and DELETE in Chapter 5.

### The Function

```python
def get_latest_shipment() -> dict[str, Any]:
```

- The function name (`get_latest_shipment`) becomes the **operation ID** in the auto-generated docs
- `-> dict[str, Any]` is a **return type hint** — it tells FastAPI (and developers) what shape the response will have
- FastAPI automatically converts the returned dictionary to **JSON**

!!! note "Better return types coming"
    Returning `dict[str, Any]` works, but it's loosely typed. In Chapter 4, we'll replace this with a **Pydantic model** like `-> Shipment`, which gives us automatic validation, documentation, and IDE autocomplete. Then in Chapter 6, **SQLModel** will let this same model double as a database table definition!

### The Logic

```python
id = max(shipments.keys())
return shipments[id]
```

- `shipments.keys()` returns all the IDs: `[12701, 12702]`
- `max()` finds the highest ID: `12702`
- We return that shipment as a dictionary — FastAPI serializes it to JSON

### Try It

With your server running (`uvicorn app.main:app --reload`), open your browser:

```
http://localhost:8000/shipment/latest
```

You should see:

```json
{
    "id": 12702,
    "content": "Wooden Chai",
    "status": "Ordered"
}
```

---

## Lesson 2.3: Path Parameters

What if you want to look up a **specific** shipment by its ID? That's where **path parameters** come in:

```python
@app.get("/shipment/{id}")
def get_shipment(id: str) -> dict[str, Any]:
    if id not in shipments:
        return {
            "details": "Given ID doesn't exits"
        }
    return shipments[id]
```

### How Path Parameters Work

The `{id}` in the URL path is a **placeholder**. When someone visits `/shipment/12701`, FastAPI:

1. Extracts `"12701"` from the URL
2. Passes it to the function as the `id` parameter
3. The function uses it to look up the shipment

```
URL:  /shipment/12701
                └──┬──┘
                   │
                   ▼
def get_shipment(id: str):
                 └──┬──┘
                    │
            id = "12701"
```

### Type Hint Matters: `id: str`

Notice that `id` is typed as `str`, not `int`. This means:

- FastAPI will pass the value as a **string**: `"12701"`
- But our dictionary keys are **integers**: `12701`
- So `"12701" not in shipments` is always `True`!

!!! warning "A Bug to Fix!"
    This is an intentional learning moment. The parameter type should be `int` to match the dictionary keys:

    ```python
    @app.get("/shipment/{id}")
    def get_shipment(id: int) -> dict[str, Any]:
    ```

    With `id: int`, FastAPI will **automatically convert** the string `"12701"` from the URL into the integer `12701`. If someone passes a non-numeric value like `/shipment/abc`, FastAPI will automatically return a `422 Validation Error` — no extra code needed!

### Try It

```
http://localhost:8000/shipment/12701
```

---

## Lesson 2.4: Error Handling

The current error handling returns a plain dictionary:

```python
if id not in shipments:
    return {
        "details": "Given ID doesn't exits"
    }
```

This works, but it has a problem: **the HTTP status code is still 200 (OK)**. Any client consuming this API would think the request succeeded, even though the shipment wasn't found.

!!! tip "The Better Way: HTTPException"
    FastAPI provides `HTTPException` for returning proper error responses:

    ```python
    from fastapi import FastAPI, HTTPException

    @app.get("/shipment/{id}")
    def get_shipment(id: int) -> dict[str, Any]:
        if id not in shipments:
            raise HTTPException(
                status_code=404,
                detail="Shipment not found"
            )
        return shipments[id]
    ```

    Now the client receives a `404 Not Found` status code, which is the correct HTTP semantic for "this resource doesn't exist." We'll implement proper error handling in Chapter 12.

### Common HTTP Status Codes

| Code | Meaning | When to use |
|------|---------|-------------|
| `200` | OK | Request succeeded |
| `201` | Created | New resource was created (POST) |
| `204` | No Content | Success, but nothing to return (DELETE) |
| `400` | Bad Request | Client sent invalid data |
| `404` | Not Found | Resource doesn't exist |
| `422` | Unprocessable Entity | Validation error (FastAPI auto-generates this) |
| `500` | Internal Server Error | Something broke on the server |

---

## Lesson 2.5: API Documentation with Scalar

The last endpoint serves the Scalar documentation UI:

```python
from scalar_fastapi import get_scalar_api_reference

@app.get("/scalar", include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
    )
```

### What's Happening Here?

1. **`get_scalar_api_reference()`** — Returns an HTML page with the Scalar UI
2. **`openapi_url=app.openapi_url`** — Tells Scalar where to find the OpenAPI schema (defaults to `/openapi.json`)
3. **`include_in_schema=False`** — This is a meta-endpoint (it *serves* docs, it *isn't* an API endpoint). This flag hides it from the auto-generated docs so it doesn't show up as a regular endpoint

!!! info "FastAPI's Built-in Docs vs Scalar"
    FastAPI already gives you free docs at `/docs` (Swagger UI) and `/redoc` (ReDoc). Scalar is a **third-party alternative** with a more modern look and feel. You can use any or all of them!

---

## The Complete Code

Here's the full `app/main.py` with all the pieces together:

```python
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from typing import Any

app = FastAPI()

shipments = {
    12701:{
        "id": 12701,
        "content": "Wooden table",
        "status": "in-transit"
    },
     12702:{
        "id": 12702,
        "content": "Wooden Chai",
        "status": "Ordered"
    }
}

@app.get("/shipment/latest")
def get_latest_shipment() -> dict[str, Any]:
    id = max(shipments.keys())
    return shipments[id]

@app.get("/shipment/{id}")
def get_shipment(id: str) -> dict[str, Any]:
    if id not in shipments:
        return {
            "details": "Given ID doesn't exits"
        }
    return shipments[id]

@app.get("/scalar",include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url= app.openapi_url,
    )
```

---

## 🏋️ Try It Yourself

Here are some exercises to solidify what you learned:

!!! example "Exercise 1: Fix the Bug"
    Change `id: str` to `id: int` in `get_shipment()` and see how FastAPI handles the type conversion automatically. Try visiting `/shipment/abc` — what happens?

!!! example "Exercise 2: Add a New Endpoint"
    Create a `GET /shipments` endpoint (notice the plural) that returns **all** shipments as a list:
    ```python
    @app.get("/shipments")
    def get_all_shipments() -> list[dict[str, Any]]:
        return list(shipments.values())
    ```

!!! example "Exercise 3: Add a POST Endpoint"
    Create a `POST /shipment` endpoint that adds a new shipment. You'll need to accept JSON data in the request body:
    ```python
    @app.post("/shipment")
    def create_shipment(shipment: dict[str, Any]) -> dict[str, Any]:
        new_id = max(shipments.keys()) + 1
        shipment["id"] = new_id
        shipments[new_id] = shipment
        return shipment
    ```
    Test it with: `curl -X POST http://localhost:8000/shipment -H "Content-Type: application/json" -d '{"content": "Glass vase", "status": "pending"}'`

---

## What You Learned

In this chapter, you:

- ✅ Created in-memory data as a temporary data store
- ✅ Built a `GET` endpoint that returns the latest shipment
- ✅ Used **path parameters** to look up specific resources
- ✅ Understood the type hint bug (`str` vs `int`) and why it matters
- ✅ Learned about proper **HTTP error handling** with `HTTPException`
- ✅ Explored how Scalar API docs are served with `include_in_schema=False`

---

## Next Steps

Your API is functional, but how does it all work behind the scenes? In the next chapter, we'll look under the hood at FastAPI's request lifecycle, ASGI, and auto-generated schemas.

**[Chapter 3: How FastAPI Works Under the Hood →](ch03-under-the-hood.md)**
