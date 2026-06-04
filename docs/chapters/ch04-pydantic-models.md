# Chapter 4: Pydantic Models & Schemas

In Chapter 2, we built endpoints that manually accepted and returned raw dictionaries (`dict[str, Any]`). This worked, but it had several issues:

- **No Validation:** A client could send `{"weight": "heavy"}` instead of a number, and our app would crash.
- **No Autocomplete:** Your IDE didn't know what fields were inside the dictionary.
- **Poor Documentation:** The OpenAPI docs didn't know what data to expect.

In this chapter, we fix all of that using **Pydantic**, FastAPI's built-in data validation engine. We will also learn an advanced pattern: using different schemas for Creating vs Reading data.

!!! note "Code Evolution"
    We are splitting our code into two files:
    
    1. `app/schema.py` — Where we define the "shape" of our data using Pydantic.
    2. `app/app.py` — Our endpoints (renamed from `main.py`).

---

## Lesson 4.1: Defining the Schema (`schema.py`)

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

### 2. Base Models & Inheritance

In real APIs, the data you *receive* to create an item is often different from the data you *return* when reading an item. For example, when creating a shipment, the client doesn't send the `status` (it defaults to "placed"). But when reading a shipment, we *do* want to return the status.

We can solve this elegantly using **Pydantic Inheritance**:

```python
from random import randint
from typing import Optional
from pydantic import BaseModel, Field

def random_generator():
    return randint(110000, 129999)

# 1. The Base Model (Shared Fields)
class BaseShipment(BaseModel):
    content: str = Field(max_length=30, description="Contents of the shipment")
    weight: float = Field(lt=25, description="Weight of the shipment in kg")
    destination: Optional[int] = Field(
        default_factory=random_generator,
        description="Destination zipcode, if not passed send to random location 😁",
    )

# 2. Used for POST requests (Creating)
class ShipmentCreate(BaseShipment):
    pass  # Inherits content, weight, and destination. No status needed!

# 3. Used for GET requests (Reading)
class ShipmentRead(BaseShipment):
    status: ShipmentStatus  # Adds the status field to the base fields

# 4. Used for PATCH requests (Updating)
class ShipmentUpdate(BaseModel):
    status: ShipmentStatus = Field(description="Status of the shipment")
```

**The Magic of `Field`:**
- `max_length=30`: FastAPI will reject any content string longer than 30 characters.
- `lt=25`: The weight must be strictly *less than* 25 kg.
- `default_factory`: If the client omits `destination`, Pydantic calls `random_generator()` to create one dynamically!

---

## Lesson 4.2: Using the Models in Endpoints

Now open your `app/app.py`. Let's import our new schemas and upgrade our endpoints.

### The Import

```python
from app.schema import ShipmentCreate, ShipmentRead, ShipmentStatus, ShipmentUpdate
```

### 1. Upgrading the POST Endpoint

```python
@app.post("/shipment", response_model=ShipmentRead)
def submit_shipment(req_body: ShipmentCreate):
    id = max(shipments.keys()) + 1
    
    # .model_dump() converts the Pydantic model to a dictionary
    shipments[id] = {**req_body.model_dump(), "status": ShipmentStatus.PLACED}
    
    return shipments[id]
```

**What changed?**
- **`req_body: ShipmentCreate`**: Validates incoming JSON. The client doesn't send `status`.
- **`response_model=ShipmentRead`**: Tells FastAPI that the return value will include the `status`.
- **`.model_dump()`**: Converts the Pydantic object into a dictionary so we can store it in our in-memory database.

### 2. Upgrading the GET Endpoint

```python
@app.get("/shipment/{id}", response_model=ShipmentRead)
def get_shipment(id: int | None = None):
    if id is None:
        id = max(shipments.keys())
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given ID doesn't exits"
        )
    return shipments[id]
```
Notice how `response_model=ShipmentRead` ensures the returned dictionary is automatically validated and serialized according to our schema.

### 3. Upgrading the PATCH Endpoint

```python
@app.patch("/shipment/{id}", response_model=ShipmentRead)
def update_shipment(id: int, req_body: ShipmentUpdate):
    shipment = shipments[id]
    shipment.update(req_body)
    return shipments[id]
```
By using `ShipmentUpdate`, we strict restrict the client to *only* updating the `status` field. They cannot accidentally or maliciously change the `weight` or `content`!

---

## 🏋️ Try It Yourself

Start your server (note the new filename!):
```bash
uvicorn app.app:app --reload
```

### 1. Check the Docs
Open `http://localhost:8000/scalar`. Look at the `POST /shipment` endpoint:
- The Request Body only asks for `content`, `weight`, and `destination` (`ShipmentCreate`).
- The Response Model includes `status` (`ShipmentRead`).
- The `PATCH` endpoint only allows modifying the `status` (`ShipmentUpdate`).

### 2. Test Validation
Try sending a POST request with a weight that is too high (e.g., `30`):
```bash
curl -X POST http://localhost:8000/shipment \
  -H "Content-Type: application/json" \
  -d '{"content": "Heavy bricks", "weight": 30.5}'
```
You will get a `422 Unprocessable Entity` error back from FastAPI saying the weight must be less than 25.

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
- ✅ Used **Pydantic Inheritance** to create separate Create, Read, and Update schemas.
- ✅ Created a `BaseModel` with `Field` constraints (max length, less than).
- ✅ Used `default_factory` to dynamically generate default values.
- ✅ Used `.model_dump()` to convert validated objects back into dictionaries.

## Next Steps

Currently, our endpoints are fully validated, but we are still saving everything to an in-memory dictionary. In the next chapter we'll replace it with a real **SQLite database** that persists across server restarts!

**[Chapter 5: SQLite Database →](ch05-sqlite.md)**

