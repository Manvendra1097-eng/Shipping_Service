# Service Layer & Repository Pattern

As business logic grows, it's tempting to put everything inside endpoint functions. This works for prototypes but breaks down quickly — endpoints become long, business rules get duplicated, and testing becomes painful.

The **Service Layer** pattern separates your concerns into distinct responsibilities:

```
HTTP Layer    │  endpoint receives request, validates it, returns response
Service Layer │  business rules (what the app DOES)
Data Layer    │  database queries (how data is stored/retrieved)
```

---

## The Problem Without a Service Layer

```python
# ❌ Everything crammed into an endpoint
@app.post("/shipment")
async def create_shipment(req_body: ShipmentCreate, session: AsyncSession):
    # Business logic in the endpoint 👎
    shipment = Shipment(
        **req_body.model_dump(),
        status=ShipmentStatus.PLACED,
        estimated_delivery=datetime.now() + timedelta(days=3),
    )
    session.add(shipment)
    await session.commit()
    await session.refresh(shipment)
    
    # What if we need the same logic in a background task?
    # We'd have to copy-paste this whole block. 
    return {"id": shipment.id}
```

---

## The Service Class Pattern

```python
# services/shipment_service.py
class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session   # Injected by FastAPI's DI system

    async def add(self, shipment_create: ShipmentCreate) -> int:
        # All business logic lives HERE
        shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.PLACED,
            estimated_delivery=datetime.now() + timedelta(days=3),
        )
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment.id
```

```python
# api/router.py — endpoint becomes trivial
@shipment_router.post("/")
async def submit_shipment(req_body: ShipmentCreate, service: ShipmentServiceDep):
    id = await service.add(req_body)   # ← One line!
    return {"id": id}
```

---

## Injecting the Service via FastAPI DI

The service is wired through a dependency chain in `session.py`:

```python
# 1. Session dependency
async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# 2. Service depends on session
async def get_shipment_service(session: SessionDep) -> ShipmentService:
    return ShipmentService(session)

ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]
```

FastAPI resolves this automatically. When an endpoint declares `service: ShipmentServiceDep`, FastAPI:
1. Creates a session via `get_session()`
2. Passes it to `get_shipment_service()`
3. Passes the `ShipmentService` instance to your endpoint function

---

## Benefits

| Concern | Where it lives |
|---------|---------------|
| HTTP validation | Endpoint + Pydantic schema |
| Business rules | Service class |
| Database queries | Service class (via session) |
| Configuration | `config.py` |

### Testing becomes easy

```python
# Mock the service in tests — no database needed!
def test_create_shipment():
    mock_service = MagicMock(spec=ShipmentService)
    mock_service.add.return_value = 12703
    
    app.dependency_overrides[get_shipment_service] = lambda: mock_service
    
    response = client.post("/shipment/", json={"content": "Box", "weight": 1.0})
    assert response.json() == {"id": 12703}
```

### Reusability

The same service can be used by:
- HTTP endpoints
- Background tasks
- WebSocket handlers
- CLI scripts

---

## Service vs Repository

| | Service | Repository |
|-|---------|------------|
| **Responsibility** | Business rules (e.g., set status, compute delivery date) | Pure data access (get, save, delete) |
| **Knows about** | Domain concepts, rules | Database only |
| **Example** | `ShipmentService.add()` sets the status to PLACED | `ShipmentRepository.save(shipment)` |

For small projects, combining both into a single `Service` class is fine. As the project grows, you might split them.

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| Service class | Holds business logic, receives session via constructor |
| DI chain | `session → service → endpoint` wired by FastAPI automatically |
| Thin endpoints | Endpoints delegate to service, stay 1-3 lines |
| Testability | Mock the service to test endpoints without a database |

---

**[← Back to Home](../index.md)**
