from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")
IdT = TypeVar("IdT")


class BaseService(Generic[ModelT, IdT]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, model: type[ModelT], id: IdT) -> ModelT | None:
        return await self.session.get(model, id)

    async def add_and_commit(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update_and_commit(self, instance: ModelT, **changes) -> ModelT:
        instance.sqlmodel_update(changes)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete_and_commit(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.commit()
