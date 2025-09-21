import os


def get_memory_store():
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if dsn:
        from memory.stores.postgres_store_new import PGConfig, PostgresStore

        return PostgresStore(PGConfig(dsn=dsn))
    from memory.stores.inmemory_store import InMemoryStore

    return InMemoryStore()
