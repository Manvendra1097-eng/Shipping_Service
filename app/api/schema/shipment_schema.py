from datetime import datetime
from enum import Enum
from random import randint
from typing import Optional

from pydantic import BaseModel, Field

from app.api.schema.delivery_partner_schema import DeliveryPartnerRead
from app.api.schema.seller_schema import SellerRead


def random_generator():
    return randint(110000, 129999)


class ShipmentStatus(str, Enum):
    PLACED = "placed"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_of_delivery"
    DELIVERED = "delivered"


class BaseShipment(BaseModel):
    content: str = Field(max_length=30, description="Contents of the shipment")
    weight: float = Field(lt=25, description="Weight of the shipment in kg")
    destination: Optional[int] = Field(
        default_factory=random_generator,
        description=" Destination zipcode, if not passed send to random location 😁",
    )


class ShipmentCreate(BaseShipment):
    pass


class ShipmentRead(BaseShipment):
    status: ShipmentStatus
    estimated_delivery: datetime
    seller: SellerRead
    delivery_partner: DeliveryPartnerRead | None = None


class ShipmentUpdate(BaseModel):
    status: ShipmentStatus | None = Field(
        default=None, description="Status of the shipment"
    )
    estimated_delivery: datetime | None = Field(default=None)
