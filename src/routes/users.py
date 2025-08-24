from fastapi import APIRouter

from src.controllers.users import handle_users_login
from src.models.users import Users

users_routes = APIRouter()


@users_routes.post("/users/login")
async def users_login(user: Users):
    return await handle_users_login(user)
