from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schema.seller_schema import SellerCreate
from app.database.models import Seller
from app.services.auth_entity_service import AuthEntityService
from app.services.auth_service import (
    hash_password,
)


class SellerService(AuthEntityService[Seller]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Seller, "seller")

    async def add(self, seller: SellerCreate) -> Seller:
        seller_model = Seller(
            **seller.model_dump(exclude=["password"]),
            password=hash_password(seller.password),
        )
        return await self.add_and_commit(seller_model)

    async def login(self, email: str, password: str):
        return await self.login_with_email(email, password)

    async def get_seller(self, id: UUID):
        return await self.get_entity(id)

    async def logout(self, jti: str, exp: int | float):
        await self.logout_token(jti, exp)
