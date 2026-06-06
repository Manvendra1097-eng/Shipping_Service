# Redis — Fast In-Memory Data Store

Redis ("Remote Dictionary Server") is an in-memory key-value store used for caching, session storage, pub/sub messaging, rate limiting, and more. In our application, we use it as a **JWT token blacklist** — storing the `jti` of logged-out tokens so they can't be reused.

---

## Why Redis for a Token Blacklist?

| Option | Problem |
|--------|---------|
| Store in PostgreSQL | Too slow — DB query on every request |
| Store in Python dict | Lost on server restart, doesn't work across multiple workers |
| Store in Redis | Fast in-memory lookup, automatic TTL expiry, works across workers |

Redis fits perfectly because:
1. It's **extremely fast** — microsecond read/write
2. It supports **TTL (time-to-live)** — keys auto-delete after a set time
3. It's **shared** across all app instances/workers

---

## Async Redis Client

```python
from redis.asyncio import Redis
from app.database.config import config

_redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    username=config.REDIS_USER,
    password=config.REDIS_PASSWORD,
    decode_responses=True,     # Returns str, not bytes
)
```

We use `redis.asyncio` (not the standard `redis`) to get a non-blocking client compatible with FastAPI's async event loop. With `decode_responses=True`, keys and values are automatically decoded to Python strings.

---

## Token Blacklist Operations

### Adding to Blacklist (on logout)

```python
async def add_jti_to_blacklist(jti: str, ex: int):
    await _redis_client.set(jti, "blacklisted", ex=ex)
```

`ex=ex` sets the key's TTL in seconds. When the token would naturally expire, Redis automatically deletes the key — no cleanup job needed.

### Checking the Blacklist (on every protected request)

```python
async def is_jti_blacklisted(jti: str) -> bool:
    return await _redis_client.exists(jti)
```

`exists()` returns `1` if the key exists, `0` if not. This is a single O(1) Redis lookup — extremely fast.

### How Logout Uses It

```python
# In SellerService
async def logout(self, jti: str, exp: int):
    # Calculate remaining seconds until token expiry
    ex = exp - int(datetime.now(timezone.utc).timestamp())
    await add_jti_to_blacklist(jti, ex)
```

The TTL is set to exactly how many seconds remain on the token. Once the token would have expired anyway, the Redis key is also gone — no permanent storage growth.

---

## Redis Data Structures

Redis supports several data types, though we're only using strings here:

| Type | Command | Use case |
|------|---------|----------|
| **String** | `SET key value EX 60` | Token blacklist, simple caching |
| **Hash** | `HSET key field value` | Store object fields (like a dict) |
| **List** | `LPUSH key value` | Queues, activity feeds |
| **Set** | `SADD key member` | Unique collections, tags |
| **Sorted Set** | `ZADD key score member` | Leaderboards, rate limiting |
| **Pub/Sub** | `PUBLISH / SUBSCRIBE` | Real-time notifications |

---

## TTL (Time-To-Live)

TTL is one of Redis's most powerful features for ephemeral data:

```python
# Set a key with a TTL
await client.set("session:abc", "data", ex=3600)   # Expires in 1 hour

# Check remaining TTL
ttl = await client.ttl("session:abc")   # Returns seconds remaining, -1 if no TTL

# Manually delete
await client.delete("session:abc")
```

---

## Caching with Redis (Future Use)

Beyond the blacklist, Redis is commonly used for response caching:

```python
import json

async def get_shipment_cached(id: int):
    cache_key = f"shipment:{id}"
    
    # Check cache first
    cached = await client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Cache miss — fetch from DB
    shipment = await db.get(Shipment, id)
    await client.set(cache_key, json.dumps(shipment.model_dump()), ex=300)  # 5 min TTL
    return shipment
```

This pattern (cache-aside) can reduce database load dramatically for read-heavy endpoints.

---

## Setting Up Redis

**Docker (recommended for development):**
```bash
docker run --name fastship-redis \
  -p 6379:6379 \
  -d redis:7 \
  redis-server --requirepass "your_password"
```

**`.env` configuration:**
```ini
REDIS_HOST = localhost
REDIS_PORT = 6379
REDIS_USER = default
REDIS_PASSWORD = your_password
```

**Install the async client:**
```bash
pip install redis[asyncio]
```

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| `redis.asyncio.Redis` | Non-blocking Redis client for FastAPI |
| `decode_responses=True` | Returns Python strings, not bytes |
| `SET key value EX seconds` | Store with automatic expiry |
| `EXISTS key` | O(1) check — returns 1/0 |
| JTI blacklist pattern | Store `jti`, TTL = remaining token lifetime |
| Cache-aside | Check Redis first, fall back to DB, then cache result |

---

**[← Back to Home](../index.md)**
