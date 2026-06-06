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
  "id": 1,
  "jti": "a9f7c3b2-...",
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

Our implementation uses `id`, `name`, `jti`, and `exp`.

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

## Key Takeaways

| Concept | Summary |
|---------|---------|
| JWT | Signed token carrying claims — no DB lookup to verify |
| `jti` | Unique token ID enabling per-token invalidation |
| `exp` | Expiry — always set an expiry on tokens |
| `OAuth2PasswordBearer` | FastAPI utility to extract Bearer token from headers |
| `OAuth2PasswordRequestForm` | Standard form-data login (username + password) |
| bcrypt | Secure one-way password hashing with `passlib` |
| Redis JTI blacklist | Stateless logout — blacklist token's `jti` until it expires |
| `_: Dep` in endpoint | Dependency used only for its side-effects (auth gate) |

---

**[← Back to Home](../index.md)**
