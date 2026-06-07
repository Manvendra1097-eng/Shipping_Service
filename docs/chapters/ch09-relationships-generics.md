# Chapter 9: Delivery Partners, Relationships & Generic Services

This chapter introduces our third actor — the **Delivery Partner** — and brings in two of the most important software design patterns in the codebase: **database relationships** and **generic base classes**.

!!! note "What Changed"
    ```
    app/
    ├── database/
    │   └── models.py              UPDATED — UUID PKs, User base class,
    │                                         Seller/DeliveryPartner + Relationships
    ├── services/
    │   ├── base_service.py        NEW — Generic[ModelT, IdT] with shared CRUD
    │   ├── auth_service.py        NEW — Pure functions: hash_password, verify_password,
    │                                     issue_access_token(+role), blacklist_token_if_valid
    │   ├── auth_entity_service.py NEW — AuthEntityService[ModelT](session, model, role)
    │   ├── seller_service.py      UPDATED — passes role="seller" to AuthEntityService
    │   ├── delivery_partner_service.py  NEW — role="delivery_partner"
    │   └── shipment_service.py    UPDATED — Smart partner assignment, selectinload,
    │                                         NoDeliveryPartnerAvailableError, UUID IDs
    ├── api/
    │   ├── router/
    │   │   ├── delivery_partner_router.py  NEW — /partner/signup, /login, /logout
    │   │   │                                     uses PartnerPayloadDep
    │   │   └── seller_router.py           UPDATED — uses SellerPayloadDep
    │   └── schema/
    │       ├── delivery_partner_schema.py  NEW — DeliveryPartnerCreate/Read
    │       └── shipment_schema.py          UPDATED — seller + delivery_partner in ShipmentRead
    └── dependencies.py            UPDATED — split OAuth2 schemes per actor, role validation,
                                             _get_logged_in_entity generic helper,
                                             SellerPayloadDep + PartnerPayloadDep
    ```

---

## Lesson 9.1: Refactored Models — UUID PKs & Relationships

### The `User` Base Class

Instead of duplicating `name`, `email`, `password` in both `Seller` and `DeliveryPartner`, a shared non-table base class does the work:

```python
class User(SQLModel):           # No table=True — this is just a shared base
    name: str
    email: EmailStr
    password: str

class Seller(User, table=True):
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True), default_factory=uuid4)
    shipments: list["Shipment"] = Relationship(back_populates="seller")

class DeliveryPartner(User, table=True):
    __tablename__ = "delivery_partner"
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True), default_factory=uuid4)
    serviceable_zip_code: list[int] = Field(sa_column=Column(ARRAY(INTEGER)))
    max_handling_capacity: int
    shipments: list["Shipment"] = Relationship(back_populates="delivery_partner")
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
```

### UUID Primary Keys

All IDs moved from `int` to `UUID`:

```python
id: UUID = Field(
    sa_column=Column(pg.UUID, primary_key=True),
    default_factory=uuid4     # Auto-generate a UUID on creation
)
```

**Why UUID instead of integer?**

| Integer ID | UUID |
|-----------|------|
| Sequential (predictable) | Random (unpredictable) |
| Leaks record count | No information leakage |
| Auto-increment requires DB roundtrip | Generated in Python before DB insert |
| Can't merge distributed datasets | Globally unique |

### SQLModel Relationships

```python
class Shipment(SQLModel, table=True):
    seller_id: UUID = Field(foreign_key="seller.id")
    seller: "Seller" = Relationship(back_populates="shipments")

    delivery_partner_id: Optional[UUID] = Field(
        default=None, foreign_key="delivery_partner.id"
    )
    delivery_partner: "DeliveryPartner" = Relationship(back_populates="shipments")
    
    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
```

`Relationship()` is SQLModel's ORM-level association. It does NOT create a database column — it tells SQLAlchemy how to join tables when loading related objects.

!!! tip "Optional FK"
    `delivery_partner_id: Optional[UUID] = Field(default=None, ...)` means a shipment can exist without an assigned partner (e.g., immediately after creation before assignment runs).

---

## Lesson 9.2: Generic `BaseService` — DRY Service Foundation

Instead of repeating `session.get`, `session.add`, `session.commit`, `session.refresh` in every service, a `Generic` base class captures this pattern once:

```python
from typing import Generic, TypeVar

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

`Generic[ModelT, IdT]` means the class works with **any model type** and **any ID type**. Subclasses declare their types when inheriting:

```python
class ShipmentService(BaseService[Shipment, UUID]):   # ModelT=Shipment, IdT=UUID
    ...
```

---

## Lesson 9.3: `auth_service.py` — Pure Authentication Functions

Authentication logic (hashing, JWT, blacklist) is extracted into **pure functions** — no class, no state, just behaviour:

```python
from passlib.context import CryptContext
from app.database.redis import add_jti_to_blacklist
from app.utils import get_token

ctx = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    return ctx.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return ctx.verify(password, hashed_password)

# role is embedded in the token payload so the API can verify WHO issued it
def issue_access_token(name: str, user_id: str, role: str) -> str:
    return get_token(data={"name": name, "id": user_id, "role": role})

async def blacklist_token_if_valid(jti: str, exp: int | float) -> None:
    ex = int(exp) - int(datetime.now(timezone.utc).timestamp())
    if ex <= 0:
        return    # Token already expired — no need to blacklist
    await add_jti_to_blacklist(jti, ex)
```

The key addition is the `role` parameter in `issue_access_token`. Every token now carries a `"role"` claim — `"seller"` or `"delivery_partner"`. This allows the API to reject a delivery partner's token on a seller-only endpoint.

!!! tip "Pure functions vs methods"
    These functions have **no dependency on `self`** — they're standalone utilities. Keeping them separate makes them trivially testable and reusable by any service.

---

## Lesson 9.4: `AuthEntityService` — Generic Auth Mixin

`AuthEntityService` sits between `BaseService` and the concrete services. It now also stores the **role string** used to stamp every token:

```python
ModelT = TypeVar("ModelT", bound=User)   # Constrained: must be a User subclass

class AuthEntityService(BaseService[ModelT, UUID], Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT], role: str):
        super().__init__(session)
        self.model = model    # The concrete model class (Seller or DeliveryPartner)
        self.role = role      # "seller" or "delivery_partner"

    async def login_with_email(self, email: str, password: str) -> str | None:
        statement = select(self.model).where(self.model.email == email)
        result = await self.session.execute(statement)
        user = result.scalar()
        if user is None or not verify_password(password, user.password):
            return None
        return issue_access_token(user.name, str(user.id), self.role)  # role embedded

    async def get_entity(self, id: UUID) -> ModelT | None:
        return await self.get_by_id(self.model, id)

    async def logout_token(self, jti: str, exp: int | float) -> None:
        await blacklist_token_if_valid(jti, exp)
```

### Service Inheritance Chain

```
BaseService[ModelT, IdT]           — generic CRUD (add, get, update, delete)
    │
    └── AuthEntityService[ModelT]  — login (+ role embed), get_entity, logout_token
            │
            ├── SellerService(session, Seller, "seller")
            └── DeliveryPartnerService(session, DeliveryPartner, "delivery_partner")
```

Each concrete service passes its role identity to the base:

```python
class SellerService(AuthEntityService[Seller]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Seller, "seller")   # role="seller" embedded in token

class DeliveryPartnerService(AuthEntityService[DeliveryPartner]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DeliveryPartner, "delivery_partner")
```

---

## Lesson 9.5: `DeliveryPartner` Model & Service

```python
class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str = Field(min_length=8, max_length=72)
    serviceable_zip_code: list[int]     # Which zip codes they can deliver to
    max_handling_capacity: int           # Max active shipments at once

class DeliveryPartnerRead(BaseDeliveryPartner):
    serviceable_zip_code: list[int]
    max_handling_capacity: int
```

`serviceable_zip_code` is stored in PostgreSQL as an **ARRAY of integers**:
```python
serviceable_zip_code: list[int] = Field(sa_column=Column(ARRAY(INTEGER)))
```

This allows a single SQL query to find all partners who serve a given zip code using PostgreSQL's `ANY()` operator:
```python
DeliveryPartner.serviceable_zip_code.any(destination_zip_code)
```

---

## Lesson 9.6: Smart Partner Assignment in `ShipmentService`

The most complex piece — when a shipment is created, we automatically assign the **best available** delivery partner:

```python
async def _select_delivery_partner(self, destination_zip_code: int) -> DeliveryPartner:
    # Step 1: Find all partners who serve this zip code
    statement = select(DeliveryPartner).where(
        DeliveryPartner.serviceable_zip_code.any(destination_zip_code)
    )
    result = await self.session.execute(statement)
    serviceable_partners = result.scalars().all()

    if not serviceable_partners:
        raise NoDeliveryPartnerAvailableError("No delivery partner serves this destination")

    # Step 2: Count active shipments per partner (single DB query)
    active_loads = await self._get_active_load_by_partner(
        [partner.id for partner in serviceable_partners]
    )

    # Step 3: Filter to only partners with remaining capacity
    eligible_partners = []
    for partner in serviceable_partners:
        current_load = active_loads.get(partner.id, 0)
        if current_load < partner.max_handling_capacity:
            remaining_capacity = partner.max_handling_capacity - current_load
            eligible_partners.append((partner, remaining_capacity))

    if not eligible_partners:
        raise NoDeliveryPartnerAvailableError("No delivery partner has available handling capacity")

    # Step 4: Sort by most remaining capacity (tiebreak: oldest first, then UUID)
    eligible_partners.sort(key=lambda item: (-item[1], item[0].created_at, str(item[0].id)))
    return eligible_partners[0][0]
```

### The Active Load Query

```python
async def _get_active_load_by_partner(self, partner_ids: list[UUID]) -> dict[UUID, int]:
    active_statuses = [ShipmentStatus.PLACED, ShipmentStatus.IN_TRANSIT, ShipmentStatus.OUT_FOR_DELIVERY]
    
    statement = (
        select(Shipment.delivery_partner_id, func.count(Shipment.id))
        .where(
            Shipment.delivery_partner_id.in_(partner_ids),
            Shipment.status.in_(active_statuses),
        )
        .group_by(Shipment.delivery_partner_id)
    )
    result = await self.session.execute(statement)
    return {partner_id: total for partner_id, total in result.all() if partner_id}
```

This uses `GROUP BY` to count active shipments per partner in a **single database query** instead of N queries.

---

## Lesson 9.7: Eager Loading with `selectinload`

When fetching a shipment, we need the nested `seller` and `delivery_partner` objects:

```python
async def get(self, id: UUID) -> Shipment:
    stm = (
        select(Shipment)
        .options(
            selectinload(Shipment.seller),
            selectinload(Shipment.delivery_partner),
        )
        .where(Shipment.id == id)
    )
    result = await self.session.execute(stm)
    return result.scalar_one_or_none()
```

Without `selectinload`, accessing `shipment.seller` would trigger a **lazy load** — a synchronous DB call inside an async context, which raises `MissingGreenlet` errors. `selectinload` forces SQLAlchemy to fetch related objects upfront using a `SELECT ... WHERE id IN (...)` query.

!!! warning "Lazy loading is broken in async SQLAlchemy"
    In async contexts, **all related object access must be eager loaded** (e.g., `selectinload`, `joinedload`). Never access `instance.relationship_field` without pre-loading it.

---

## Lesson 9.8: Updated `ShipmentRead` Schema

```python
class ShipmentRead(BaseShipment):
    status: ShipmentStatus
    estimated_delivery: datetime
    seller: SellerRead                      # Nested seller info
    delivery_partner: DeliveryPartnerRead | None = None  # Optional — may not be assigned yet
```

The response now includes full nested objects:
```json
{
  "content": "Electronics",
  "weight": 2.5,
  "destination": 110001,
  "status": "placed",
  "estimated_delivery": "2026-06-10T...",
  "seller": {"name": "Alice", "email": "alice@example.com"},
  "delivery_partner": {
    "name": "FastDeliver Co",
    "email": "fd@example.com",
    "serviceable_zip_code": [110001, 110002],
    "max_handling_capacity": 50
  }
}
```

---

## Lesson 9.9: Role-Based Token Validation

With two actor types (Seller, DeliveryPartner), we can no longer use a single `PayloadDep`. The dependency system was refactored to be fully role-aware:

### Split OAuth2 Schemes

```python
# Each actor has its own scheme pointing to its own login URL
seller_oauth_scheme = OAuth2PasswordBearer(tokenUrl="/seller/login", auto_error=False)
partner_oauth_scheme = OAuth2PasswordBearer(tokenUrl="/partner/login", auto_error=False)

SellerOAuth2PasswordBearerDep = Annotated[str | None, Depends(seller_oauth_scheme)]
PartnerOAuth2PasswordBearerDep = Annotated[str | None, Depends(partner_oauth_scheme)]
```

This means Swagger/Scalar's Authorize UI shows **two separate login flows** — one for sellers, one for delivery partners.

### Role Validation in `_get_payload_from_token`

```python
async def _get_payload_from_token(token: str, expected_role: str):
    payload = get_payload(token)
    if payload is None:
        raise HTTPException(401, "Invalid or malformed token")

    role = payload.get("role")
    if role != expected_role:                    # Reject wrong-role tokens!
        raise HTTPException(401, "Token role mismatch")

    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise HTTPException(401, "Invalid or malformed token")

    if await is_jti_blacklisted(jti):
        raise HTTPException(401, "Invalid or malformed token")
    return payload

async def get_seller_payload_from_token(token: SellerTokenDep):
    return await _get_payload_from_token(token, "seller")

async def get_partner_payload_from_token(token: PartnerTokenDep):
    return await _get_payload_from_token(token, "delivery_partner")

SellerPayloadDep = Annotated[dict, Depends(get_seller_payload_from_token)]
PartnerPayloadDep = Annotated[dict, Depends(get_partner_payload_from_token)]
```

A delivery partner cannot use their token to call seller-only endpoints — the `role` check rejects it with `401 Token role mismatch`.

### Generic `_get_logged_in_entity` Helper

Instead of duplicating `get_logged_in_seller` and `get_logged_in_delivery_partner` (which were identical except for the service call and error message), a single generic helper is used:

```python
EntityT = TypeVar("EntityT")   # Used only in dependencies.py

def _get_uuid_from_payload(payload: dict) -> UUID:
    entity_id = payload.get("id")
    try:
        return UUID(str(entity_id))
    except (ValueError, TypeError):
        raise HTTPException(401, "Invalid or malformed token")

async def _get_logged_in_entity(
    payload: dict,
    entity_getter: Callable[[UUID], Awaitable[EntityT | None]],
    not_found_detail: str,
) -> EntityT:
    entity_uuid = _get_uuid_from_payload(payload)
    entity = await entity_getter(entity_uuid)
    if entity is None:
        raise HTTPException(401, not_found_detail)
    return entity

# Used by sellers
async def get_logged_in_seller(payload: SellerPayloadDep, service: SellerServiceDep):
    return await _get_logged_in_entity(payload, service.get_entity, "Seller account not found")

LoggedInSellerDep = Annotated[Seller, Depends(get_logged_in_seller)]

# Used by delivery partners
async def get_logged_in_delivery_partner(
    payload: PartnerPayloadDep, service: DeliveryPartnerServiceDep
):
    return await _get_logged_in_entity(payload, service.get_entity, "Delivery partner account not found")

LoggedInDeliveryPartnerDep = Annotated[DeliveryPartner, Depends(get_logged_in_delivery_partner)]
```

`Callable[[UUID], Awaitable[EntityT | None]]` is the type annotation for "an async function that takes a UUID and returns EntityT or None". This is Python's way of typing higher-order async functions.

---

## What You Learned

In this chapter, you:

- ✅ Used a **`User` non-table base class** to share fields across models
- ✅ Switched all PKs to **UUID** with `pg.UUID` + `default_factory=uuid4`
- ✅ Defined **SQLModel Relationships** (`back_populates`) for FK joins
- ✅ Stored a **PostgreSQL ARRAY** column (`ARRAY(INTEGER)`)
- ✅ Built a **`Generic` base service** (`BaseService[ModelT, IdT]`) eliminating repeated CRUD code
- ✅ Created **pure auth functions** in `auth_service.py` (hash, verify, issue token + role, blacklist)
- ✅ Embedded a **`role` claim** in every JWT — `"seller"` or `"delivery_partner"`
- ✅ Built an **`AuthEntityService[ModelT]`** generic mixin that stores its role and embeds it at login
- ✅ Implemented **smart delivery partner assignment** (zip-code `ANY()` → capacity check → sort)
- ✅ Used `func.count + GROUP BY` to count active loads in **one DB query**
- ✅ Used `selectinload` to eagerly load related objects in async SQLAlchemy
- ✅ Returned **nested response models** (`seller`, `delivery_partner` inside `ShipmentRead`)
- ✅ Split OAuth2 schemes per actor (`seller_oauth_scheme` / `partner_oauth_scheme`)
- ✅ Added **role validation** (`_get_payload_from_token(token, expected_role)`) — cross-actor tokens rejected with 401
- ✅ Used a **generic `_get_logged_in_entity` helper** (`Callable[[UUID], Awaitable[T]]`) to eliminate duplicated auth logic
- ✅ Separated UUID parsing into `_get_uuid_from_payload` for clean reuse

## Next Steps

With the data model, relationships, and role-based auth fully in place, next up is **testing** with Pytest and FastAPI's `TestClient`, and **Docker Compose** to orchestrate PostgreSQL + Redis + the app together.
