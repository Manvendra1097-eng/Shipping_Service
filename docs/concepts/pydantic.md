# Data Validation with Pydantic

When building APIs, you can't trust the data the client sends you. You need to ensure that the data is exactly what you expect (e.g., `id` is an integer, `status` is a string, `weight` is a positive float). 

Writing manual `if/else` checks for every field in every endpoint is tedious and error-prone. This is where **Pydantic** comes in.

## What is Pydantic?

[Pydantic](https://docs.pydantic.dev/) is a Python library for data parsing and validation using Python type hints. It is deeply integrated into FastAPI and is what gives FastAPI its magical powers of validation and automatic documentation.

Instead of writing manual checks, you define the "shape" of your data using a Python class. Pydantic guarantees that the data matches that shape, or it throws a clear validation error.

---

## Defining a Pydantic Model

You define a Pydantic model by creating a class that inherits from `BaseModel`.

```python
from pydantic import BaseModel, Field

class Shipment(BaseModel):
    id: int
    content: str
    weight: float
    status: str = "Placed"  # Default value if not provided
```

### What happens here?
1. **Type hints:** We specify that `id` must be an `int`, `content` a `str`, etc.
2. **Required vs Optional:** Because `id`, `content`, and `weight` don't have default values, they are **required**. If the client doesn't send them, Pydantic raises an error.
3. **Defaults:** Because `status` has a default value (`"Placed"`), it is **optional**. If the client omits it, Pydantic uses `"Placed"`.

---

## Using Models in FastAPI

Let's see how Pydantic replaces raw dictionaries in your FastAPI endpoints.

### 1. Request Bodies (Receiving Data)

**Without Pydantic (The old way):**
```python
@app.post("/shipment")
def create_shipment(req_body: dict[str, Any]):
    # We have to manually extract and hope the keys exist!
    weight = req_body["weight"] 
    ...
```

**With Pydantic:**
```python
@app.post("/shipment")
def create_shipment(shipment: Shipment):
    # FastAPI automatically parses the JSON body into the Shipment model
    # We can access fields safely using dot notation!
    weight = shipment.weight
    ...
```

If a client sends this invalid JSON:
```json
{
    "content": "Glass vase",
    "weight": "very heavy"
}
```
FastAPI and Pydantic will automatically intercept the request and return a `422 Unprocessable Entity` error before your function even runs:
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "id"],
            "msg": "Field required"
        },
        {
            "type": "float_parsing",
            "loc": ["body", "weight"],
            "msg": "Input should be a valid number",
            "input": "very heavy"
        }
    ]
}
```

### 2. Response Models (Sending Data)

You can also use Pydantic models to define what your API *returns*.

```python
@app.get("/shipment/{id}", response_model=Shipment)
def get_shipment(id: int):
    # ... logic ...
    return shipments[id]
```

Why use `response_model`?
1. **Data Filtering:** If your dictionary/database record contains a secret field (e.g., `internal_notes`), but your `Shipment` model doesn't include it, FastAPI will automatically strip it out before sending the response to the client.
2. **Automatic Serialization:** FastAPI automatically converts your Python objects into JSON based on the model.
3. **Documentation:** It tells the OpenAPI schema exactly what this endpoint returns, populating your Scalar/Swagger UI.

---

## Advanced Validation with `Field`

Sometimes basic types aren't enough. You might want to say "weight must be greater than 0" or "content can't be longer than 100 characters". You do this using Pydantic's `Field` function.

```python
from pydantic import BaseModel, Field

class Shipment(BaseModel):
    id: int = Field(gt=0, description="The unique shipment ID")
    content: str = Field(min_length=3, max_length=100)
    weight: float = Field(gt=0, description="Weight in kg")
    status: str = Field(default="Placed", pattern="^(Placed|in-transit|Delivered)$")
```

If someone tries to create a shipment with `weight: -5`, Pydantic will instantly reject it!

---

## Key Takeaways

| Feature | Benefit |
|---------|---------|
| **Validation** | Rejects bad data before your endpoint logic even runs. |
| **Serialization** | Automatically converts JSON to Python objects (and vice versa). |
| **Autocomplete** | Your IDE knows exactly what fields exist (e.g., `shipment.weight`). |
| **Documentation** | Your UI docs get beautiful, accurate schemas automatically. |

In **Chapter 4**, we will refactor our Shipping API to replace all `dict[str, Any]` occurrences with proper Pydantic models!

---

**[← Back to Home](../index.md)**
