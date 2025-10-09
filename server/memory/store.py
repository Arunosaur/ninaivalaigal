"""Store module."""


class InMemoryStore:
    """InMemoryStore storage implementation."""

    def __init__(self):
        """Initialize instance."""

        self.data = {"personal": {}, "team": {}, "org": {}}

    def write(self, user_id, record):
        """write function."""

        self.data[record.scope].setdefault(user_id, []).append(record.dict())
        return {"status": "ok", "record": record.dict()}

    def query(self, user_id, query):
        """query function."""

        return self.data.get(query.scope, {}).get(user_id, [])

    def share(self, user_id, share):
        """share function."""

        return {"status": "shared", "share": share.dict()}


memory_store = InMemoryStore()
