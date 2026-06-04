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
| [Chapter 5](chapters/ch05-sqlite.md) | SQLite Database | Persist data with SQLite, custom DB class, parameterized queries |

### Part 3: Database Integration 🔜

| Chapter | Topic | What You'll Learn |
|---------|-------|-------------------|
| Chapter 6 | SQLModel | Replace raw SQL with SQLModel ORM — define tables as Pydantic classes |
| Chapter 7 | Database Relationships | One-to-Many, Many-to-Many relationships |
| Chapter 8 | PostgreSQL & Alembic | Upgrade to PostgreSQL, schema migrations with Alembic |

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

## Project Structure

Here is the actual layout of this project:

```
learn_fastapi/
├── app/                          # Application code
│   ├── __init__.py               # Makes app/ a Python package
│   ├── app.py                    # FastAPI application — all endpoints live here
│   ├── database.py               # SQLite database class (DB)
│   └── schema.py                 # Pydantic models and data validation
├── docs/                         # This tutorial documentation (MkDocs)
│   ├── index.md                  # You are here!
│   ├── chapters/                 # Tutorial chapters (numbered, progressive)
│   │   ├── ch01-getting-started.md
│   │   ├── ch02-building-endpoints.md
│   │   ├── ch03-under-the-hood.md
│   │   ├── ch04-pydantic-models.md
│   │   └── ch05-sqlite.md
│   └── concepts/                 # Concept deep-dives (standalone)
│       ├── decorator.md
│       ├── enum.md
│       ├── path_and_query_parameter.md
│       └── pydantic.md
├── sqlite.db                     # SQLite database file (auto-created at runtime)
├── mkdocs.yml                    # MkDocs configuration
├── requirements.txt              # Python dependencies
└── venv/                         # Virtual environment (not committed to git)
```

---

Ready to start? Head to **[Chapter 1: Getting Started →](chapters/ch01-getting-started.md)**
