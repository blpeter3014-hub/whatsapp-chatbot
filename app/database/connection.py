import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None


async def connect_db():
    global pool

    if pool is not None:
        return pool

    if not DATABASE_URL:
        raise RuntimeError("No se encontró DATABASE_URL en el archivo .env")

    pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=10,
        command_timeout=30,
    )
    return pool


async def close_db():
    global pool

    if pool is not None:
        await pool.close()
        pool = None


def get_pool():
    if pool is None:
        raise RuntimeError("PostgreSQL no está conectado")
    return pool
