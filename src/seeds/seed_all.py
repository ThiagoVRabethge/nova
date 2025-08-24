from src.seeds.users import seed_users


async def seed_all():
    await seed_users()
