# Learn FastAPI — A Hands-On Tutorial

Welcome! This is a **progressive tutorial guide** for learning [FastAPI](https://fastapi.tiangolo.com/) — one of the fastest-growing Python web frameworks. You'll learn by building and extending a real **Shipping API** step by step.

!!! info "Course Companion"
    This guide follows the structure of [**"Ultimate Guide to FastAPI and Backend Development"**](https://www.udemy.com/) (Build REST APIs For The Modern Web) by Rahul Mula. It serves as your personal notes, reference, and code companion as you progress through the course.

## Why FastAPI?

FastAPI is a modern, high-performance Python web framework built on top of standard Python type hints. Here's why developers love it:

- ⚡ **Blazing fast** — On par with Node.js and Go, thanks to async support
- 🧩 **Type-safe** — Leverages Python type hints for automatic validation
- 📖 **Auto-documented** — Generates interactive API docs from your code
- 🐍 **Pythonic** — If you know Python, you already know most of FastAPI

## Tech Stack (What You'll Learn)

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Web framework for building REST APIs |
| **SQLModel** | Database ORM — combines SQLAlchemy + Pydantic (by the same author as FastAPI) |
| **OAuth2 + JWT** | Authentication & authorization |
| **Pytest** | Testing framework |
| **React** | Frontend integration |
| **Docker** | Containerization & deployment |

## How to Use This Guide

This guide is organized as **numbered chapters**. Each chapter builds on the previous one, teaching a new concept using the actual code in the `app/` folder.

!!! tip "Progressive Learning"
    New chapters will be added as you progress through the course. Chapters marked 🔜 are planned but not yet written.

## Tutorial Chapters

### Part 1 & 2: Foundations & Data Modeling ✅

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| [Chapter 1](chapters/ch01-getting-started.md) | Getting Started | Project setup, virtual environments, running your first server |
| [Chapter 2](chapters/ch02-building-endpoints.md) | Building Endpoints | GET routes, path parameters, in-memory data, error handling |
| [Chapter 3](chapters/ch03-under-the-hood.md) | Under the Hood | Request lifecycle, ASGI, type hints, OpenAPI schema |
| [Chapter 4](chapters/ch04-pydantic-models.md) | Pydantic Models | Request/response schemas, data validation, serialization |
| [Chapter 5](chapters/ch05-sqlite.md) | SQLite (Raw SQL) | Persist data with raw `sqlite3`, custom DB class — stepping stone |
| [Chapter 6](chapters/ch06-sqlmodel.md) | SQLModel | Tables as Python classes, session dependency, lifespan, CRUD with ORM |
| [Chapter 7](chapters/ch07-postgres-async.md) | PostgreSQL & Async | Async engine, asyncpg, pydantic-settings, APIRouter, Service layer |
| [Chapter 8](chapters/ch08-authentication.md) | Authentication | Sellers, bcrypt, JWT tokens, OAuth2, Redis token blacklist |
| [Chapter 9](chapters/ch09-relationships-generics.md) | Relationships & Generics | UUID PKs, ORM relationships, BaseService[T], smart partner assignment |

### Part 3: Testing & Deployment 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 10 | Pytest & TestClient | Unit tests, dependency overrides, test databases |
| Chapter 11 | Docker & Deployment | Containerise the app, Docker Compose, production config |

### Part 4: Authentication & Security 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 9 | OAuth2 & JWT | Login/logout, JWT tokens, password hashing |
| Chapter 10 | Protecting Endpoints | Dependency injection for auth, role-based access |

### Part 5: Advanced Backend 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 11 | Async & Background Tasks | `async/await`, background jobs (e.g., email notifications) |
| Chapter 12 | Error Handling & Middleware | Custom exceptions, CORS, request/response hooks |
| Chapter 13 | Dependency Injection | Cleaner code with FastAPI's DI system |

### Part 6: Testing 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 14 | Pytest Basics | Unit tests, test structure, assertions |
| Chapter 15 | Testing FastAPI | TestClient, dependency overrides, test databases |

### Part 7: Frontend & Deployment 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 16 | React Integration | Connecting a React frontend to your FastAPI backend |
| Chapter 17 | Docker | Containerize the app, Docker Compose, multi-service setup |
| Chapter 18 | Deployment | Production config, cloud deployment best practices |

## Concept Deep-Dives

These are standalone pages that explore Python/FastAPI concepts in detail:

- 🎯 [Python Decorators](concepts/decorator.md) — The magic behind `@app.get()`
- 🔀 [Path & Query Parameters](concepts/path_and_query_parameter.md) — Two ways to pass data to your API
- 🛡️ [Data Validation (Pydantic)](concepts/pydantic.md) — Type-safe request/response models
- 📋 [Enumerations (Enums)](concepts/enum.md) — Restricting fields to predefined values
- 🗄️ [SQLModel & ORMs](concepts/sqlmodel.md) — Database tables as Python classes
- ⚡ [Async & Concurrency](concepts/async_concurrency.md) — Event loop, async/await, asyncio, def vs async def
- 🛣️ [APIRouter](concepts/api_router.md) — Split endpoints into modular routers
- 🏗️ [Service Layer Pattern](concepts/service_layer.md) — Separate business logic from endpoints
- ⚙️ [Config with pydantic-settings](concepts/pydantic_settings.md) — Manage secrets and env variables safely
- 🔐 [JWT & OAuth2](concepts/jwt_oauth2.md) — Tokens, bcrypt, OAuth2 flows, JTI blacklisting
- ⚡ [Redis](concepts/redis.md) — In-memory store for caching and token blacklists
- 🧬 [Python Generics](concepts/generics.md) — TypeVar, Generic[T], type-safe reusable base classes
- 🔗 [SQLModel Relationships](concepts/relationships.md) — FK columns, Relationship(), selectinload, eager loading

## Project Structure

Here is the actual layout of this project:

```
learn_fastapi/
├── .env
├── app/
│   ├── main.py                   # FastAPI entry point + lifespan
│   ├── dependencies.py           # All DI: service deps + full auth chain
│   ├── utils.py                  # JWT create/decode helpers
│   ├── api/
│   │   ├── router/
│   │   │   ├── __init__.py       # app_router combines all sub-routers
│   │   │   ├── shipment_router.py
│   │   │   ├── seller_router.py
│   │   │   └── delivery_partner_router.py
│   │   └── schema/
│   │       ├── shipment_schema.py   # includes nested SellerRead + DeliveryPartnerRead
│   │       ├── seller_schema.py
│   │       └── delivery_partner_schema.py
│   ├── database/
│   │   ├── config.py             # Postgres + Redis + JWT settings
│   │   ├── models.py             # User, Seller, DeliveryPartner, Shipment + Relationships
│   │   ├── redis.py              # Async Redis client + JTI blacklist
│   │   └── session.py            # Async engine, SessionDep
│   └── services/
│       ├── base_service.py       # Generic[ModelT, IdT] — shared CRUD
│       ├── auth_service.py       # Pure functions: hash, verify, issue token, blacklist
│       ├── auth_entity_service.py# Generic auth mixin: login, get_entity, logout
│       ├── seller_service.py     # Extends AuthEntityService[Seller]
│       ├── delivery_partner_service.py # Extends AuthEntityService[DeliveryPartner]
│       └── shipment_service.py   # Smart partner assignment + selectinload
├── docs/
├── mkdocs.yml
├── requirements.txt
└── venv/
```

---

Ready to start? Head to **[Chapter 1: Getting Started →](chapters/ch01-getting-started.md)**
