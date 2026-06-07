from fastapi import APIRouter, HTTPException, status

from app.api.schema.seller_schema import SellerCreate, SellerRead, TokenResponse
from app.dependencies import (
    OAuth2PasswordRequestFormDep,
    PayloadDep,
    SellerServiceDep,
)


seller_router = APIRouter(prefix="/seller", tags=["Seller"])


@seller_router.post("/signup", response_model=SellerRead)
async def create_seller(seller: SellerCreate, service: SellerServiceDep):
    return await service.add(seller)


@seller_router.post("/login", response_model=TokenResponse)
async def login(request: OAuth2PasswordRequestFormDep, service: SellerServiceDep):
    token = await service.login(request.username, request.password)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return {"access_token": token, "token_type": "bearer"}


@seller_router.get("/logout")
async def logout(payload: PayloadDep, service: SellerServiceDep):
    jti = payload.get("jti")
    exp = payload.get("exp")

    if not isinstance(jti, str) or not isinstance(exp, (int, float)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token",
        )

    await service.logout(jti, exp)
    return {"detail": " Logged out successfully"}
