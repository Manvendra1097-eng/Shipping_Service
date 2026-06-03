# Chapter 4: Pydantic Models

In Chapter 2, we built endpoints that manually accepted and returned raw dictionaries (`dict[str, Any]`). This worked, but it had several issues:

- **No Validation:** A client could send `{"weight": "heavy"}` instead of a number, and our app would crash when it tried to process it.
- **No Autocomplete:** Your IDE didn't know what fields were inside the dictionary.
- **Poor Documentation:** The OpenAPI docs didn't know what data to expect.

In this chapter, we fix all of that using **Pydantic**, FastAPI's built-in data validation engine.

!!! note "Code Evolution"
    We are splitting our code into two files:
    
    1. `app/schema.py` — Where we define the "shape" of our data using Pydantic.
    2. `app/app.py` — Our endpoints (renamed from `main.py`).

---

## Lesson 4.1: Defining the Schema

Create a new file `app/schema.py`. This is where we will define what a "Shipment" actually looks like.

### 1. The Shipment Status (Enum)

First, a shipment status shouldn't be any random string. It should be a specific set of allowed values. We use Python's `Enum` for this:

```python
from enum import Enum

class ShipmentStatus(str, Enum):
    PLACED = "placed"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_of_delivery"
    DELIVERED = "delivered"
```

!!! tip "Why `str, Enum`?"
    Inheriting from both `str` and `Enum` tells FastAPI to serialize these values as standard strings in JSON responses. See the [Enumerations concept page](../concepts/enum.md) for a deep dive!

### 2. The Shipment Model (BaseModel)

Next, we define the `Shipment` class by inheriting from Pydantic's `BaseModel`:

```python
from random import randint
from typing import Optional
from pydantic import BaseModel, Field

def random_generator():
    return randint(110000, 129999)

class Shipment(BaseModel):
    content: str = Field(max_length=30, description="Contents of the shipment")
    weight: float = Field(lt=25, description="Weight of the shipment in kg")
    destination: Optional[int] = Field(
        default_factory=random_generator,
        description="Destination zipcode, if not passed send to random location 😁",
    )
    status: ShipmentStatus = Field(
        default=ShipmentStatus.PLACED, description="Status of the shipment"
    )
```

**Let's break down the magic of `Field`:**
- `max_length=30`: FastAPI will reject any content string longer than 30 characters.
- `lt=25`: The weight must be strictly *less than* 25 kg.
- `default_factory=random_generator`: If the client doesn't provide a destination zip code, Pydantic will call the `random_generator` function to create one dynamically!
- `status: ShipmentStatus = Field(default=ShipmentStatus.PLACED)`: The status defaults to "placed" and is strictly validated against our Enum.

---

## Lesson 4.2: Using the Model in Endpoints

Now open your `app/app.py` (which you should rename from `main.py`). Let's import our new schema and upgrade the `POST /shipment` endpoint.

### The Import

```python
from app.schema import Shipment
```

### Upgrading the POST Endpoint

**Before (Chapter 2):**
```python
@app.post("/shipment")
def submit_shipment(req_body: dict[str, Any]) -> dict[str, Any]:
    id = max(shipments.keys()) + 1
    weight = req_body["weight"]
    content = req_body["content"]
    # ...
```

**After (Chapter 4):**
```python
@app.post("/shipment", response_model=Shipment)
def submit_shipment(req_body: Shipment):
    id = max(shipments.keys()) + 1
    
    # Convert the Pydantic model to a dictionary to store it
    shipments[id] = req_body.model_dump()
    
    # Convert the dictionary back to a Pydantic model to return it
    return Shipment.model_validate(shipments[id])
```

### What changed?

1. **`req_body: Shipment`**: FastAPI automatically reads the JSON request, validates it against the `Shipment` rules (max length, max weight, allowed enums), and passes us a Python object. If validation fails, it returns a `422` error automatically!
2. **`response_model=Shipment`**: Tells FastAPI that this endpoint returns a `Shipment` object. This makes your Scalar documentation incredibly detailed.
3. **`model_dump()`**: Converts the Pydantic object back into a standard Python dictionary so we can store it in our `shipments` dictionary.
4. **`model_validate()`**: Converts a dictionary back into a Pydantic object.

---

## 🏋️ Try It Yourself

Start your server (note the new filename!):
```bash
uvicorn app.app:app --reload
```

### 1. Check the Docs
Open `http://localhost:8000/scalar`. Look at the `POST /shipment` endpoint. You'll see:
- A dropdown menu for `status`
- The descriptions ("Weight of the shipment in kg")
- The constraints (`< 25`)

### 2. Test Validation
Try sending a POST request with a weight that is too high (e.g., `30`):
```bash
curl -X POST http://localhost:8000/shipment \
  -H "Content-Type: application/json" \
  -d '{"content": "Heavy bricks", "weight": 30.5}'
```
You will get a clear error back from FastAPI saying the weight must be less than 25.

### 3. Test Default Factory
Try sending a request *without* a `destination`:
```bash
curl -X POST http://localhost:8000/shipment \
  -H "Content-Type: application/json" \
  -d '{"content": "Mystery Box", "weight": 2.0}'
```
Look at the response — Pydantic automatically generated a random zip code for you!

---

## What You Learned

In this chapter, you:

- ✅ Extracted your data structures into a dedicated `schema.py` file.
- ✅ Used `Enum` to restrict values to a specific set.
- ✅ Created a `BaseModel` with `Field` constraints (max length, less than).
- ✅ Used `default_factory` to dynamically generate default values.
- ✅ Updated an endpoint to use `response_model` and parse the request body automatically.
- ✅ Used `model_dump()` and `model_validate()` to bridge Pydantic and raw dictionaries.

## Next Steps

Currently, our `PATCH` and `GET` endpoints are still using raw dictionaries. In the future, we'll replace the entire `shipments` dictionary with **SQLModel** (Chapter 6), which combines Pydantic and SQLAlchemy to seamlessly save these validated models directly to a database!
