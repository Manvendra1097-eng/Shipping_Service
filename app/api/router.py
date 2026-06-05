from fastapi import HTTPException, status, APIRouter

from app.database.models import Shipment
from app.database.session import ShipmentServiceDep
from app.api.schema.shipment_schema import (
    ShipmentCreate,
    ShipmentRead,
    ShipmentUpdate,
)


shipment_router = APIRouter(prefix="/shipment", tags=["Shipment"])


@shipment_router.get("/{id}", response_model=ShipmentRead)
async def get_shipment(id: int, service: ShipmentServiceDep):
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given ID doesn't exits"
        )
    return shipment


@shipment_router.post("/", response_model=None)
async def submit_shipment(req_body: ShipmentCreate, service: ShipmentServiceDep):
    id = await service.add(req_body)
    return {"id": id}


@shipment_router.patch("/{id}", response_model=ShipmentRead)
async def update_shipment(
    id: int, req_body: ShipmentUpdate, service: ShipmentServiceDep
):
    update_data = req_body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment with id {id} not found",
        )
    shipment = await service.update(id, update_data)
    return shipment


@shipment_router.delete("/{id}")
async def cancel_shipment(id: int, service: ShipmentServiceDep) -> dict[str, str]:
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment with id {id} not found",
        )
    await service.delete(id)
    return {"detail": f"Shipment with id {id} is deleted"}
