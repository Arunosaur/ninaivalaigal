import os
def get_memory_store():
    dsn = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if dsn:
        from server.memory.stores.postgres_store import PostgresStore, PGConfig
        return PostgresStore(PGConfig(dsn=dsn))
    from server.memory.stores.inmemory_store import InMemoryStore
    return InMemoryStore()
