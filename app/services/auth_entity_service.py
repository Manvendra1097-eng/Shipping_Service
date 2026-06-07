from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database.models import User
from app.services.auth_service import (
    blacklist_token_if_valid,
    issue_access_token,
    verify_password,
)
from app.services.base_service import BaseService

ModelT = TypeVar("ModelT", bound=User)


class AuthEntityService(BaseService[ModelT, UUID], Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT], role: str):
        super().__init__(session)
        self.model = model
        self.role = role

    async def login_with_email(self, email: str, password: str) -> str | None:
        statement = select(self.model).where(self.model.email == email)
        result = await self.session.execute(statement)
        user = result.scalar()

        if user is None or not verify_password(password, user.password):
            return None

        return issue_access_token(user.name, str(user.id), self.role)

    async def get_entity(self, id: UUID) -> ModelT | None:
        return await self.get_by_id(self.model, id)

    async def logout_token(self, jti: str, exp: int | float) -> None:
        await blacklist_token_if_valid(jti, exp)
