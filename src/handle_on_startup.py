from src.config.database import create_db_and_tables
from src.seeds.seed_all import seed_all


async def handle_on_startup():
    await create_db_and_tables()

    await seed_all()
