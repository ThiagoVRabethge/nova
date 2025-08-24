import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel


async def get_column_type(column, dialect: str) -> str:
    """
    Retorna o tipo de dado da coluna, ajustando para o dialeto do banco.
    """
    col_type_str = str(column.type).upper()

    if dialect == "postgresql":
        if "VARCHAR" in col_type_str:
            return "VARCHAR"
        if "TEXT" in col_type_str:
            return "TEXT"
        if "BOOLEAN" in col_type_str:
            return "BOOLEAN"
        if "INTEGER" in col_type_str:
            return "INTEGER"
        if "DATETIME" in col_type_str:
            return "TIMESTAMP"
        if "FLOAT" in col_type_str:
            return "FLOAT"

    return col_type_str


async def watch(
    engine: AsyncEngine, models: list[type[SQLModel]], use_identity: bool = False
):
    """
    Cria ou altera tabelas para corresponder aos modelos fornecidos.
    Funciona de forma assíncrona com AsyncEngine (SQLite ou PostgreSQL).
    """
    db_dialect = os.environ.get("DIALETICS", "").lower()

    if not db_dialect:
        # Detecta automaticamente pelo engine URL
        url = str(engine.url)
        if url.startswith("sqlite"):
            db_dialect = "sqlite"
        else:
            db_dialect = "postgresql"

    assert db_dialect in ("sqlite", "postgresql"), (
        f"Dialeto não suportado: {db_dialect}"
    )
    print(f"Usando o dialeto: {db_dialect}")

    async with engine.begin() as conn:
        for model in models:
            table_name = model.__tablename__

            # Verifica colunas existentes
            if db_dialect == "sqlite":
                result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns_info = result.fetchall()
                table_exists = len(columns_info) > 0
                existing_columns = {col[1] for col in columns_info}  # nomes das colunas
            else:  # PostgreSQL
                result = await conn.execute(
                    text(
                        f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                        """
                    )
                )
                rows = result.fetchall()
                table_exists = len(rows) > 0
                existing_columns = {r[0] for r in rows}

            # Criar tabela se não existir
            if not table_exists:
                columns = []
                for column in model.__table__.columns:
                    col_type = await get_column_type(column, db_dialect)
                    col_def = f"{column.name} {col_type}"

                    if column.primary_key:
                        if db_dialect == "postgresql":
                            if use_identity:
                                col_def = f"{column.name} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
                            else:
                                col_def = f"{column.name} SERIAL PRIMARY KEY"
                        elif db_dialect == "sqlite":
                            if column.autoincrement and col_type.startswith("INTEGER"):
                                col_def = (
                                    f"{column.name} INTEGER PRIMARY KEY AUTOINCREMENT"
                                )
                            else:
                                col_def += " PRIMARY KEY"

                    columns.append(col_def)

                columns_sql = ",\n    ".join(columns)
                query = text(f"CREATE TABLE {table_name} (\n    {columns_sql}\n)")
                await conn.execute(query)

            else:
                # Adicionar colunas novas se não existirem
                for column in model.__table__.columns:
                    if column.name not in existing_columns:
                        col_type = await get_column_type(column, db_dialect)
                        query = text(
                            f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}"
                        )
                        await conn.execute(query)
