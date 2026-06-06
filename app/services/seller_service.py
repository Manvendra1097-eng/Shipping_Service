from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlmodel import select

from app.api.schema.seller_schema import SellerCreate
from app.database.models import Seller
from app.database.redis import add_jti_to_blacklist
from app.utils import get_token

ctx = CryptContext(schemes=["bcrypt"])


class SellerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, seller: SellerCreate) -> Seller:
        seller = Seller(
            **seller.model_dump(exclude=["password"]),
            password=ctx.hash(seller.password),
        )
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller

    async def login(self, email: str, password: str):
        statment = select(Seller).where(Seller.email == email)
        result = await self.session.execute(statment)
        user = result.scalar()

        if user is None or not ctx.verify(password, user.password):
            return None

        return get_token(data={"name": user.name, "id": user.id})

    async def get_seller(self, id: int):
        return await self.session.get(Seller, id)

    async def logout(self, jti: str, exp: int):
        ex = exp - int(datetime.now(timezone.utc).timestamp())
        await add_jti_to_blacklist(jti, ex)
