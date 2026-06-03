# Getting Started

This guide will help you set up and run the Shipping Service on your local machine.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Shipping_Service
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**On Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install fastapi uvicorn scalar-fastapi
```

## Running the Service

### Start the Development Server

```bash
cd app
uvicorn main:app --reload
```

The service will start on `http://localhost:8000`

### Access the API Documentation

- **Scalar UI**: http://localhost:8000/scalar
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Testing Endpoints

### Get Shipment Status

```bash
curl http://localhost:8000/shipment
```

**Response:**
```json
{
  "content": "wooden table",
  "status": "in transit"
}
```

## Project Structure

```
app/
├── __init__.py      # Package initialization
└── main.py          # Main FastAPI application

concept/
└── decorator-routing.py  # Decorator pattern implementation

docs/
└── *.md            # Documentation files
```

## Next Steps

- Read the [API Documentation](api.md) to explore available endpoints
- Check the [Architecture](architecture.md) to understand the system design
- Learn about the [Decorator Pattern](concepts/decorator.md) used in routing

## Troubleshooting

### Module Not Found Error

Make sure you have activated your virtual environment and installed all dependencies:

```bash
pip install -r requirements.txt
```

### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
uvicorn main:app --reload --port 8001
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Scalar Documentation](https://scalar.com/)
