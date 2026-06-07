from uuid import UUID

from app.api.schema.delivery_partner_schema import DeliveryPartnerCreate
from app.database.models import DeliveryPartner
from app.services.auth_entity_service import AuthEntityService

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import (
    hash_password,
)


class DeliveryPartnerService(AuthEntityService[DeliveryPartner]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, DeliveryPartner, "delivery_partner")

    async def add(
        self, delivery_partner_create: DeliveryPartnerCreate
    ) -> DeliveryPartner:
        delivery_partner = DeliveryPartner(
            **delivery_partner_create.model_dump(exclude={"password"}),
            password=hash_password(delivery_partner_create.password),
        )
        return await self.add_and_commit(delivery_partner)

    async def login(self, email: str, password: str):
        return await self.login_with_email(email, password)

    async def get_delivery_partner(self, id: UUID):
        return await self.get_entity(id)

    async def logout(self, jti: str, exp: int | float):
        await self.logout_token(jti, exp)
