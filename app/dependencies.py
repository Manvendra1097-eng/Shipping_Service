from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.database.models import DeliveryPartner, Seller
from app.database.redis import is_jti_blacklisted
from app.database.session import SessionDep
from app.services.delivery_partner_service import DeliveryPartnerService
from app.services.seller_service import SellerService
from app.services.shipment_service import ShipmentService
from app.utils import get_payload


# Shipment Service Dependency
async def get_shipment_service(session: SessionDep):
    return ShipmentService(session)


ShipmentServiceDep = Annotated[ShipmentService, Depends(get_shipment_service)]


# Seller Service Dependency
async def get_seller_service(session: SessionDep):
    return SellerService(session)


SellerServiceDep = Annotated[SellerService, Depends(get_seller_service)]

# OAuth2PasswordRequestForm Dependency
OAuth2PasswordRequestFormDep = Annotated[OAuth2PasswordRequestForm, Depends()]

# OAuth2PasswordBearer Dependency
oauth_scheme = OAuth2PasswordBearer(tokenUrl="/seller/login", auto_error=False)
OAuth2PasswordBearerDep = Annotated[str | None, Depends(oauth_scheme)]


# Access Token Data Dependency
def get_token(token: OAuth2PasswordBearerDep):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )
    return token


TokenDep = Annotated[str, Depends(get_token)]


# Payload Dependency
async def get_payload_from_token(token: TokenDep):
    payload = get_payload(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    if await is_jti_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )
    return payload


PayloadDep = Annotated[dict, Depends(get_payload_from_token)]


# Logged In Seller
async def get_logged_in_seller(payload: PayloadDep, service: SellerServiceDep):
    seller_id = payload.get("id")
    try:
        seller_uuid = UUID(str(seller_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    seller = await service.get_seller(seller_uuid)
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Seller account not found",
        )
    return seller


LoggedInSellerDep = Annotated[Seller, Depends(get_logged_in_seller)]


# Delivery Partner Service Dependency
async def get_delivery_service(session: SessionDep):
    return DeliveryPartnerService(session)


DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService, Depends(get_delivery_service)
]


# Logged In Delivery Partner
async def get_logged_in_delivery_partner(
    payload: PayloadDep, service: DeliveryPartnerServiceDep
):
    partner_id = payload.get("id")
    try:
        partner_uuid = UUID(str(partner_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    partner = await service.get_delivery_partner(partner_uuid)
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Delivery partner account not found",
        )
    return partner


LoggedInDeliveryPartnerDep = Annotated[
    DeliveryPartner, Depends(get_logged_in_delivery_partner)
]
