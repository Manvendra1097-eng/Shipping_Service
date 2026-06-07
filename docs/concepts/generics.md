# Python Generics — Type-Safe Reusable Code

Python's `typing.Generic` lets you write classes and functions that work correctly with **any type**, while still giving the type checker full information about what type is being used. In our codebase, it's used to build `BaseService[ModelT, IdT]` — a single class that handles CRUD for any SQLModel table.

---

## The Problem: Repeated Code

Without generics, every service repeats the same boilerplate:

```python
class SellerService:
    async def add_and_commit(self, seller: Seller) -> Seller:
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller

class ShipmentService:
    async def add_and_commit(self, shipment: Shipment) -> Shipment:
        self.session.add(shipment)          # Exact same code!
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment
```

---

## TypeVar — Parameterising a Class

`TypeVar` creates a placeholder for a type that will be filled in later:

```python
from typing import TypeVar

ModelT = TypeVar("ModelT")   # "some model type, TBD"
IdT = TypeVar("IdT")         # "some ID type, TBD"
```

---

## `Generic[ModelT, IdT]` — The Base Class

```python
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT")

class BaseService(Generic[ModelT, IdT]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model: type[ModelT], id: IdT) -> ModelT | None:
        return await self.session.get(model, id)

    async def add_and_commit(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update_and_commit(self, instance: ModelT, **changes) -> ModelT:
        instance.sqlmodel_update(changes)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete_and_commit(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.commit()
```

---

## Using a Generic Class

Subclasses specify the type parameters when inheriting:

```python
from uuid import UUID

class ShipmentService(BaseService[Shipment, UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def delete(self, id: UUID) -> None:
        shipment = await self.get_by_id(Shipment, id)  # Returns Shipment | None
        await self.delete_and_commit(shipment)           # Accepts Shipment
```

The type checker now knows:
- `get_by_id(Shipment, id)` returns `Shipment | None`
- `add_and_commit(shipment)` accepts a `Shipment` and returns `Shipment`

---

## Constrained TypeVars — `bound=`

You can restrict what types are allowed:

```python
ModelT = TypeVar("ModelT", bound=User)   # Must be User or a subclass

class AuthEntityService(BaseService[ModelT, UUID], Generic[ModelT]):
    ...
```

`bound=User` means only `Seller`, `DeliveryPartner`, or other `User` subclasses can be used as `ModelT`. This lets `AuthEntityService` safely access `user.email` and `user.password` — it knows the type has those fields.

---

## Inheriting From Two Bases

A class can inherit from both `BaseService` and declare its own generic parameter:

```python
class AuthEntityService(BaseService[ModelT, UUID], Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]):
        super().__init__(session)
        self.model = model
```

Then concrete classes fix the type:

```python
class SellerService(AuthEntityService[Seller]):    # ModelT = Seller
    def __init__(self, session: AsyncSession):
        super().__init__(session, Seller)
```

---

## The Full Inheritance Chain

```
BaseService[ModelT, IdT]            — session + CRUD helpers
    │
    └── AuthEntityService[ModelT]   — login, get_entity, logout (bound=User)
            │
            ├── SellerService       — add() with hash_password
            └── DeliveryPartnerService — add() with hash_password + zip codes
```

---

## Generics vs `Any`

```python
# ❌ Using Any — no type safety
class BaseService:
    async def add_and_commit(self, instance: Any) -> Any: ...

# ✅ Using Generic — full type safety
class BaseService(Generic[ModelT, IdT]):
    async def add_and_commit(self, instance: ModelT) -> ModelT: ...
```

With `Any`, a type checker can't warn you if you pass a `Shipment` where a `Seller` is expected. With `Generic`, it can.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| `TypeVar("T")` | Placeholder for an unknown-but-consistent type |
| `Generic[T]` | Makes the class parameterisable by a type |
| `bound=User` | Restricts TypeVar to a class and its subclasses |
| `MyClass[Concrete]` | Fixes the TypeVar when inheriting or annotating |
| Why use it? | Write once, reuse for any model — no copy-paste |

---

**[← Back to Home](../index.md)**
