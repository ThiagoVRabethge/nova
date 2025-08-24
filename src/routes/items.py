from fastapi import APIRouter, Depends

from src.controllers.items import (
    handle_delete_items,
    handle_get_items,
    handle_get_items_by_id,
    handle_patch_items,
    handle_post_items,
)
from src.models.items import Items
from src.security.verify_jwt_token import verify_jwt_token

items_routes = APIRouter(dependencies=[Depends(verify_jwt_token)])


@items_routes.get("/items")
async def get_items():
    return await handle_get_items()


@items_routes.get("/items/{item_id}")
async def get_item(item_id: int):
    return await handle_get_items_by_id(item_id)


@items_routes.post("/items")
async def post_items(item: Items):
    return await handle_post_items(item)


@items_routes.patch("/items/{item_id}")
async def patch_items(item_id: int, item: Items):
    return await handle_patch_items(item_id, item)


@items_routes.delete("/items/{item_id}")
async def delete_items(item_id: int):
    return await handle_delete_items(item_id)
