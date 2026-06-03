from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from typing import Any

app = FastAPI()

shipments = {
    12701:{
        "id": 12701,
        "content": "Wooden table",
        "status": "in-transit"
    },
     12702:{
        "id": 12702,
        "content": "Wooden Chai",
        "status": "Ordered"
    }
}

@app.get("/shipment/latest")
def get_latest_shipment() -> dict[str,Any]:
    id = max(shipments.keys())
    return shipments[id]

@app.get("/shipment/{id}")
def get_shipment(id: str) -> dict[str, Any]:
    if id not in shipments:
        return {
            "details": "Given ID doesn't exits"
        }
    return shipments[id]

@app.get("/scalar",include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url= app.openapi_url,
    )
