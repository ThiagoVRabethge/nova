from fastapi import FastAPI

from src.handle_on_startup import handle_on_startup
from src.middlewares.cors import cors
from src.routes.private import private
from src.routes.public import public

app = FastAPI()

cors(app)


@app.on_event("startup")
async def on_startup():
    await handle_on_startup()


@app.get("/")
async def root_info():
    return {
        "made_with": "FastApi, SQLModel",
        "docs": "see /docs",
        "redoc": "see /redoc",
    }


for public_route in public:
    app.include_router(public_route)

for private_route in private:
    app.include_router(private_route)
