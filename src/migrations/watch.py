import os
import warnings
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import MetaData, SQLModel


async def get_column_type(column, dialect: str) -> str:
    """
    Retorna o tipo de dado da coluna, ajustando para o dialeto do banco.
    """
    col_type_str = str(column.type).upper()

    # Mapeamento mais robusto de tipos
    type_mapping = {
        "postgresql": {
            "VARCHAR": "VARCHAR",
            "TEXT": "TEXT",
            "BOOLEAN": "BOOLEAN",
            "INTEGER": "INTEGER",
            "DATETIME": "TIMESTAMP",
            "TIMESTAMP": "TIMESTAMP",
            "FLOAT": "FLOAT",
            "NUMERIC": "NUMERIC",
            "DATE": "DATE",
            "BIGINT": "BIGINT",
            "SMALLINT": "SMALLINT",
        },
        "sqlite": {
            "VARCHAR": "TEXT",
            "TEXT": "TEXT",
            "BOOLEAN": "INTEGER",
            "INTEGER": "INTEGER",
            "DATETIME": "TEXT",
            "TIMESTAMP": "TEXT",
            "FLOAT": "REAL",
            "NUMERIC": "NUMERIC",
            "DATE": "TEXT",
            "BIGINT": "INTEGER",
            "SMALLINT": "INTEGER",
        },
    }

    # Procura pelo tipo mapeado ou retorna o tipo original
    for key, mapped_type in type_mapping.get(dialect, {}).items():
        if key in col_type_str:
            return mapped_type

    return col_type_str


def _get_dialect(engine: AsyncEngine) -> str:
    """Obtém o dialeto do banco de forma segura."""
    db_dialect = os.environ.get("DIALECT", "").lower()

    if not db_dialect:
        # Detecta automaticamente pelo engine URL
        url = str(engine.url)
        if url.startswith("sqlite"):
            return "sqlite"
        elif url.startswith("postgresql"):
            return "postgresql"

    if db_dialect not in ("sqlite", "postgresql"):
        raise ValueError(f"Dialeto não suportado: {db_dialect}")

    return db_dialect


async def _get_existing_columns(conn, table_name: str, dialect: str):
    """Obtém colunas existentes de forma segura."""
    if dialect == "sqlite":
        # SQLite não suporta parâmetros em PRAGMA, então usamos f-string com validação
        if not table_name.isidentifier():
            raise ValueError(f"Nome de tabela inválido: {table_name}")

        result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
        columns_info = result.fetchall()
        return {col[1] for col in columns_info}

    else:  # PostgreSQL
        # PostgreSQL suporta parâmetros normais
        result = await conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table_name
            """),
            {"table_name": table_name},
        )
        rows = result.fetchall()
        return {r[0] for r in rows}


async def _table_exists(conn, table_name: str, dialect: str) -> bool:
    """Verifica se a tabela existe de forma segura."""
    if dialect == "sqlite":
        # SQLite não suporta parâmetros em algumas consultas
        if not table_name.isidentifier():
            raise ValueError(f"Nome de tabela inválido: {table_name}")

        result = await conn.execute(
            text(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
            )
        )
    else:  # PostgreSQL
        result = await conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :table_name)"
            ),
            {"table_name": table_name},
        )

    return bool(result.scalar())


async def _create_table(conn, table, dialect: str, use_identity: bool):
    """Cria uma nova tabela de forma segura."""
    table_name = table.name

    # Validação do nome da tabela
    if not table_name.isidentifier():
        raise ValueError(f"Nome de tabela inválido: {table_name}")

    columns = []

    for column in table.columns:
        col_type = await get_column_type(column, dialect)
        col_def = f"{column.name} {col_type}"

        if column.primary_key:
            if dialect == "postgresql":
                if use_identity:
                    col_def = f"{column.name} INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
                else:
                    col_def = f"{column.name} SERIAL PRIMARY KEY"
            elif dialect == "sqlite":
                if column.autoincrement and col_type.upper().startswith("INTEGER"):
                    col_def = f"{column.name} INTEGER PRIMARY KEY AUTOINCREMENT"
                else:
                    col_def += " PRIMARY KEY"

        # Adicionar constraints NOT NULL se aplicável
        if not column.nullable and not column.primary_key:
            col_def += " NOT NULL"

        # Adicionar UNIQUE constraint
        if column.unique:
            col_def += " UNIQUE"

        columns.append(col_def)

    columns_sql = ",\n    ".join(columns)

    await conn.execute(text(f"CREATE TABLE {table_name} (\n    {columns_sql}\n)"))


async def _add_missing_columns(conn, table, existing_columns: set, dialect: str):
    """Adiciona colunas faltantes de forma segura."""
    table_name = table.name

    # Validação do nome da tabela
    if not table_name.isidentifier():
        raise ValueError(f"Nome de tabela inválido: {table_name}")

    for column in table.columns:
        if column.name not in existing_columns:
            col_type = await get_column_type(column, dialect)

            # Validação do nome da coluna
            if not column.name.isidentifier():
                raise ValueError(f"Nome de coluna inválido: {column.name}")

            # Constraint NOT NULL para colunas não nulas
            not_null = " NOT NULL" if not column.nullable else ""

            # Constraint UNIQUE
            unique = " UNIQUE" if column.unique else ""

            await conn.execute(
                text(
                    f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}{not_null}{unique}"
                )
            )


async def watch(
    engine: AsyncEngine,
    metadata: Optional[MetaData] = None,
    use_identity: bool = False,
    include_tables: Optional[list] = None,
    exclude_tables: Optional[list] = None,
) -> None:
    """
    Cria ou altera tabelas para corresponder aos modelos SQLModel registrados.
    Funciona de forma assíncrona com AsyncEngine (SQLite ou PostgreSQL).

    Args:
        engine: AsyncEngine para conexão com o banco
        metadata: Metadata opcional (usa SQLModel.metadata por padrão)
        use_identity: Usar IDENTITY columns no PostgreSQL (padrão: False)
        include_tables: Lista de tabelas específicas para incluir (opcional)
        exclude_tables: Lista de tabelas para excluir (opcional)

    Raises:
        ValueError: Para dialetos não suportados ou nomes inválidos
    """
    try:
        # Usar metadata padrão do SQLModel se não for fornecido
        if metadata is None:
            metadata = SQLModel.metadata

        if not metadata.tables:
            warnings.warn(
                "Nenhuma tabela encontrada no metadata. Certifique-se de que os modelos foram importados."
            )
            return

        db_dialect = _get_dialect(engine)
        print(f"Usando o dialeto: {db_dialect}")
        print(f"Tabelas detectadas: {list(metadata.tables.keys())}")

        async with engine.begin() as conn:
            # Filtrar tabelas se necessário
            tables_to_process = list(metadata.tables.values())

            if include_tables:
                tables_to_process = [
                    t for t in tables_to_process if t.name in include_tables
                ]

            if exclude_tables:
                tables_to_process = [
                    t for t in tables_to_process if t.name not in exclude_tables
                ]

            # Ordenar tabelas para evitar problemas com foreign keys
            # Tabelas sem foreign keys primeiro
            def sort_key(table):
                has_fk = any(
                    col.foreign_keys for col in table.columns if col.foreign_keys
                )
                return (has_fk, table.name)

            tables_to_process.sort(key=sort_key)

            for table in tables_to_process:
                table_name = table.name

                # Validação básica do nome da tabela
                if not table_name or not table_name.isidentifier():
                    raise ValueError(f"Nome de tabela inválido: {table_name}")

                table_exists = await _table_exists(conn, table_name, db_dialect)

                if not table_exists:
                    await _create_table(conn, table, db_dialect, use_identity)
                    print(f"✓ Tabela criada: {table_name}")
                else:
                    existing_columns = await _get_existing_columns(
                        conn, table_name, db_dialect
                    )
                    if new_columns := [
                        col for col in table.columns if col.name not in existing_columns
                    ]:
                        await _add_missing_columns(
                            conn, table, existing_columns, db_dialect
                        )
                        print(
                            f"✓ Tabela atualizada: {table_name} ({len(new_columns)} novas colunas)"
                        )
                    else:
                        print(f"✓ Tabela verificada: {table_name} (sem alterações)")

    except Exception as e:
        print(f"❌ Erro durante a sincronização: {e}")
        raise
