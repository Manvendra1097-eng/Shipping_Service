# Custom Decorator Routing

This page documents the conceptual implementation of a custom, decorator-based routing system for the **Shipping Service**. It allows you to map URL paths directly to Python handler functions using clean annotations, similar to frameworks like FastAPI or Flask.

---

## The Logic

The routing engine relies on a global dictionary (`routes`) that stores a mapping between a `str` path and a `Callable` function. The `@router` decorator acts as a factory, capturing the path first and then registering the decorated function into the dictionary.

### Implementation Code

Here is the exact implementation used in `concept/decorator-routing.py`:

```python
from typing import Callable, Any

# Global registry for application routes
routes: dict[str, Callable[[Any], Any]] = {}

def router(path: str):
    """
    A decorator factory that registers a route mapping 
    a URL path to a handler function.
    """
    def wrapper(fun):
        routes[path] = fun
        return fun
    return wrapper

# Example Route Usage
@router("/shipment")
def get_shipment():
    return {
        "message": "You shipment is on the way"
    }

request = ""

while request != "quit":
    request = input("> ")
    if request in routes:
        print (routes[request]())
    else:
        print("No route found")

```