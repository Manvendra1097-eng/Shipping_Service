# Python Decorators — The Magic Behind `@app.get()`

Every time you write `@app.get("/shipment/latest")` in FastAPI, you're using a **Python decorator**. But what exactly is a decorator, and how does it work? This deep-dive will demystify the concept by building a mini routing framework from scratch.

---

## What is a Decorator?

A decorator is a function that **wraps another function** to modify or extend its behavior — without changing the original function's code.

Here's the simplest possible decorator:

```python
def my_decorator(func):
    def wrapper():
        print("Before the function runs")
        func()
        print("After the function runs")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
```

**Output:**
```
Before the function runs
Hello!
After the function runs
```

### What Actually Happens?

The `@my_decorator` syntax is **syntactic sugar**. It's equivalent to:

```python
def say_hello():
    print("Hello!")

say_hello = my_decorator(say_hello)  # ← Same as @my_decorator
```

So `@decorator` is just a shorthand for reassigning the function to a wrapped version of itself.

---

## Connecting to FastAPI

In your `app/main.py`, you write:

```python
@app.get("/shipment/latest")
def get_latest_shipment() -> dict[str, Any]:
    id = max(shipments.keys())
    return shipments[id]
```

This is a decorator in action! Here's what FastAPI does behind the scenes:

1. `app.get("/shipment/latest")` is called → returns a decorator function
2. That decorator receives `get_latest_shipment` as its argument
3. Inside, FastAPI **registers** the function in its internal route table: *"when someone visits GET /shipment/latest, call this function"*
4. The original function is returned unchanged

This is called a **decorator factory** — a function that *creates* a decorator. Let's build one ourselves.

---

## Building a Mini Router

To truly understand how `@app.get()` works, let's build a simplified version from scratch:

```python
from typing import Callable, Any

# This dictionary stores our routes — just like FastAPI's internal route table
routes: dict[str, Callable[[Any], Any]] = {}

# The decorator factory
def router(path: str):
    def wrapper(func):
        routes[path] = func   # Register the function for this path
        return func            # Return the original function unchanged
    return wrapper
```

### Using Our Router

```python
@router("/shipment")
def get_shipment():
    return {"message": "Your shipment is on the way"}

@router("/status")
def get_status():
    return {"status": "active"}
```

### What Happens Step by Step

```
1. @router("/shipment") is called
   ↓
2. router() receives path="/shipment" and returns wrapper function
   ↓
3. wrapper() receives get_shipment as its argument
   ↓
4. routes["/shipment"] = get_shipment  (registered!)
   ↓
5. wrapper() returns get_shipment unchanged
   ↓
6. get_shipment is now in the routes dictionary
```

After both decorators run, our `routes` dictionary looks like:

```python
{
    "/shipment": <function get_shipment>,
    "/status": <function get_status>
}
```

### Testing Our Router

Here's a simple CLI loop to dispatch requests:

```python
request = ""
while request != "quit":
    request = input("> ")
    if request in routes:
        print(routes[request]())
    else:
        print("No route found")
```

```
> /shipment
{'message': 'Your shipment is on the way'}
> /status
{'status': 'active'}
> /unknown
No route found
> quit
```

**This is essentially what FastAPI does** — just with HTTP requests instead of terminal input, and a lot more features on top.

---

## Types of Decorators

### 1. Simple Decorator (no arguments)

```python
def log_calls(func):
    def wrapper(*args, **kwargs):
        print(f"Calling: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@log_calls
def get_shipment():
    return {"message": "Shipment data"}
```

### 2. Decorator Factory (with arguments)

This is what FastAPI uses — a function that **takes arguments** and **returns a decorator**:

```python
def router(path: str):           # ← Takes arguments
    def decorator(func):         # ← This is the actual decorator
        routes[path] = func
        return func
    return decorator              # ← Returns the decorator

@router("/shipment")             # ← router("/shipment") returns the decorator
def get_shipment():              # ← The decorator receives this function
    pass
```

!!! info "Two Layers of Wrapping"
    - **Simple decorator**: `@log_calls` → one layer (`func → wrapper`)
    - **Decorator factory**: `@router("/shipment")` → two layers (`args → decorator → func`)

    FastAPI uses the factory pattern because it needs to pass the URL path as an argument.

---

## Making It More Powerful: Adding Logging

Let's enhance our router to log every request:

```python
def router_with_logging(path: str):
    def wrapper(func):
        def inner(*args, **kwargs):
            print(f"📥 Request received: {path}")
            result = func(*args, **kwargs)
            print(f"📤 Response sent for: {path}")
            return result
        routes[path] = inner
        return func
    return wrapper

@router_with_logging("/shipment")
def get_shipment():
    return {"message": "Shipment data"}
```

Now every call to this route gets logged automatically. This is exactly how FastAPI's middleware and dependency injection work under the hood.

---

## Stacking Decorators

You can apply multiple decorators to a single function. They execute **bottom-up**:

```python
def log(func):
    def wrapper(*args, **kwargs):
        print(f"LOG: Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def validate(func):
    def wrapper(*args, **kwargs):
        print("VALIDATE: Checking inputs...")
        return func(*args, **kwargs)
    return wrapper

@log           # ← Runs second (outermost)
@validate      # ← Runs first (innermost)
@router("/shipment")
def get_shipment():
    return {"message": "Shipment data"}
```

**Output when called:**
```
LOG: Calling wrapper
VALIDATE: Checking inputs...
```

---

## Best Practice: Use `functools.wraps`

When you wrap a function with a decorator, the wrapper replaces the original function's metadata (name, docstring, etc.). Use `@wraps` to preserve it:

```python
from functools import wraps

def router(path: str):
    def wrapper(func):
        @wraps(func)  # ← Preserves func.__name__, func.__doc__, etc.
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        routes[path] = inner
        return func
    return wrapper
```

!!! warning "Why this matters"
    Without `@wraps`, debugging tools, logging, and FastAPI's auto-docs would show `"inner"` or `"wrapper"` as the function name instead of `"get_shipment"`. Always use `@wraps` in production decorators.

---

## Decorator vs No Decorator

Here's the same functionality without decorators — notice how the decorator version is cleaner:

### Without Decorator ❌
```python
def get_shipment():
    return {"message": "Shipment data"}

def get_status():
    return {"status": "active"}

# Manual registration — easy to forget, hard to read
routes["/shipment"] = get_shipment
routes["/status"] = get_status
```

### With Decorator ✅
```python
@router("/shipment")
def get_shipment():
    return {"message": "Shipment data"}

@router("/status")
def get_status():
    return {"status": "active"}
```

The decorator version is:

- **Self-documenting** — you can see the route right above the function
- **Impossible to forget** — registration happens automatically
- **Consistent** — every route follows the same pattern

---

## Key Takeaways

| Concept | Summary |
|---------|---------|
| **Decorator** | A function that wraps another function to add behavior |
| **`@syntax`** | Syntactic sugar for `func = decorator(func)` |
| **Decorator Factory** | A function that takes arguments and returns a decorator (e.g., `@app.get("/path")`) |
| **`@wraps`** | Preserves the wrapped function's metadata |
| **FastAPI's `@app.get()`** | A decorator factory that registers your function in FastAPI's route table |

The decorator pattern is one of Python's most powerful features. Understanding it deeply will help you not just with FastAPI, but with every Python framework you encounter.

---

## Further Reading

- [Python Decorator Documentation](https://docs.python.org/3/glossary.html#term-decorator) — Official Python docs
- [RealPython: Primer on Decorators](https://realpython.com/primer-on-python-decorators/) — Comprehensive tutorial
- [PEP 318 — Decorators for Functions](https://peps.python.org/pep-0318/) — The proposal that introduced decorator syntax

---

**[← Back to Home](../index.md)**
