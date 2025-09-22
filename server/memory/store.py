class InMemoryStore:
    def __init__(self):
        self.data = {"personal": {}, "team": {}, "org": {}}

    def write(self, user_id, record):
        self.data[record.scope].setdefault(user_id, []).append(record.dict())
        return {"status": "ok", "record": record.dict()}

    def query(self, user_id, query):
        return self.data.get(query.scope, {}).get(user_id, [])

    def share(self, user_id, share):
        return {"status": "shared", "share": share.dict()}


memory_store = InMemoryStore()
