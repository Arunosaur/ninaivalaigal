from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class RetentionPolicy:
    days: int  # 0 for immediate discard


class RetentionExecutor:
    def __init__(
        self,
        tier_policy: dict[int, RetentionPolicy],
        query_expired: Callable[[datetime, int], Iterable[int]],
        delete_ids: Callable[[Iterable[int]], int],
        metrics: Callable[[str, dict], None] | None = None,
        page_size: int = 1000,
    ):
        self.tier_policy = tier_policy
        self.query_expired = query_expired
        self.delete_ids = delete_ids
        self.metrics = metrics or (lambda name, tags: None)
        self.page_size = page_size

    def run(self, tier: int, now: datetime | None = None, dry_run: bool = False) -> int:
        now = now or datetime.utcnow()
        policy = self.tier_policy.get(tier)
        if not policy or policy.days < 0:
            return 0
        cutoff = now - timedelta(days=policy.days)
        total = 0
        while True:
            ids = list(self.query_expired(cutoff, self.page_size))
            if not ids:
                break
            if dry_run:
                self.metrics("retention.dry_run", {"tier": tier, "count": len(ids)})
                break
            deleted = self.delete_ids(ids)
            total += deleted
            self.metrics("retention.deleted", {"tier": tier, "count": deleted})
            if deleted < len(ids):
                break
        return total
