from pathlib import Path

from app.database.connection import get_pool

# Raíz del proyecto (app/database/initialize.py -> subir 2 niveles)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def initialize_database():
    pool = get_pool()

    schema_sql = (PROJECT_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    seed_sql = (PROJECT_ROOT / "sql" / "seed.sql").read_text(encoding="utf-8")

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Crear las tablas e índices que falten
            await conn.execute(schema_sql)
            # Insertar los datos iniciales que falten
            await conn.execute(seed_sql)

    print("Base de datos inicializada correctamente.")
