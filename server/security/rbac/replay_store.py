"""replay store module."""

import os
import time
from collections import OrderedDict

TTL = int(os.getenv("JWT_REPLAY_TTL", "300"))

_seen = OrderedDict()


def seen_before(jti: str) -> bool:
    """Check if JWT token ID has been seen before to prevent replay attacks."""
    now = time.time()
    if jti in _seen and now - _seen[jti] < TTL:
        return True
    _seen[jti] = now
    # cleanup expired
    for k in list(_seen.keys()):
        if now - _seen[k] > TTL:
            _seen.pop(k, None)
    return False
