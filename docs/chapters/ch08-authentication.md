# Chapter 8: Authentication — Sellers, JWT & OAuth2

Up to now, anyone can call our API and create or delete shipments. In this chapter, we add a complete authentication system: sellers can register, log in to receive a JWT token, use that token to access protected endpoints, and log out to invalidate the token.

!!! note "What Changed"
    ```
    app/
    ├── main.py                         (renamed from app.py)
    ├── dependencies.py                 NEW — all DI deps centralised here
    ├── utils.py                        NEW — JWT create/decode helpers
    ├── api/
    │   ├── router/
    │   │   ├── __init__.py             NEW — combines routers into app_router
    │   │   ├── seller_router.py        NEW — /seller/signup, /login, /logout
    │   │   └── shipment_router.py      Updated — POST/PATCH/DELETE now require auth
    │   └── schema/
    │       ├── seller_schema.py        NEW — SellerCreate, SellerRead, TokenResponse
    │       └── shipment_schema.py      (unchanged)
    ├── database/
    │   ├── config.py                   Updated — added JWT_TOKEN, JWT_ALGO, Redis vars
    │   ├── models.py                   Updated — added Seller table
    │   ├── redis.py                    NEW — async Redis client for token blacklist
    │   └── session.py                  Updated — SellerServiceDep added
    └── services/
        ├── seller_service.py           NEW — signup, login (bcrypt), logout (JTI blacklist)
        └── shipment_service.py         Updated — update() now uses ShipmentUpdate model
    ```

---

## Lesson 8.1: The Seller Model & Schema

### Database Model (`database/models.py`)

```python
from pydantic import EmailStr
from sqlmodel import SQLModel, Field

class Seller(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    email: EmailStr      # Validates email format via Pydantic
    password: str        # Stored as bcrypt hash — NEVER store plaintext!
```

### API Schema (`api/schema/seller_schema.py`)

```python
from pydantic import BaseModel, EmailStr, Field

class BaseSeller(BaseModel):
    name: str
    email: EmailStr

class SellerCreate(BaseSeller):
    password: str = Field(min_length=8, max_length=72)  # 72 = bcrypt max

class SellerRead(BaseSeller):
    pass  # Inherits name and email — password is intentionally excluded!

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

!!! important "Never return passwords"
    `SellerRead` deliberately does not include the `password` field. Even though the password is hashed, returning it in API responses is unnecessary and a security risk. The `SellerCreate` → `SellerRead` schema split enforces this separation.

---

## Lesson 8.2: Password Hashing with bcrypt (`services/seller_service.py`)

Passwords must **never** be stored as plaintext. We use `passlib` with bcrypt:

```python
from passlib.context import CryptContext

ctx = CryptContext(schemes=["bcrypt"])

class SellerService:
    async def add(self, seller: SellerCreate) -> Seller:
        seller_db = Seller(
            **seller.model_dump(exclude=["password"]),  # Don't spread plaintext pw
            password=ctx.hash(seller.password),          # Store the hash instead
        )
        self.session.add(seller_db)
        await self.session.commit()
        await self.session.refresh(seller_db)
        return seller_db
```

`ctx.hash("my_password")` produces a string like:
```
$2b$12$hj29FQAGTdwPqMPsFi8MFez3Kzr2i5KyGa3FV5...
```

This hash is:
- **Irreversible** — you cannot decrypt it back to the original password
- **Salted** — two users with the same password get different hashes
- **Slow by design** — bcrypt is deliberately slow to make brute-force attacks expensive

---

## Lesson 8.3: JWT Tokens (`utils.py`)

JSON Web Tokens (JWTs) are used to prove identity without hitting the database on every request.

```python
import jwt
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from app.database.config import config

def get_token(data: dict, exp: timedelta = timedelta(days=1)) -> str:
    return jwt.encode(
        payload={
            **data,
            "jti": str(uuid4()),                           # Unique token ID
            "exp": datetime.now(timezone.utc) + exp,       # Expiry timestamp
        },
        key=config.JWT_TOKEN,
        algorithm=config.JWT_ALGO,
    )

def get_payload(token: str) -> dict | None:
    try:
        return jwt.decode(jwt=token, key=config.JWT_TOKEN, algorithms=[config.JWT_ALGO])
    except jwt.PyJWTError:
        return None    # Expired, tampered, or invalid token
```

### JWT Structure

A JWT is three base64-encoded sections separated by dots:
```
eyJhbGciOiJIUzI1NiJ9.eyJuYW1lIjoiQWxpY2UiLCJpZCI6MX0.abc123
     HEADER                      PAYLOAD                  SIGNATURE
```

| Claim | Key | Value |
|-------|-----|-------|
| Seller name | `name` | `"Alice"` |
| Seller ID | `id` | `1` |
| JWT ID | `jti` | `"a9f7c..."` (UUID) |
| Expiry | `exp` | Unix timestamp |

The **`jti` (JWT ID)** is a UUID added to every token so we can individually blacklist tokens on logout.

---

## Lesson 8.4: Redis Token Blacklist (`database/redis.py`)

When a user logs out, we can't "delete" the JWT (it's stateless). Instead, we store its `jti` in Redis with the same TTL as the token's remaining lifetime:

```python
from redis.asyncio import Redis
from app.database.config import config

_redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    username=config.REDIS_USER,
    password=config.REDIS_PASSWORD,
    decode_responses=True,      # Return strings, not bytes
)

async def add_jti_to_blacklist(jti: str, ex: int):
    await _redis_client.set(jti, "blacklisted", ex=ex)  # auto-expires with token

async def is_jti_blacklisted(jti: str) -> bool:
    return await _redis_client.exists(jti)
```

**Logout logic in `SellerService`:**
```python
async def logout(self, jti: str, exp: int):
    # Calculate remaining seconds until token expires
    ex = exp - int(datetime.now(timezone.utc).timestamp())
    await add_jti_to_blacklist(jti, ex)
```

The Redis key auto-expires when the token would have expired — no cleanup needed!

---

## Lesson 8.5: The Dependency Chain (`dependencies.py`)

All authentication dependencies now live in `app/dependencies.py` — separate from session/service setup:

```python
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# 1. Extract Bearer token from Authorization header
oauth_scheme = OAuth2PasswordBearer(tokenUrl="/seller/login", auto_error=False)
OAuth2PasswordBearerDep = Annotated[str | None, Depends(oauth_scheme)]

# 2. Validate token is present
def get_token(token: OAuth2PasswordBearerDep):
    if not token:
        raise HTTPException(401, detail="Missing access token")
    return token

TokenDep = Annotated[str, Depends(get_token)]

# 3. Decode token AND check Redis blacklist
async def get_payload_from_token(token: TokenDep):
    payload = get_payload(token)                           # Decode JWT
    if payload is None or await is_jti_blacklisted(payload["jti"]):
        raise HTTPException(401, detail="Invalid or malformed token")
    return payload

PayloadDep = Annotated[dict, Depends(get_payload_from_token)]

# 4. Load the actual Seller from DB
async def get_logged_in_seller(payload: PayloadDep, service: SellerServiceDep):
    seller = await service.get_seller(payload["id"])
    if seller is None:
        raise HTTPException(401, detail="Seller account not found")
    return seller

LoggedInSellerDep = Annotated[Seller, Depends(get_logged_in_seller)]
```

### The Full Auth Chain

```
HTTP Request with: Authorization: Bearer <token>
         │
         ▼
oauth_scheme          → extracts raw token string
         │
         ▼
get_token()           → ensures token exists (401 if missing)
         │
         ▼
get_payload_from_token() → decodes JWT + checks Redis blacklist
         │
         ▼
get_logged_in_seller()   → loads Seller from DB by payload["id"]
         │
         ▼
Endpoint receives: seller: Seller  ← fully authenticated user
```

---

## Lesson 8.6: Seller Router (`api/router/seller_router.py`)

```python
seller_router = APIRouter(prefix="/seller", tags=["Seller"])

# POST /seller/signup
@seller_router.post("/signup", response_model=SellerRead)
async def create_seller(seller: SellerCreate, service: SellerServiceDep):
    return await service.add(seller)

# POST /seller/login  ← OAuth2 standard uses form data, not JSON!
@seller_router.post("/login", response_model=TokenResponse)
async def login(request: OAuth2PasswordRequestFormDep, service: SellerServiceDep):
    token = await service.login(request.username, request.password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": token, "token_type": "bearer"}

# GET /seller/logout
@seller_router.get("/logout")
async def logout(payload: PayloadDep, service: SellerServiceDep):
    await service.logout(payload["jti"], payload["exp"])
    return {"detail": "Logged out successfully"}
```

!!! tip "OAuth2PasswordRequestForm sends form data"
    The `/login` endpoint uses `OAuth2PasswordRequestForm` — this expects the request body as **form data** (not JSON), with fields `username` and `password`. This is the OAuth2 standard used by Swagger/Scalar's "Authorize" button. We're using `email` as `username` here.

---

## Lesson 8.7: Protected Shipment Endpoints

POST, PATCH, and DELETE shipment operations now require authentication. The `_: LoggedInSellerDep` parameter does all the work — if the token is invalid or missing, FastAPI returns 401 before your function body even runs:

```python
@shipment_router.post("/", response_model=None)
async def submit_shipment(
    _: LoggedInSellerDep,       # Auth check — underscore = "we need it but don't use it"
    req_body: ShipmentCreate,
    service: ShipmentServiceDep
):
    id = await service.add(req_body)
    return {"id": id}
```

The `_` naming convention signals that the dependency is only for its side effect (authentication), not for data its value provides.

---

## Lesson 8.8: Updated Config & Router Registration

### `config.py` — Added JWT & Redis vars
```python
class Setting(BaseSettings):
    # PostgreSQL (unchanged)
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    # Redis (new)
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_USER: str
    REDIS_PASSWORD: str
    # JWT (new)
    JWT_TOKEN: str    # Secret key for signing tokens
    JWT_ALGO: str     # e.g., "HS256"
```

### `api/router/__init__.py` — Master router
```python
from fastapi import APIRouter
from app.api.router.shipment_router import shipment_router
from app.api.router.seller_router import seller_router

app_router = APIRouter()
app_router.include_router(shipment_router)
app_router.include_router(seller_router)
```

### `main.py` — Thin as ever
```python
app.include_router(app_router)   # One line to include everything
```

---

## 🏋️ Try It Yourself

```bash
uvicorn app.main:app --reload
```

1. **Signup**: `POST /seller/signup` with `{"name": "Alice", "email": "alice@test.com", "password": "secret123"}`
2. **Login**: `POST /seller/login` with form data `username=alice@test.com&password=secret123`. Copy the `access_token`.
3. **Create shipment**: `POST /shipment/` with `Authorization: Bearer <token>` header.
4. **Logout**: `GET /seller/logout` with the token. The `jti` is blacklisted in Redis.
5. **Try again**: Use the same token for another request — get `401 Invalid or malformed token`.

---

## What You Learned

In this chapter, you:

- ✅ Created a **`Seller` database model** with hashed password storage
- ✅ Used **`passlib` / bcrypt** for secure password hashing and verification
- ✅ Built **JWT tokens** with `jti` (unique ID) and expiry claims
- ✅ Used **Redis** as a token blacklist for stateless logout
- ✅ Built a **multi-step DI auth chain**: token → payload → seller
- ✅ Used `OAuth2PasswordBearer` and `OAuth2PasswordRequestForm` for standard OAuth2
- ✅ Protected endpoints with `_: LoggedInSellerDep` as a side-effect dependency
- ✅ Centralised all DI in `dependencies.py` and all routers in `api/router/__init__.py`

## Next Steps

The API now has full authentication! The next chapter goes much further — adding a `DeliveryPartner` actor, switching all IDs to **UUID**, building database **Relationships**, and refactoring the service layer with **Python Generics** and smart partner assignment.

**[Chapter 9: Relationships & Generics →](ch09-relationships-generics.md)**

