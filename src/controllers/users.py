from datetime import datetime, timedelta

import jwt
from decouple import config
from fastapi import HTTPException
from passlib.hash import sha256_crypt
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config.database import engine
from src.models.users import Users

JWT_SECRET = config("JWT_SECRET")

JWT_ALGORITHM = config("JWT_ALGORITHM")

JWT_EXPIRE_MINUTES = int(config("JWT_EXPIRE_MINUTES"))


async def handle_users_login(user: Users):
    async with AsyncSession(engine) as session:
        result = await session.exec(select(Users).where(Users.email == user.email))

        db_user = result.first()

        if not db_user or not sha256_crypt.verify(user.password, db_user.password):
            raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

        user_data = db_user.dict(exclude={"password"})

        token_data = {"sub": str(db_user.id), "email": db_user.email}

        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)

        token_data.update({"exp": expire})

        token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {"access_token": token, "token_type": "bearer", "user_data": user_data}
