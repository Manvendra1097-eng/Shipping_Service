from enum import Enum
from random import randint
from typing import Optional

from pydantic import BaseModel, Field


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


class ShipmentUpdate(BaseModel):
    status: ShipmentStatus = Field(description="Status of the shipment")
