from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import ARRAY, INTEGER, Column
from sqlmodel import Relationship, SQLModel, Field
from sqlalchemy.dialects import postgresql as pg

from app.api.schema.shipment_schema import ShipmentStatus


class Shipment(SQLModel, table=True):
    __tablename__ = "shipment"
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True), default_factory=uuid4)
    content: str
    weight: float = Field(le=25)
    destination: int
    status: ShipmentStatus
    estimated_delivery: datetime

    seller_id: UUID = Field(foreign_key="seller.id")
    seller: "Seller" = Relationship(back_populates="shipments")

    delivery_partner_id: Optional[UUID] = Field(
        default=None, foreign_key="delivery_partner.id"
    )
    delivery_partner: "DeliveryPartner" = Relationship(back_populates="shipments")

    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))


class User(SQLModel):
    name: str
    email: EmailStr
    password: str


# Seller model
class Seller(User, table=True):
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True), default_factory=uuid4)

    shipments: list[Shipment] = Relationship(back_populates="seller")


class DeliveryPartner(User, table=True):
    __tablename__ = "delivery_partner"
    id: UUID = Field(sa_column=Column(pg.UUID, primary_key=True), default_factory=uuid4)

    serviceable_zip_code: list[int] = Field(sa_column=Column(ARRAY(INTEGER)))
    max_handling_capacity: int

    shipments: list[Shipment] = Relationship(back_populates="delivery_partner")

    created_at: datetime = Field(sa_column=Column(pg.TIMESTAMP, default=datetime.now))
