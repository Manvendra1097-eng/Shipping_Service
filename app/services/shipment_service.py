from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.schema.shipment_schema import (
    ShipmentCreate,
    ShipmentStatus,
    ShipmentUpdate,
)
from app.database.models import DeliveryPartner, Shipment
from app.services.base_service import BaseService
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession


class NoDeliveryPartnerAvailableError(Exception):
    pass


class ShipmentService(BaseService[Shipment, UUID]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def _get_active_load_by_partner(
        self, partner_ids: list[UUID]
    ) -> dict[UUID, int]:
        if not partner_ids:
            return {}

        active_statuses = [
            ShipmentStatus.PLACED,
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.OUT_FOR_DELIVERY,
        ]

        statement = (
            select(Shipment.delivery_partner_id, func.count(Shipment.id))
            .where(
                Shipment.delivery_partner_id.in_(partner_ids),
                Shipment.status.in_(active_statuses),
            )
            .group_by(Shipment.delivery_partner_id)
        )
        result = await self.session.execute(statement)

        return {partner_id: total for partner_id, total in result.all() if partner_id}

    async def _select_delivery_partner(
        self, destination_zip_code: int
    ) -> DeliveryPartner:
        statement = select(DeliveryPartner).where(
            DeliveryPartner.serviceable_zip_code.any(destination_zip_code)
        )
        result = await self.session.execute(statement)
        serviceable_partners = result.scalars().all()

        if not serviceable_partners:
            raise NoDeliveryPartnerAvailableError(
                "No delivery partner serves this destination"
            )

        active_loads = await self._get_active_load_by_partner(
            [partner.id for partner in serviceable_partners]
        )

        eligible_partners: list[tuple[DeliveryPartner, int]] = []
        for partner in serviceable_partners:
            current_load = active_loads.get(partner.id, 0)
            if current_load < partner.max_handling_capacity:
                remaining_capacity = partner.max_handling_capacity - current_load
                eligible_partners.append((partner, remaining_capacity))

        if not eligible_partners:
            raise NoDeliveryPartnerAvailableError(
                "No delivery partner has available handling capacity"
            )

        eligible_partners.sort(
            key=lambda item: (-item[1], item[0].created_at, str(item[0].id))
        )
        return eligible_partners[0][0]

    async def get(self, id: UUID) -> Shipment:
        stm = (
            select(Shipment)
            .options(
                selectinload(Shipment.seller),
                selectinload(Shipment.delivery_partner),
            )
            .where(Shipment.id == id)
        )
        result = await self.session.execute(stm)
        return result.scalar_one_or_none()

    async def add(self, shipment_create: ShipmentCreate, seller_id: UUID):
        delivery_partner = await self._select_delivery_partner(
            shipment_create.destination
        )
        shipment = Shipment(
            **shipment_create.model_dump(),
            seller_id=seller_id,
            delivery_partner_id=delivery_partner.id,
            status=ShipmentStatus.PLACED,
            estimated_delivery=datetime.now() + timedelta(days=3),
        )
        shipment = await self.add_and_commit(shipment)
        return shipment.id

    async def update(self, id: UUID, shipment_update: ShipmentUpdate) -> Shipment:
        shipment = await self.get_by_id(Shipment, id)
        return await self.update_and_commit(
            shipment, **shipment_update.model_dump(exclude_unset=True)
        )

    async def delete(self, id: UUID) -> None:
        shipment = await self.get_by_id(Shipment, id)
        await self.delete_and_commit(shipment)
