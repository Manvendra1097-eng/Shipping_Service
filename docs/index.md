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

### Part 3: Authentication & Security 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 8 | OAuth2 & JWT | Login/logout, JWT tokens, password hashing |
| Chapter 9 | Protecting Endpoints | Dependency injection for auth, role-based access |

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

## Project Structure

Here is the actual layout of this project:

```
learn_fastapi/
├── .env                          # Secrets — NOT committed to git
├── app/
│   ├── __init__.py
│   ├── app.py                    # FastAPI entry point + lifespan + router registration
│   ├── api/
│   │   ├── router.py             # Shipment CRUD endpoints (APIRouter)
│   │   └── schema/
│   │       └── shipment_schema.py # Pydantic request/response models
│   ├── database/
│   │   ├── config.py             # pydantic-settings + .env loader
│   │   ├── models.py             # SQLModel table definitions
│   │   └── session.py            # Async engine, init_db, SessionDep, ShipmentServiceDep
│   └── services/
│       └── shipment_service.py   # Business logic — add, get, update, delete
├── docs/
│   ├── index.md
│   ├── chapters/
│   │   ├── ch01 — ch07.md
│   └── concepts/
│       ├── decorator.md
│       ├── enum.md
│       ├── path_and_query_parameter.md
│       ├── pydantic.md
│       ├── sqlmodel.md
│       ├── async_concurrency.md
│       ├── api_router.md
│       ├── service_layer.md
│       └── pydantic_settings.md
├── mkdocs.yml
├── requirements.txt
└── venv/
```

---

Ready to start? Head to **[Chapter 1: Getting Started →](chapters/ch01-getting-started.md)**
