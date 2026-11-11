from app.database.connection import get_pool

# Caché global del proceso (vive en la RAM de Python)
COMPANY_CACHE = {}


async def load_company_cache():
    """Carga la información activa desde PostgreSQL hacia la RAM."""
    pool = get_pool()
    rows = await pool.fetch("""
        SELECT knowledge_key, category, content
        FROM company_knowledge
        WHERE is_active = TRUE
    """)

    COMPANY_CACHE.clear()
    for row in rows:
        COMPANY_CACHE[row["knowledge_key"]] = {
            "category": row["category"],
            "content": row["content"],
        }

    print(f"Caché cargado: {len(COMPANY_CACHE)} registros.")
    return COMPANY_CACHE


def get_company_context():
    """Devuelve la información que ya está disponible en RAM."""
    return COMPANY_CACHE.copy()
