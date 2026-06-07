# SQLModel Relationships & Eager Loading

SQLModel (via SQLAlchemy ORM) lets you define relationships between tables as Python attributes. Instead of manually writing JOIN queries, you access related objects as regular Python attributes. In async contexts, **eager loading** is mandatory.

---

## Defining Relationships

Relationships are declared on the model using `Relationship()` and correspond to a foreign key column:

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import UUID

class Seller(SQLModel, table=True):
    id: UUID = ...
    shipments: list["Shipment"] = Relationship(back_populates="seller")

class Shipment(SQLModel, table=True):
    seller_id: UUID = Field(foreign_key="seller.id")   # FK column in DB
    seller: "Seller" = Relationship(back_populates="shipments")  # ORM attribute (no DB column)

    delivery_partner_id: Optional[UUID] = Field(
        default=None, foreign_key="delivery_partner.id"
    )
    delivery_partner: Optional["DeliveryPartner"] = Relationship(back_populates="shipments")
```

| Part | What it does |
|------|-------------|
| `seller_id: UUID = Field(foreign_key="seller.id")` | Creates the FK column in the database |
| `seller: "Seller" = Relationship(...)` | ORM-level attribute — no DB column, enables `shipment.seller` |
| `back_populates="shipments"` | Links the two sides — `seller.shipments` and `shipment.seller` stay in sync |

!!! warning "String forward references"
    Use string literals (`"Seller"` not `Seller`) when the referenced class is defined later in the file, or in another module that would cause a circular import.

---

## One-to-Many vs Many-to-One

In our model, one `Seller` has many `Shipments`:

```
Seller (1) ─────────────────── (many) Shipment
```

- On the "one" side (`Seller`): `shipments: list[Shipment] = Relationship(...)`
- On the "many" side (`Shipment`): `seller: Seller = Relationship(...)`

---

## Optional Relationships

`delivery_partner` is optional — a shipment may not have one assigned yet:

```python
delivery_partner_id: Optional[UUID] = Field(default=None, foreign_key="delivery_partner.id")
delivery_partner: Optional["DeliveryPartner"] = Relationship(back_populates="shipments")
```

The response schema handles this with:
```python
class ShipmentRead(BaseShipment):
    delivery_partner: DeliveryPartnerRead | None = None
```

---

## Lazy Loading vs Eager Loading

By default, SQLAlchemy uses **lazy loading** — related objects are fetched on first access via a separate SQL query. This works in synchronous code:

```python
# Sync — OK (but N+1 problem)
seller = session.get(Seller, id)
print(seller.name)         # SELECT seller WHERE id=...
print(seller.shipments)    # SELECT shipment WHERE seller_id=...  ← extra query
```

**In async SQLAlchemy, lazy loading is broken.** Accessing a relationship attribute outside an active `async with` session raises `sqlalchemy.exc.MissingGreenlet`.

---

## `selectinload` — The Async Solution

`selectinload` tells SQLAlchemy to fetch related objects in a **second query immediately**, before the session closes:

```python
from sqlalchemy.orm import selectinload
from sqlmodel import select

async def get(self, id: UUID) -> Shipment:
    stm = (
        select(Shipment)
        .options(
            selectinload(Shipment.seller),            # Load seller in one extra query
            selectinload(Shipment.delivery_partner),  # Load delivery_partner in another
        )
        .where(Shipment.id == id)
    )
    result = await self.session.execute(stm)
    return result.scalar_one_or_none()
```

SQLAlchemy executes two additional `SELECT ... WHERE id IN (...)` queries — one for sellers, one for delivery partners. You then access them without any further DB calls.

---

## Comparison: Loading Strategies

| Strategy | How | When to use |
|----------|-----|-------------|
| `selectinload` | Separate `SELECT ... WHERE id IN (...)` | Many records, async |
| `joinedload` | `LEFT OUTER JOIN` in the same query | Single record, one relationship |
| `subqueryload` | Subquery in main query | Large collections |
| Lazy (default) | Extra query on first access | Sync only — breaks in async! |

For most async FastAPI use cases, `selectinload` is the right choice.

---

## Nested Response Schemas

Once relationships are eagerly loaded, Pydantic can serialize nested objects automatically:

```python
class ShipmentRead(BaseShipment):
    seller: SellerRead                          # Nested Pydantic model
    delivery_partner: DeliveryPartnerRead | None = None  # Optional nested
```

FastAPI serializes `Shipment.seller` (a `Seller` ORM object) into `SellerRead` (a Pydantic model). This works because Pydantic v2 can read attributes from ORM objects.

---

## `scalar_one_or_none()` vs `scalar()`

When fetching with `select()`, use the right result accessor:

```python
result = await session.execute(stm)

result.scalar_one_or_none()   # Returns one or None — raises if multiple rows
result.scalar()               # Returns first or None — silent if multiple rows
result.scalars().all()        # Returns all as a list
result.all()                  # Returns list of tuples (used with multi-column selects)
```

Use `scalar_one_or_none()` when you expect exactly 0 or 1 row. Use `scalars().all()` when fetching many records.

---

## PostgreSQL ARRAY Columns

SQLModel doesn't have a native list field for integers — use SQLAlchemy's `ARRAY`:

```python
from sqlalchemy import ARRAY, INTEGER, Column
from sqlmodel import Field

serviceable_zip_code: list[int] = Field(sa_column=Column(ARRAY(INTEGER)))
```

Query with PostgreSQL's `ANY()` operator:
```python
statement = select(DeliveryPartner).where(
    DeliveryPartner.serviceable_zip_code.any(destination_zip_code)
)
```

This translates to: `WHERE 110001 = ANY(serviceable_zip_code)` in PostgreSQL.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| `Field(foreign_key=...)` | Creates the FK column in DB |
| `Relationship(back_populates=...)` | ORM attribute — no DB column |
| `selectinload` | Eager-loads relations — **required in async** |
| Lazy loading in async | Raises `MissingGreenlet` — never use in FastAPI |
| `scalar_one_or_none()` | Correct accessor for 0-or-1 result |
| `ARRAY(INTEGER)` | PostgreSQL native array column |
| Nested Pydantic schemas | FastAPI auto-serialises ORM relationships |

---

**[← Back to Home](../index.md)**
