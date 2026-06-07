from fastapi import APIRouter, HTTPException, status

from app.api.schema.delivery_partner_schema import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
)
from app.api.schema.seller_schema import TokenResponse
from app.dependencies import (
    DeliveryPartnerServiceDep,
    OAuth2PasswordRequestFormDep,
    PartnerPayloadDep,
)


delivery_partner_router = APIRouter(prefix="/partner", tags=["Delivery Partner"])


@delivery_partner_router.post("/signup", response_model=DeliveryPartnerRead)
async def create_delivery_partner(
    delivery_partner: DeliveryPartnerCreate, service: DeliveryPartnerServiceDep
):
    return await service.add(delivery_partner)


@delivery_partner_router.post("/login", response_model=TokenResponse)
async def login(
    request: OAuth2PasswordRequestFormDep, service: DeliveryPartnerServiceDep
):
    token = await service.login(request.username, request.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return {"access_token": token, "token_type": "bearer"}


@delivery_partner_router.get("/logout")
async def logout(payload: PartnerPayloadDep, service: DeliveryPartnerServiceDep):
    jti = payload.get("jti")
    exp = payload.get("exp")

    if not isinstance(jti, str) or not isinstance(exp, (int, float)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    await service.logout(jti, exp)
    return {"detail": " Logged out successfully"}
