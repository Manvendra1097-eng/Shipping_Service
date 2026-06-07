# JWT & OAuth2 Authentication

Almost every real API needs to know *who* is making a request and *whether* they're allowed to. FastAPI has first-class support for the OAuth2 standard and makes JWT-based authentication straightforward to implement.

---

## The Problem: Stateless APIs

HTTP is stateless — each request is independent. Without authentication, the server has no idea which user is calling it.

**Session-based auth** (old approach): Server stores a session in memory or a database. Every request hits the database to look up the session. Doesn't scale horizontally.

**JWT-based auth** (modern approach): The server issues a cryptographically signed token. The client sends it with every request. The server verifies the signature — **no database lookup needed**.

---

## What is JWT?

A JSON Web Token (JWT) is a compact, URL-safe string with three dot-separated parts:

```
eyJhbGciOiJIUzI1NiJ9  .  eyJuYW1lIjoiQWxpY2UiLCJpZCI6MX0  .  SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
       HEADER                          PAYLOAD                              SIGNATURE
```

Each part is Base64URL-encoded (not encrypted — just encoded):

**Header**: Algorithm used (`HS256`, `RS256`, etc.)
```json
{"alg": "HS256", "typ": "JWT"}
```

**Payload**: Claims (data about the user + metadata):
```json
{
  "name": "Alice",
  "id": "a9f7c3b2-...",
  "role": "seller",
  "jti": "b3e2d1a0-...",
  "exp": 1717600000
}
```

**Signature**: `HMAC-SHA256(base64(header) + "." + base64(payload), SECRET_KEY)`

!!! warning "JWTs are encoded, not encrypted"
    Anyone can decode the payload with `base64.decode()`. **Never put sensitive data** (passwords, credit cards) in a JWT payload. The signature only proves the token hasn't been tampered with — it doesn't hide the content.

---

## Standard JWT Claims

| Claim | Meaning |
|-------|---------|
| `sub` | Subject — who the token is about (usually user ID) |
| `exp` | Expiry — Unix timestamp after which token is invalid |
| `iat` | Issued at — when the token was created |
| `jti` | JWT ID — unique identifier for this specific token |
| `iss` | Issuer — who created the token |

Our implementation uses `id`, `name`, `role`, `jti`, and `exp`.

---

## Creating & Verifying Tokens

```python
import jwt
from uuid import uuid4
from datetime import datetime, timedelta, timezone

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Create a token
def get_token(data: dict, exp: timedelta = timedelta(days=1)) -> str:
    return jwt.encode(
        payload={
            **data,
            "jti": str(uuid4()),
            "exp": datetime.now(timezone.utc) + exp,
        },
        key=SECRET_KEY,
        algorithm=ALGORITHM,
    )

# Verify and decode a token
def get_payload(token: str) -> dict | None:
    try:
        return jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None  # Expired, invalid signature, or malformed
```

`jwt.PyJWTError` catches all JWT errors: `ExpiredSignatureError`, `InvalidSignatureError`, `DecodeError`, etc.

---

## OAuth2 in FastAPI

OAuth2 is a standard protocol for authorization. FastAPI provides two key utilities:

### `OAuth2PasswordBearer`

Extracts the `Bearer` token from the `Authorization` header:

```python
from fastapi.security import OAuth2PasswordBearer

oauth_scheme = OAuth2PasswordBearer(
    tokenUrl="/seller/login",   # Where to get a token (shown in Scalar/Swagger UI)
    auto_error=False            # Return None instead of 401 if no token — lets us give custom error
)
```

When an endpoint depends on this, FastAPI:
1. Reads the `Authorization: Bearer <token>` header
2. Extracts the raw token string
3. Passes it to your dependency function

### `OAuth2PasswordRequestForm`

Provides the standard login form fields (`username`, `password`):

```python
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

OAuth2PasswordRequestFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]

@router.post("/login")
async def login(request: OAuth2PasswordRequestFormDep):
    email = request.username    # OAuth2 spec calls it "username"
    password = request.password
```

!!! important "Form data, not JSON"
    `OAuth2PasswordRequestForm` expects `application/x-www-form-urlencoded` (form data), not JSON. This is the OAuth2 standard. The Scalar/Swagger "Authorize" button uses this format automatically.

---

## The Full Auth Dependency Chain

```python
# Step 1: Extract token (returns None if missing)
oauth_scheme = OAuth2PasswordBearer(tokenUrl="/seller/login", auto_error=False)

# Step 2: Require token (raise 401 if None)
def get_token(token: Annotated[str | None, Depends(oauth_scheme)]):
    if not token:
        raise HTTPException(401, "Missing access token")
    return token

# Step 3: Decode + blacklist check
async def get_payload(token: Annotated[str, Depends(get_token)]):
    payload = decode_jwt(token)
    if payload is None or await is_blacklisted(payload["jti"]):
        raise HTTPException(401, "Invalid or malformed token")
    return payload

# Step 4: Load user
async def get_current_user(payload: Annotated[dict, Depends(get_payload)]):
    user = await db.get_user(payload["id"])
    if user is None:
        raise HTTPException(401, "User not found")
    return user

# Usage in endpoint
@router.get("/protected")
async def protected(user: Annotated[User, Depends(get_current_user)]):
    return {"message": f"Hello, {user.name}"}
```

FastAPI resolves this entire chain automatically for every request.

---

## Token Blacklisting with JTI

JWTs can't be "deleted" — they're valid until they expire. To support **logout**, you track which tokens have been explicitly invalidated using the `jti` claim.

```
Login  → Issue token with jti="abc-123", exp=tomorrow
Logout → Store "abc-123" in Redis with TTL = remaining token lifetime
Next request with same token → Redis.exists("abc-123") → True → 401
Token expires naturally → Redis key auto-deletes → no cleanup needed
```

This gives you stateless logout with no permanent database growth.

---

## Password Hashing with bcrypt

Passwords must never be stored as plaintext. bcrypt is the standard for password hashing:

```python
from passlib.context import CryptContext

ctx = CryptContext(schemes=["bcrypt"])

# Hashing (on signup)
hashed = ctx.hash("my_password")
# "$2b$12$hj29FQAGTdwPqMPsFi8MFezKzr2i5KyGa..."

# Verification (on login)
is_valid = ctx.verify("my_password", hashed)  # True
is_valid = ctx.verify("wrong_pass", hashed)   # False
```

bcrypt is:
- **One-way** — cannot decrypt back to original
- **Salted** — same password → different hash every time
- **Slow** — cost factor makes brute-force expensive (adjustable)
- **Limited to 72 chars** — passwords > 72 chars are truncated by bcrypt

---

## Role-Based Auth with Multiple Actor Types

When your API has multiple actor types (e.g., Seller and DeliveryPartner), a single shared `PayloadDep` is no longer safe — a delivery partner could use their token on a seller endpoint. The solution is to embed a **role** in the token and validate it.

### Embed role at token creation

```python
def issue_access_token(name: str, user_id: str, role: str) -> str:
    return get_token(data={"name": name, "id": user_id, "role": role})

# SellerService passes "seller"
token = issue_access_token(user.name, str(user.id), "seller")

# DeliveryPartnerService passes "delivery_partner"
token = issue_access_token(user.name, str(user.id), "delivery_partner")
```

### Validate role at token decode

```python
async def _get_payload_from_token(token: str, expected_role: str):
    payload = get_payload(token)
    if payload is None:
        raise HTTPException(401, "Invalid or malformed token")

    if payload.get("role") != expected_role:      # Key check!
        raise HTTPException(401, "Token role mismatch")
    ...
    return payload

# Role-specific payload deps
SellerPayloadDep  = Annotated[dict, Depends(lambda t: _get_payload_from_token(t, "seller"))]
PartnerPayloadDep = Annotated[dict, Depends(lambda t: _get_payload_from_token(t, "delivery_partner"))]
```

### Split OAuth2 schemes per actor

```python
seller_oauth_scheme = OAuth2PasswordBearer(tokenUrl="/seller/login", auto_error=False)
partner_oauth_scheme = OAuth2PasswordBearer(tokenUrl="/partner/login", auto_error=False)
```

Scalar/Swagger shows separate Authorize buttons for each, and the `tokenUrl` tells the UI where to exchange credentials for a token.

### Higher-order async function type hint

The `_get_logged_in_entity` helper accepts a callable that fetches an entity by UUID:

```python
from typing import Callable, Awaitable

async def _get_logged_in_entity(
    payload: dict,
    entity_getter: Callable[[UUID], Awaitable[EntityT | None]],   # "async fn(UUID) -> T"
    not_found_detail: str,
) -> EntityT:
    uuid = _get_uuid_from_payload(payload)
    entity = await entity_getter(uuid)
    if entity is None:
        raise HTTPException(401, not_found_detail)
    return entity
```

`Callable[[UUID], Awaitable[T | None]]` reads as: *a callable that takes a UUID and returns an awaitable that resolves to T or None*. This is the standard way to type async callback functions in Python.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| JWT | Signed token carrying claims — no DB lookup to verify |
| `role` claim | Custom claim identifying the actor type (`"seller"`, `"delivery_partner"`) |
| `jti` | Unique token ID enabling per-token invalidation |
| `exp` | Expiry — always set an expiry on tokens |
| `OAuth2PasswordBearer` | FastAPI utility to extract Bearer token from headers |
| Split schemes | One `OAuth2PasswordBearer` per actor, each with its own `tokenUrl` |
| `OAuth2PasswordRequestForm` | Standard form-data login (username + password) |
| Role validation | Check `payload["role"] == expected_role` — reject mismatched tokens |
| bcrypt | Secure one-way password hashing with `passlib` |
| Redis JTI blacklist | Stateless logout — blacklist token's `jti` until it expires |
| `Callable[[UUID], Awaitable[T]]` | Type hint for higher-order async callbacks |
| `_: Dep` in endpoint | Dependency used only for its side-effects (auth gate) |

---

**[← Back to Home](../index.md)**
