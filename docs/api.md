# API Documentation

The Shipping Service provides a RESTful API for managing and tracking shipments. This document describes all available endpoints.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Get Shipment

Retrieve the current status of a shipment.

**Endpoint:**
```
GET /shipment
```

**Description:**
Returns information about a shipment including its content and current status.

**Request:**
```bash
curl -X GET "http://localhost:8000/shipment"
```

**Response:**
```json
{
  "content": "wooden table",
  "status": "in transit"
}
```

**Status Code:**
- `200` - Success

**Response Fields:**
| Field | Type | Description |
|-------|------|-------------|
| content | string | Description of the shipment contents |
| status | string | Current status of the shipment (e.g., "in transit", "delivered", "pending") |

---

### API Documentation UI

Access the interactive API documentation using Scalar UI.

**Endpoint:**
```
GET /scalar
```

**Description:**
Serves the Scalar API documentation interface. This provides an interactive way to explore and test all available endpoints.

**Access:**
Open your browser and navigate to:
```
http://localhost:8000/scalar
```

**Features:**
- Interactive endpoint testing
- Request/response examples
- Real-time API exploration
- Authentication testing (if applicable)

---

## Error Handling

All API responses follow standard HTTP status codes:

| Status Code | Meaning |
|------------|---------|
| 200 | Request successful |
| 400 | Bad request |
| 404 | Resource not found |
| 500 | Internal server error |

### Error Response Format

```json
{
  "detail": "Error description"
}
```

---

## Usage Examples

### JavaScript/Fetch API

```javascript
fetch('http://localhost:8000/shipment')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

### Python

```python
import requests

response = requests.get('http://localhost:8000/shipment')
data = response.json()
print(data)
```

### cURL

```bash
curl -X GET "http://localhost:8000/shipment" \
  -H "accept: application/json"
```

---

## Rate Limiting

Currently, there are no rate limits on the API. However, it's good practice to implement reasonable request intervals in your client applications.

---

## API Versioning

The current API version is v1.0. Future versions may be available at different URL paths (e.g., `/api/v2/shipment`).

---

## Contact & Support

For API issues or feature requests, please refer to the project repository or documentation.
