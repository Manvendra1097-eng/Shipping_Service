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

class BaseShipment(BaseModel):
    content: str
    weight: float
```

### Required vs Optional
Because `content` and `weight` don't have default values, they are **required**. If the client doesn't send them, Pydantic raises a `422 Unprocessable Entity` error.

To make a field optional, you can use `Optional` (or `| None`) and provide a default:
```python
from typing import Optional

class BaseShipment(BaseModel):
    content: str
    weight: float
    destination: Optional[int] = None
```

---

## The "Create vs Read" Inheritance Pattern

In real APIs, the data you **receive** (Create) is rarely identical to the data you **return** (Read). 

For example, when creating a shipment, the user shouldn't send the `status` — the server decides that. But when reading a shipment, the user *needs* to see the `status`.

You can solve this using standard Python inheritance:

```python
# 1. Base fields shared by everything
class BaseShipment(BaseModel):
    content: str
    weight: float

# 2. Schema for the Request Body (POST)
class ShipmentCreate(BaseShipment):
    pass # Uses just the base fields

# 3. Schema for the Response (GET)
class ShipmentRead(BaseShipment):
    status: str # Adds status to the response
    
# 4. Schema for Updates (PATCH)
class ShipmentUpdate(BaseModel):
    status: str # Only allows updating the status field
```

This prevents malicious users from sending `{"status": "delivered"}` during creation!

---

## Using Models in FastAPI

### Request Bodies & Responses

Use your inherited schemas in your endpoints:

```python
# Accept ShipmentCreate, Return ShipmentRead
@app.post("/shipment", response_model=ShipmentRead)
def create_shipment(shipment: ShipmentCreate):
    
    # We can access fields safely using dot notation!
    weight = shipment.weight
    
    # ... logic ...
```

Why use `response_model`?
1. **Data Filtering:** If your database dictionary contains a secret field (e.g., `internal_notes`), but your `ShipmentRead` model doesn't include it, FastAPI will automatically strip it out before sending the response.
2. **Documentation:** It tells the OpenAPI schema exactly what this endpoint returns, populating your Scalar/Swagger UI.

---

## Advanced Features

### Validation with `Field`

Sometimes types aren't enough. You might want to say "weight must be less than 25kg" or "content can't be longer than 30 characters". You do this using Pydantic's `Field` function.

```python
class BaseShipment(BaseModel):
    content: str = Field(max_length=30, description="Contents of the shipment")
    weight: float = Field(lt=25, description="Weight in kg")
```

### Default Factories

If you need a default value to be generated dynamically (like a random ID, a UUID, or the current timestamp), use `default_factory`:

```python
from random import randint

def random_generator():
    return randint(110000, 129999)

class BaseShipment(BaseModel):
    destination: Optional[int] = Field(default_factory=random_generator)
```
Every time a new `BaseShipment` is instantiated without a destination, Pydantic will execute `random_generator()` to create one.

### Dumping Data to Dictionaries

When you need to save your Pydantic object into a dictionary (or database), you use the `.model_dump()` method.

```python
shipment_dict = req_body.model_dump()
```

`.model_dump()` takes several powerful arguments to shape the output:

- `exclude_none=True`: Removes any keys from the dictionary where the value is `None`. This is incredibly useful for `PATCH` requests where you only want to update fields the user actually provided!
- `exclude_unset=True`: Removes any keys that were populated by default values (only includes fields the user explicitly set).
- `exclude={"weight"}`: Explicitly removes the `weight` key from the resulting dictionary.

```python
# Perfect for PATCH endpoints!
update_data = req_body.model_dump(exclude_none=True)
```

---

## Key Takeaways

| Feature | Benefit |
|---------|---------|
| **Inheritance** | Define `Base`, `Create`, and `Read` schemas to strictly control inputs and outputs. |
| **Field Validation** | Rejects bad data (`lt=25`) before your endpoint logic even runs. |
| **`model_dump()`** | Converts Pydantic objects to dictionaries. Use `exclude_none=True` for clean updates. |
| **Documentation** | Your UI docs get beautiful, accurate schemas automatically. |

---

**[← Back to Home](../index.md)**
