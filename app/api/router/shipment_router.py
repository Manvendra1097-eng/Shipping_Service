from uuid import UUID

from fastapi import HTTPException, status, APIRouter

from app.dependencies import LoggedInSellerDep, ShipmentServiceDep
from app.api.schema.shipment_schema import (
    ShipmentCreate,
    ShipmentRead,
    ShipmentUpdate,
)
from app.services.shipment_service import NoDeliveryPartnerAvailableError


shipment_router = APIRouter(prefix="/shipment", tags=["Shipment"])


@shipment_router.get("/{id}", response_model=ShipmentRead)
async def get_shipment(id: UUID, service: ShipmentServiceDep):
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Given ID doesn't exits"
        )
    # print(Panel(str(shipment), border_style="green"))
    return shipment


@shipment_router.post("/", response_model=None)
async def submit_shipment(
    seller: LoggedInSellerDep, req_body: ShipmentCreate, service: ShipmentServiceDep
):
    try:
        id = await service.add(req_body, seller.id)
    except NoDeliveryPartnerAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return {"id": id}


@shipment_router.patch("/{id}", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    req_body: ShipmentUpdate,
    service: ShipmentServiceDep,
    _: LoggedInSellerDep,
):
    if not req_body.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No data provided to update"
        )
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment with id {id} not found",
        )
    shipment = await service.update(id, req_body)
    return shipment


@shipment_router.delete("/{id}")
async def cancel_shipment(
    id: UUID, service: ShipmentServiceDep, _: LoggedInSellerDep
) -> dict[str, str]:
    shipment = await service.get(id)
    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shipment with id {id} not found",
        )
    await service.delete(id)
    return {"detail": f"Shipment with id {id} is deleted"}
