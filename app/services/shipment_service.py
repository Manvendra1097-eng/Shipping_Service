from app.api.schema.shipment_schema import (
    ShipmentCreate,
    ShipmentStatus,
    ShipmentUpdate,
)
from app.database.models import Shipment
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession


class ShipmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: int) -> Shipment:
        return await self.session.get(Shipment, id)

    async def add(self, shipment_create: ShipmentCreate):
        shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.PLACED,
            estimated_delivery=datetime.now() + timedelta(days=3),
        )
        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment.id

    async def update(self, id: int, shipment_update: dict) -> Shipment:
        shipment = await self.session.get(Shipment, id)
        shipment.sqlmodel_update(shipment_update)

        self.session.add(shipment)
        await self.session.commit()
        await self.session.refresh(shipment)
        return shipment

    async def delete(self, id: int) -> None:
        shipment = await self.session.get(Shipment, id)
        await self.session.delete(shipment)
        await self.session.commit()
