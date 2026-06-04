from fastapi import FastAPI, HTTPException, status
from scalar_fastapi import get_scalar_api_reference

from app.database import DB
from app.schema import ShipmentCreate, ShipmentRead, ShipmentUpdate

app = FastAPI()

db = DB()


@app.get("/shipment/{id}", response_model=ShipmentRead)
def get_shipment(id: int | None = None):
    shipment = db.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given ID doesn't exits"
        )
    return shipment


@app.post("/shipment", response_model=None)
def submit_shipment(req_body: ShipmentCreate):
    new_id = db.create(req_body)
    return {"id": new_id}


@app.patch("/shipment/{id}", response_model=ShipmentRead)
def update_shipment(id: int, req_body: ShipmentUpdate):
    shipment = db.update(id, req_body)
    return shipment


@app.delete("/shipment/{id}")
def cancel_shipment(id: int) -> dict[str, str]:
    db.delete(id)
    return {"detail": f"Shpment with id {id} is deleted"}


@app.get("/scalar", include_in_schema=False)
def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
    )
