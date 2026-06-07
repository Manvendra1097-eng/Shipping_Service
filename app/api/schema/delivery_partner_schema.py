from pydantic import BaseModel, EmailStr, Field


class BaseDeliveryPartner(BaseModel):
    name: str
    email: EmailStr


class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str = Field(min_length=8, max_length=72)
    serviceable_zip_code: list[int]
    max_handling_capacity: int


class DeliveryPartnerRead(BaseDeliveryPartner):
    serviceable_zip_code: list[int]
    max_handling_capacity: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
