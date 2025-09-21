from __future__ import annotations

import hashlib
import json
import os
import sys

SNAPSHOT_FILE = os.getenv("POLICY_SNAPSHOT_FILE", "rbac/POLICY_SNAPSHOT.sha256")
ALLOW_ENV = os.getenv("ALLOW_POLICY_HASH_CHANGE", "false").lower() == "true"


def compute_policy_fingerprint() -> str:
    try:
        from rbac.policy import POLICY
    except Exception as e:
        print(f"error importing policy: {e}", file=sys.stderr)
        return ""
    items = sorted(
        [
            (r.name, res.name, sorted(a.name for a in acts))
            for (r, res), acts in POLICY.items()
        ]
    )
    blob = json.dumps(items, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def main():
    new_hash = compute_policy_fingerprint()
    if not new_hash:
        sys.exit(2)
    if not os.path.exists(SNAPSHOT_FILE):
        print(f"no snapshot at {SNAPSHOT_FILE}; creating one", file=sys.stderr)
        with open(SNAPSHOT_FILE, "w") as f:
            f.write(new_hash + "\n")
        sys.exit(0)
    with open(SNAPSHOT_FILE) as f:
        old_hash = f.read().strip()
    if new_hash != old_hash:
        if not ALLOW_ENV:
            print(
                "Policy hash changed. Set ALLOW_POLICY_HASH_CHANGE=true to proceed.",
                file=sys.stderr,
            )
            print(f"old={old_hash}\nnew={new_hash}", file=sys.stderr)
            sys.exit(1)
        else:
            with open(SNAPSHOT_FILE, "w") as f:
                f.write(new_hash + "\n")
            print("Snapshot updated.")
            sys.exit(0)


if __name__ == "__main__":
    main()
