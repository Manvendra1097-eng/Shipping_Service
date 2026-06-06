from fastapi import APIRouter

from app.api.router.shipment_router import shipment_router
from app.api.router.seller_router import seller_router

app_router = APIRouter()

app_router.include_router(shipment_router)
app_router.include_router(seller_router)
