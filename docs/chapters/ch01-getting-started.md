# Chapter 1: Setting Up Your First FastAPI Project

In this chapter, you'll set up the project from scratch and get a FastAPI server running on your machine. By the end, you'll have a working API you can hit from your browser.

---

## What is FastAPI?

FastAPI is a **modern Python web framework** for building APIs. If you've used Flask or Django, FastAPI will feel familiar — but with some powerful upgrades:

| Feature | Flask | Django | FastAPI |
|---------|-------|--------|---------|
| Async support | ❌ (add-on) | ❌ (add-on) | ✅ Built-in |
| Auto API docs | ❌ | ❌ | ✅ Built-in |
| Type validation | ❌ | Partial | ✅ Built-in |
| Performance | Moderate | Moderate | Very High |

FastAPI achieves this by building on two key Python features: **type hints** and **async/await**.

---

## Prerequisites

Before you begin, make sure you have:

- **Python 3.8 or higher** — Check with `python --version`
- **pip** — Python's package installer (comes with Python)
- A **code editor** — VS Code, PyCharm, or any editor you prefer
- A **terminal** — Command Prompt, PowerShell, or your system terminal

---

## Step 1: Clone or Create the Project

If you're cloning this repository:

```bash
git clone <repository-url>
cd learn_fastapi
```

Or if you're starting fresh, create a new folder:

```bash
mkdir learn_fastapi
cd learn_fastapi
```

---

## Step 2: Create a Virtual Environment

A virtual environment keeps your project dependencies isolated from other Python projects on your machine.

```bash
python -m venv venv
```

!!! info "What is `venv`?"
    The `venv` module creates a self-contained directory (`venv/`) with its own Python interpreter and `pip`. This way, installing packages for this project won't affect your global Python installation.

### Activate the virtual environment

**On Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**On Linux/Mac:**
```bash
source venv/bin/activate
```

You'll see `(venv)` appear in your terminal prompt — that means it's active.

---

## Step 3: Install Dependencies

Install the core packages needed for this project:

```bash
pip install fastapi uvicorn scalar-fastapi
```

Let's understand what each package does:

| Package | What it does |
|---------|-------------|
| `fastapi` | The web framework — handles routing, validation, serialization |
| `uvicorn` | The ASGI server — actually runs your app and listens for HTTP requests |
| `scalar-fastapi` | Provides a beautiful, interactive API documentation UI |

!!! note "Why do we need Uvicorn separately?"
    FastAPI is just the framework — it defines how your app handles requests. But it doesn't include a server. **Uvicorn** is the server that actually listens on a port and forwards HTTP requests to FastAPI. Think of it like: Uvicorn is the waiter, FastAPI is the chef.

!!! tip "This evolves later"
    As the project grows, we'll add more packages: **Pydantic** for data models (Chapter 4), **SQLAlchemy** for databases (Chapter 6), and more. Each chapter will introduce new dependencies as needed.

---

## Step 4: Understand the Project Structure

The app code lives in the `app/` folder:

```
app/
├── __init__.py      # Makes this folder a Python "package"
└── main.py          # Your FastAPI application
```

### `__init__.py` — The Package Marker

This file is empty, but it's important. It tells Python that `app/` is a **package** (a collection of modules), not just a regular folder. Without it, you can't import from `app/`.

### `main.py` — The Application

This is where your FastAPI app lives. Here's the starting point:

```python
from fastapi import FastAPI

app = FastAPI()
```

That's it — two lines, and you have a working web application! The `app` object is your FastAPI application instance. All your routes, middleware, and configuration attach to this object.

!!! note "This file will grow"
    Right now `main.py` is tiny. In [Chapter 2](ch02-building-endpoints.md), we'll add endpoints. In later chapters, we'll split the code into multiple files using **routers** — but for now, everything lives here.

---

## Step 5: Run the Server

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

Let's break down this command:

| Part | Meaning |
|------|---------|
| `uvicorn` | The ASGI server |
| `app.main` | Python module path → `app/main.py` |
| `:app` | The FastAPI instance variable name inside `main.py` |
| `--reload` | Auto-restart when you edit code (development only!) |

You should see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to stop)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Step 6: Explore What's Running

Open your browser and visit these URLs:

### 📄 Auto-Generated Docs (Swagger UI)
```
http://localhost:8000/docs
```
FastAPI **automatically** generates interactive API documentation from your code. You can test endpoints directly from this page!

### 📋 OpenAPI Schema
```
http://localhost:8000/openapi.json
```
This is the raw OpenAPI specification — a machine-readable JSON file describing your entire API. FastAPI builds this automatically from your route definitions and type hints.

### 🎨 Scalar UI (Custom Docs)
```
http://localhost:8000/scalar
```
This project also includes [Scalar](https://scalar.com/), a modern and visually polished alternative API documentation UI.

---

## What You Learned

In this chapter, you:

- ✅ Understood what FastAPI is and how it compares to Flask/Django
- ✅ Set up a Python virtual environment
- ✅ Installed FastAPI, Uvicorn, and Scalar
- ✅ Learned about the `app/` package structure
- ✅ Started your first FastAPI server
- ✅ Discovered the auto-generated API docs

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`

Your virtual environment isn't activated, or dependencies aren't installed. Run:

```bash
# Activate venv first, then:
pip install fastapi uvicorn scalar-fastapi
```

### `Error: [Errno 98] Address already in use` (or port 8000 is busy)

Another process is using port 8000. Use a different port:

```bash
uvicorn app.main:app --reload --port 8001
```

### `Error loading ASGI app. Could not import module "app.main"`

Make sure you're running the command from the **project root** (`learn_fastapi/`), not from inside the `app/` folder.

---

## Next Steps

Your server is running, but it doesn't have any endpoints yet (except the auto-generated docs). In the next chapter, you'll build real API endpoints.

**[Chapter 2: Building API Endpoints →](ch02-building-endpoints.md)**
