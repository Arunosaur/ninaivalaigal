from datetime import datetime

from server.security.retention.executor import RetentionExecutor, RetentionPolicy


def test_retention_deletes_in_pages():
    store = list(range(1, 2501))

    def query_expired(cutoff, page_size):
        if store:
            batch = store[:page_size]
            del store[:page_size]
            return batch
        return []

    deleted_ids = []
    def delete_ids(ids):
        deleted_ids.extend(ids)
        return len(ids)

    metrics = []
    def record(name, tags):
        metrics.append((name, tags))

    rex = RetentionExecutor(
        {2: RetentionPolicy(days=365)},
        query_expired=query_expired,
        delete_ids=delete_ids,
        metrics=record,
        page_size=1000,
    )
    total = rex.run(2, now=datetime(2025,1,1), dry_run=False)
    assert total == 2500
