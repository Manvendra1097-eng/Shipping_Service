# Enumerations (Enums)

When building an API, you often have fields that can only accept a specific set of predefined values. For example, a shipment status shouldn't just be *any* string; it should only be one of `"Placed"`, `"in-transit"`, or `"Delivered"`.

Python's built-in **`Enum`** class, combined with FastAPI and Pydantic, is the perfect tool for this.

---

## What is an Enum?

An Enum (short for "enumeration") is a way to define a set of named constants.

```python
from enum import Enum

class ShipmentStatus(str, Enum):
    PLACED = "Placed"
    IN_TRANSIT = "in-transit"
    DELIVERED = "Delivered"
```

### Why inherit from `str` AND `Enum`?

By inheriting from `str` and `Enum`, we create a **String Enum**. This tells FastAPI and Pydantic:
> *"This is an enumeration, but under the hood, treat the values as normal strings."*

This is crucial for serialization. If you just inherit from `Enum`, FastAPI won't know how to turn it into JSON correctly. By inheriting from `str`, FastAPI knows to send it as a standard string.

---

## Enums in FastAPI Endpoints

You can use Enums directly in your FastAPI path parameters or query parameters.

### 1. As a Query Parameter

Let's say you want to filter shipments by status:

```python
from fastapi import FastAPI
from enum import Enum

app = FastAPI()

class ShipmentStatus(str, Enum):
    PLACED = "Placed"
    IN_TRANSIT = "in-transit"
    DELIVERED = "Delivered"

@app.get("/shipments")
def get_shipments(status: ShipmentStatus):
    return {"message": f"Getting all shipments with status: {status.value}"}
```

### The Magic of Enums in FastAPI

When you do this, two magical things happen:

1. **Automatic Validation:**
   If a client requests `/shipments?status=Lost`, FastAPI will automatically reject it with a `422 Unprocessable Entity` error, because `"Lost"` is not in the Enum.
   ```json
   {
     "detail": [
       {
         "type": "enum",
         "loc": ["query", "status"],
         "msg": "Input should be 'Placed', 'in-transit' or 'Delivered'",
         "input": "Lost"
       }
     ]
   }
   ```

2. **Drop-downs in API Docs:**
   If you look at your Scalar or Swagger UI docs, the `status` field won't be a generic text box. It will be a **drop-down menu** populated with the allowed values!

---

## Enums in Pydantic Models

Enums shine brightest when paired with Pydantic models for your request and response bodies.

### The Old Way (Manual Validation)

Without an Enum, you might try to use a Regex pattern in a `Field`, or write manual Python checks:

```python
# ❌ Error-prone and hard to maintain
class Shipment(BaseModel):
    # What if we need to add a "Cancelled" status later? We have to update the regex.
    status: str = Field(pattern="^(Placed|in-transit|Delivered)$") 
```

### The Enum Way (Type-Safe)

With an Enum, the code is self-documenting and type-safe:

```python
from enum import Enum
from pydantic import BaseModel

class ShipmentStatus(str, Enum):
    PLACED = "Placed"
    IN_TRANSIT = "in-transit"
    DELIVERED = "Delivered"

class Shipment(BaseModel):
    id: int
    content: str
    weight: float
    status: ShipmentStatus = ShipmentStatus.PLACED  # Using the Enum as the type!
```

Now, when a client sends a `POST` request to create a shipment:
- Pydantic ensures the `status` string they send matches one of the Enum values.
- In your Python code, `shipment.status` isn't just a string, it's an instance of `ShipmentStatus`, meaning you get full IDE autocomplete and type safety.

```python
@app.post("/shipment")
def create_shipment(shipment: Shipment):
    # IDE autocomplete knows about ShipmentStatus.DELIVERED!
    if shipment.status == ShipmentStatus.DELIVERED:
        send_delivery_email()
    
    return shipment
```

---

## Key Takeaways

| Benefit | Description |
|---------|-------------|
| **Validation** | Rejects invalid strings automatically (e.g., `"Lost"` instead of `"in-transit"`). |
| **Documentation** | Generates drop-down menus in your API docs (Swagger/Scalar). |
| **Type Safety** | Prevents typos in your Python code. `ShipmentStatus.PLACE` will throw an error, whereas typing `"Place"` manually might go unnoticed. |
| **Centralized Logic** | If you add a new status later, you only add it to the Enum class. |

When we refactor our API to use Pydantic models in **Chapter 4**, we'll definitely use an Enum for the shipment `status`!

---

**[← Back to Home](../index.md)**
