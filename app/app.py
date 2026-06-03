from fastapi import FastAPI, HTTPException, status
from scalar_fastapi import get_scalar_api_reference
from typing import Any

from app.schema import Shipment

app = FastAPI()


shipments = {
    12701: {
        "weight": 0.6,
        "content": "Wooden table",
        "status": "in-transit",
    },
    12702: {"weight": 1, "content": "Wooden Chai", "status": "Ordered"},
}


@app.get("/shipment/latest")
def get_latest_shipment() -> dict[str, Any]:
    id = max(shipments.keys())
    return shipments[id]


@app.get("/shipment/{id}")
def get_shipment(id: str) -> dict[str, Any]:
    if id not in shipments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given ID doesn't exits"
        )
    return shipments[id]


@app.post("/shipment", response_model=Shipment)
def submit_shipment(req_body: Shipment):
    id = max(shipments.keys()) + 1
    shipments[id] = req_body.model_dump()
    return Shipment.model_validate(shipments[id])


@app.patch("/shipment/{id}")
def update_shipment(id: int, req_body: dict[str, Any]) -> dict[str, Any]:
    shipment = shipments[id]
    shipment.update(req_body)
    return shipments[id]


@app.delete("/shipment/{id}")
def cancel_shipment(id: int) -> int:
    if not shipments[id]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shipment ID doesn't exists."
        )
    del shipments[id]
    return id


@app.get("/scalar", include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
    )
