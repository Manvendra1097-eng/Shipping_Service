from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.database.config import config
from app.services.seller_service import SellerService
from app.services.shipment_service import ShipmentService


engine = create_async_engine(
    url=config.POSTGRES_URL,
    echo=True,
)


async def init_db():
    async with engine.begin() as conn:
        from app.database.models import Shipment  # noqa: F401

        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async_session = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_shipment_service(session: SessionDep):
    return ShipmentService(session)


ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]


# for seller service
async def get_seller_service(session: SessionDep):
    return SellerService(session)


SellerServiceDep = Annotated[SellerService, Depends(get_seller_service)]
