# APIRouter — Splitting Endpoints into Modules

As your FastAPI application grows, putting every endpoint in a single `app.py` becomes unmanageable. **`APIRouter`** lets you split endpoints into separate files, just like Flask Blueprints or Express Routers.

---

## The Problem with a Single File

```python
# ❌ app.py — growing out of control
app = FastAPI()

@app.get("/shipment/{id}") ...
@app.post("/shipment/") ...
@app.patch("/shipment/{id}") ...
@app.delete("/shipment/{id}") ...
@app.get("/user/{id}") ...
@app.post("/user/") ...
@app.get("/invoice/{id}") ...
# ... hundreds of routes
```

---

## Creating a Router

```python
# api/router.py
from fastapi import APIRouter

shipment_router = APIRouter(
    prefix="/shipment",   # All routes prefixed with /shipment
    tags=["Shipment"]     # Grouped under "Shipment" in Swagger/Scalar UI
)

@shipment_router.get("/{id}")
async def get_shipment(id: int):
    ...

@shipment_router.post("/")
async def create_shipment(...):
    ...
```

The decorators change from `@app.get` to `@router.get`, but everything else works identically.

---

## Registering the Router

```python
# app.py
from fastapi import FastAPI
from app.api.router import shipment_router

app = FastAPI()
app.include_router(shipment_router)
```

`include_router()` merges the router's routes into the main app. You can include as many routers as you like:

```python
app.include_router(shipment_router)
app.include_router(user_router)
app.include_router(invoice_router)
```

---

## Router Options

You can set most decorator-level options at the router level, applying them to all routes:

```python
shipment_router = APIRouter(
    prefix="/shipment",
    tags=["Shipment"],
    dependencies=[Depends(require_auth)],   # Protect all routes with auth
    responses={404: {"description": "Not found"}},  # Shared response docs
)
```

### Overriding at Route Level

Options set on the route override the router's defaults:

```python
@shipment_router.get("/{id}", tags=["Public"])  # Overrides router's tag
async def get_shipment(id: int):
    ...
```

---

## Nested Routers

Routers can include other routers, allowing deep nesting:

```python
# api/v1/router.py
v1_router = APIRouter(prefix="/v1")
v1_router.include_router(shipment_router)
v1_router.include_router(user_router)

# app.py
app.include_router(v1_router)
# Results in: /v1/shipment/{id}, /v1/user/{id}
```

---

## Recommended File Structure

```
app/
├── app.py                     # FastAPI app + router registration
└── api/
    ├── __init__.py
    ├── router.py              # Or: one router.py per resource
    ├── shipment_router.py
    ├── user_router.py
    └── schema/
        └── shipment_schema.py
```

---

## Key Takeaways

| Feature | Benefit |
|---------|---------|
| `prefix="/shipment"` | No need to repeat prefix on every route |
| `tags=["Shipment"]` | Groups in Swagger/Scalar UI |
| `include_router()` | Plugs into the main app cleanly |
| `dependencies=` at router level | Apply auth/middleware to all routes in router |
| One file per resource | Scales to hundreds of endpoints without chaos |

---

**[← Back to Home](../index.md)**
