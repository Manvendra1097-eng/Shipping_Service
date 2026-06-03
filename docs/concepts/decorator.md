# Decorator Pattern in Routing

## Overview

The Decorator Pattern is a structural design pattern that allows you to attach additional responsibilities to an object dynamically. In the context of the Shipping Service, it's used to create a simple, elegant routing system.

## What is a Decorator?

A decorator is a function that modifies the behavior of another function without permanently changing it. It "wraps" a function to add additional functionality.

### Simple Decorator Example

```python
def my_decorator(func):
    def wrapper():
        print("Something before the function")
        func()
        print("Something after the function")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
```

**Output:**
```
Something before the function
Hello!
Something after the function
```

## Decorator-Based Routing

The Shipping Service uses decorators to register routes in a simple, elegant way.

### Implementation

```python
from typing import Callable, Any

# Storage for routes
routes: dict[str, Callable[[Any], Any]] = {}

# Decorator function
def router(path: str):
    def wrapper(fun):
        routes[path] = fun  # Register the function
        return fun          # Return the original function
    return wrapper

# Using the decorator
@router("/shipment")
def get_shipment():
    return {
        "message": "You shipment is on the way"
    }

@router("/status")
def get_status():
    return {
        "status": "active"
    }
```

### How It Works

```
1. @router("/shipment") is called with path="/shipment"
   ↓
2. router() returns the wrapper function
   ↓
3. wrapper function receives get_shipment as argument
   ↓
4. routes["/shipment"] = get_shipment (registration)
   ↓
5. wrapper returns get_shipment unchanged
   ↓
6. get_shipment is now registered in the routes dictionary
```

## Advantages

### 1. **Clean Syntax**
Decorators provide a clean, readable way to define routes:
```python
@router("/shipment")
def get_shipment():
    pass
```

### 2. **Separation of Concerns**
Route registration is separated from the actual function logic.

### 3. **Reusability**
The routing mechanism can be applied to multiple functions easily.

### 4. **Extensibility**
Easy to add additional functionality like authentication, logging, validation, etc.

### 5. **Registry Pattern**
Automatically builds a registry of all available routes.

## Advanced Example: Router with Logging

Here's an enhanced decorator that adds logging:

```python
def router_with_logging(path: str):
    def wrapper(func):
        def inner(*args, **kwargs):
            print(f"Accessing route: {path}")
            result = func(*args, **kwargs)
            print(f"Route {path} completed")
            return result
        routes[path] = inner
        return func
    return wrapper

@router_with_logging("/shipment")
def get_shipment():
    return {"message": "Shipment data"}
```

## Comparison: Decorator vs Traditional Approach

### Without Decorator
```python
def get_shipment():
    return {"message": "Shipment data"}

def register_route(path, func):
    routes[path] = func

register_route("/shipment", get_shipment)
```

### With Decorator
```python
@router("/shipment")
def get_shipment():
    return {"message": "Shipment data"}
```

The decorator approach is more concise and follows modern Python conventions.

## Using the Router

```python
# Simple CLI example
routes = {}

@router("/shipment")
def get_shipment():
    return {"message": "You shipment is on the way"}

# Command loop
request = ""
while request != "quit":
    request = input("> ")
    if request in routes:
        print(routes[request]())
    else:
        print("No route found")
```

**Usage:**
```
> /shipment
{'message': 'You shipment is on the way'}
> /unknown
No route found
> quit
```

## Decorator Chain

Decorators can be stacked for multiple effects:

```python
def log_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Calling: {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

def validate_decorator(func):
    def wrapper(*args, **kwargs):
        print("Validating inputs...")
        return func(*args, **kwargs)
    return wrapper

@log_decorator
@validate_decorator
@router("/shipment")
def get_shipment():
    return {"message": "Shipment data"}
```

## Real-World Applications

The decorator pattern is used extensively in modern frameworks:

### FastAPI
```python
@app.get("/shipment")
def get_shipment():
    return {"content": "wooden table", "status": "in transit"}
```

### Flask
```python
@app.route('/shipment', methods=['GET'])
def get_shipment():
    return {'status': 'in transit'}
```

### Django
```python
@login_required
def shipment_view(request):
    return render(request, 'shipment.html')
```

## Best Practices

1. **Keep Decorators Simple** - Single responsibility principle
2. **Use functools.wraps** - Preserves function metadata
3. **Document Decorators** - Clear docstrings
4. **Test Thoroughly** - Test both decorated and undecorated behavior
5. **Avoid Over-Decorating** - Don't use decorators excessively

### Better Decorator with functools.wraps

```python
from functools import wraps

def router(path: str):
    def wrapper(func):
        @wraps(func)  # Preserves metadata
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        routes[path] = inner
        return func
    return wrapper
```

## Conclusion

The Decorator Pattern is a powerful tool for:
- Creating elegant routing systems
- Adding cross-cutting concerns
- Maintaining clean, readable code
- Building extensible frameworks

The simple router implementation in the Shipping Service demonstrates how decorators can be used to create a flexible, intuitive interface for route registration.

## See Also

- [Python Decorator Documentation](https://docs.python.org/3/glossary.html#term-decorator)
- [Functional Programming in Python](https://realpython.com/inner-functions-what-are-they-good-for/)
- [Design Patterns](https://refactoring.guru/design-patterns)
