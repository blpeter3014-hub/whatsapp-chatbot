import asyncio

from app.database.connection import close_db, connect_db, get_pool
from app.database.initialize import initialize_database


async def main():
    try:
        await connect_db()
        await initialize_database()

        pool = get_pool()
        async with pool.acquire() as conn:
            tablas = await conn.fetch("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            print("\nTablas encontradas:")
            for tabla in tablas:
                print("-", tabla["table_name"])

            conocimiento = await conn.fetch(
                "SELECT knowledge_key, content FROM company_knowledge;"
            )
            print("\nConocimiento del asistente:")
            for item in conocimiento:
                print(f"{item['knowledge_key']}: {item['content']}")

    except Exception as e:
        print("\nError durante la prueba:", e)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
