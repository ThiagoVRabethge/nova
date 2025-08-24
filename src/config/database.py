from decouple import config
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from src.migrations.watch import watch
from src.models.items import Items
from src.models.users import Users

database_url = config("DATABASE_URL")

engine = create_async_engine(
    database_url,
    echo=True,
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

        await watch(
            engine,
            [
                Users,
                Items,
            ],
            use_identity=False,
        )
