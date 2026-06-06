from pydantic import BaseModel, EmailStr, Field


class BaseSeller(BaseModel):
    name: str
    email: EmailStr


class SellerCreate(BaseSeller):
    password: str = Field(min_length=8, max_length=72)


class SellerRead(BaseSeller):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
