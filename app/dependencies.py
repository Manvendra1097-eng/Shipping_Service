from typing import Annotated, Awaitable, Callable, TypeVar
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

EntityT = TypeVar("EntityT")


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
seller_oauth_scheme = OAuth2PasswordBearer(tokenUrl="/seller/login", auto_error=False)
partner_oauth_scheme = OAuth2PasswordBearer(
    tokenUrl="/partner/login", auto_error=False
)
SellerOAuth2PasswordBearerDep = Annotated[str | None, Depends(seller_oauth_scheme)]
PartnerOAuth2PasswordBearerDep = Annotated[str | None, Depends(partner_oauth_scheme)]


# Access Token Data Dependency
def _get_token(token: str | None):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
        )
    return token


def get_seller_token(token: SellerOAuth2PasswordBearerDep):
    return _get_token(token)


def get_partner_token(token: PartnerOAuth2PasswordBearerDep):
    return _get_token(token)


SellerTokenDep = Annotated[str, Depends(get_seller_token)]
PartnerTokenDep = Annotated[str, Depends(get_partner_token)]


# Payload Dependency
async def _get_payload_from_token(token: str, expected_role: str):
    payload = get_payload(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    role = payload.get("role")
    if role != expected_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token role mismatch",
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


async def get_seller_payload_from_token(token: SellerTokenDep):
    return await _get_payload_from_token(token, "seller")


async def get_partner_payload_from_token(token: PartnerTokenDep):
    return await _get_payload_from_token(token, "delivery_partner")


SellerPayloadDep = Annotated[dict, Depends(get_seller_payload_from_token)]
PartnerPayloadDep = Annotated[dict, Depends(get_partner_payload_from_token)]


def _get_uuid_from_payload(payload: dict) -> UUID:
    entity_id = payload.get("id")
    try:
        return UUID(str(entity_id))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )


async def _get_logged_in_entity(
    payload: dict,
    entity_getter: Callable[[UUID], Awaitable[EntityT | None]],
    not_found_detail: str,
) -> EntityT:
    entity_uuid = _get_uuid_from_payload(payload)
    entity = await entity_getter(entity_uuid)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=not_found_detail,
        )
    return entity


# Logged In Seller
async def get_logged_in_seller(payload: SellerPayloadDep, service: SellerServiceDep):
    return await _get_logged_in_entity(
        payload,
        service.get_entity,
        "Seller account not found",
    )


LoggedInSellerDep = Annotated[Seller, Depends(get_logged_in_seller)]


# Delivery Partner Service Dependency
async def get_delivery_service(session: SessionDep):
    return DeliveryPartnerService(session)


DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService, Depends(get_delivery_service)
]


# Logged In Delivery Partner
async def get_logged_in_delivery_partner(
    payload: PartnerPayloadDep, service: DeliveryPartnerServiceDep
):
    return await _get_logged_in_entity(
        payload,
        service.get_entity,
        "Delivery partner account not found",
    )


LoggedInDeliveryPartnerDep = Annotated[
    DeliveryPartner, Depends(get_logged_in_delivery_partner)
]
