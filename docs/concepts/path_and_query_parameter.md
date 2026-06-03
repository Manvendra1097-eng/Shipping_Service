# Path Parameters & Query Parameters

Two of the most common ways to pass data to an API endpoint are **path parameters** and **query parameters**. Understanding the difference — and when to use each — is essential for designing clean APIs.

---

## Path Parameters

A path parameter is part of the **URL path itself**. It identifies a specific resource.

```
GET /shipment/12701
              └──┬──┘
                 │
           path parameter
```

### How It Works in FastAPI

In your `app/main.py`, you already use a path parameter:

```python
@app.get("/shipment/{id}")
def get_shipment(id: str) -> dict[str, Any]:
    if id not in shipments:
        return {"details": "Given ID doesn't exits"}
    return shipments[id]
```

The `{id}` in the URL path is a **placeholder**. FastAPI:

1. Sees `{id}` in the route definition
2. Matches it against the actual URL (e.g., `/shipment/12701`)
3. Extracts the value `"12701"`
4. Passes it to the function as the `id` parameter

### Type Conversion

The type hint on the parameter controls how FastAPI handles the value:

```python
# String — no conversion, value stays as "12701"
def get_shipment(id: str):

# Integer — auto-converts "12701" to 12701
def get_shipment(id: int):

# Float — auto-converts "3.14" to 3.14
def get_shipment(price: float):
```

!!! tip "Automatic Validation"
    If `id: int` and someone visits `/shipment/abc`, FastAPI automatically returns a `422 Validation Error` — no extra code needed:

    ```json
    {
        "detail": [
            {
                "type": "int_parsing",
                "loc": ["path", "id"],
                "msg": "Input should be a valid integer",
                "input": "abc"
            }
        ]
    }
    ```

### Multiple Path Parameters

You can have multiple path parameters in a single route:

```python
@app.get("/warehouse/{warehouse_id}/shipment/{shipment_id}")
def get_warehouse_shipment(warehouse_id: int, shipment_id: int):
    return {
        "warehouse": warehouse_id,
        "shipment": shipment_id
    }
```

```
GET /warehouse/5/shipment/12701
               │            │
     warehouse_id=5   shipment_id=12701
```

---

## Query Parameters

A query parameter comes **after the `?`** in the URL. It's used for filtering, sorting, pagination, or optional configuration.

```
GET /shipments?status=in-transit&limit=10
               └──────┬──────┘  └──┬───┘
                      │            │
              query parameter  query parameter
```

### How It Works in FastAPI

Any function parameter that is **not** in the URL path is automatically treated as a query parameter:

```python
@app.get("/shipments")
def get_shipments(status: str, limit: int = 10):
    # status comes from ?status=...
    # limit comes from ?limit=... (defaults to 10 if not provided)
    filtered = [
        s for s in shipments.values()
        if s["status"] == status
    ]
    return filtered[:limit]
```

```
GET /shipments?status=in-transit         → status="in-transit", limit=10 (default)
GET /shipments?status=Ordered&limit=5    → status="Ordered", limit=5
```

### Required vs Optional

| Declaration | Required? | Example URL |
|-------------|-----------|-------------|
| `status: str` | ✅ Required | `/shipments?status=in-transit` |
| `limit: int = 10` | ❌ Optional (default: 10) | `/shipments` or `/shipments?limit=5` |
| `sort: str \| None = None` | ❌ Optional (default: None) | `/shipments` or `/shipments?sort=date` |

```python
@app.get("/shipments")
def get_shipments(
    status: str,                    # Required — 422 error if missing
    limit: int = 10,                # Optional — defaults to 10
    sort: str | None = None         # Optional — defaults to None
):
    ...
```

!!! warning "Missing required query parameters"
    If you call `GET /shipments` without `?status=...`, FastAPI returns:
    ```json
    {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "status"],
                "msg": "Field required"
            }
        ]
    }
    ```

---

## Path vs Query: When to Use Which?

| Use Case | Use | Example |
|----------|-----|---------|
| Identify a **specific resource** | Path parameter | `/shipment/12701` |
| **Filter** a collection | Query parameter | `/shipments?status=in-transit` |
| **Sort** results | Query parameter | `/shipments?sort=date` |
| **Paginate** results | Query parameter | `/shipments?page=2&limit=10` |
| **Search** | Query parameter | `/shipments?q=wooden` |
| Navigate a **hierarchy** | Path parameter | `/warehouse/5/shipment/12701` |

!!! info "Rule of Thumb"
    - **Path parameters** = *which* resource (identity)
    - **Query parameters** = *how* to return it (filtering, formatting)

    Think of it like a library: the path is the shelf location (`/shelf/3/book/42`), and the query is how you want it (`?format=pdf&language=en`).

---

## Combining Both

You can mix path and query parameters in the same endpoint:

```python
@app.get("/warehouse/{warehouse_id}/shipments")
def get_warehouse_shipments(
    warehouse_id: int,                     # Path parameter
    status: str | None = None,             # Query parameter (optional)
    limit: int = 20                        # Query parameter (optional)
):
    results = get_shipments_for_warehouse(warehouse_id)

    if status:
        results = [s for s in results if s["status"] == status]

    return results[:limit]
```

```
GET /warehouse/5/shipments                          → All shipments in warehouse 5
GET /warehouse/5/shipments?status=Ordered            → Only "Ordered" ones
GET /warehouse/5/shipments?status=Ordered&limit=3    → First 3 "Ordered" ones
```

**FastAPI knows the difference because:**

- `warehouse_id` appears in the path (`{warehouse_id}`) → **path parameter**
- `status` and `limit` do NOT appear in the path → **query parameters**

---

## In Your Code: A Practical Example

Here's how you could enhance the current `main.py` to use both types:

```python
# Current: Path parameter only
@app.get("/shipment/{id}")
def get_shipment(id: int) -> dict[str, Any]:
    if id not in shipments:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipments[id]

# New: Query parameters for filtering
@app.get("/shipments")
def list_shipments(
    status: str | None = None,
    limit: int = 10
) -> list[dict[str, Any]]:
    results = list(shipments.values())

    if status:
        results = [s for s in results if s["status"].lower() == status.lower()]

    return results[:limit]
```

Try it:

```bash
# All shipments
curl http://localhost:8000/shipments

# Filter by status
curl "http://localhost:8000/shipments?status=Ordered"

# Limit results
curl "http://localhost:8000/shipments?status=in-transit&limit=1"
```

---

## Advanced: Validation with `Query()` and `Path()`

FastAPI provides `Query()` and `Path()` for adding extra validation and metadata:

```python
from fastapi import FastAPI, Query, Path

@app.get("/shipment/{id}")
def get_shipment(
    id: int = Path(
        ...,                           # Required
        title="Shipment ID",
        description="The unique ID of the shipment",
        gt=0                           # Must be greater than 0
    )
):
    return shipments.get(id)

@app.get("/shipments")
def list_shipments(
    status: str | None = Query(
        default=None,
        min_length=2,                  # At least 2 characters
        max_length=50,                 # At most 50 characters
        description="Filter by shipment status"
    ),
    limit: int = Query(
        default=10,
        ge=1,                          # Minimum 1
        le=100,                        # Maximum 100
        description="Max number of results to return"
    )
):
    ...
```

| Validator | Meaning | Works on |
|-----------|---------|----------|
| `gt=0` | Greater than 0 | Numbers |
| `ge=1` | Greater than or equal to 1 | Numbers |
| `lt=100` | Less than 100 | Numbers |
| `le=100` | Less than or equal to 100 | Numbers |
| `min_length=2` | Minimum string length | Strings |
| `max_length=50` | Maximum string length | Strings |
| `pattern="^[a-z]+$"` | Regex pattern match | Strings |

!!! tip "These show up in your docs!"
    All `title`, `description`, and validation constraints are automatically included in the OpenAPI schema. So your Swagger UI and Scalar docs will display them — making your API self-documenting.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| **Path parameter** | Part of the URL path — identifies a resource (`/shipment/{id}`) |
| **Query parameter** | After the `?` — filters, sorts, paginates (`?status=Ordered&limit=10`) |
| **Type hints** | Control auto-conversion and validation (`id: int` auto-converts and validates) |
| **Default values** | Make query params optional (`limit: int = 10`) |
| **`Path()` / `Query()`** | Add extra validation and OpenAPI metadata |
| **FastAPI auto-detects** | In the path → path param. Not in the path → query param. |

---

## Further Reading

- [FastAPI Docs: Path Parameters](https://fastapi.tiangolo.com/tutorial/path-params/)
- [FastAPI Docs: Query Parameters](https://fastapi.tiangolo.com/tutorial/query-params/)
- [FastAPI Docs: Query Validation](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/)
- [FastAPI Docs: Path Validation](https://fastapi.tiangolo.com/tutorial/path-params-numeric-validations/)

---

**[← Back to Home](../index.md)**
