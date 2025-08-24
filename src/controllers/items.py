from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.database import engine
from src.models.items import Items


async def handle_get_items():
    async with AsyncSession(engine) as session:
        result = await session.exec(select(Items))

        return result.all()


async def handle_get_items_by_id(item_id: int):
    async with AsyncSession(engine) as session:
        item = await session.get(Items, item_id)

        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado")

        return item


async def handle_post_items(item: Items):
    async with AsyncSession(engine) as session:
        session.add(item)

        await session.commit()

        await session.refresh(item)

        return item


async def handle_patch_items(item_id: int, item: Items):
    async with AsyncSession(engine) as session:
        db_item = await session.get(Items, item_id)

        if not db_item:
            raise HTTPException(status_code=404, detail="Item não encontrado")

        update_data = item.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(db_item, key, value)

        await session.commit()

        await session.refresh(db_item)

        return db_item


async def handle_delete_items(item_id: int):
    async with AsyncSession(engine) as session:
        item = await session.get(Items, item_id)

        if not item:
            raise HTTPException(status_code=404, detail="Item não encontrado")

        await session.delete(item)

        await session.commit()

        return {"message": "Item removido com sucesso"}
