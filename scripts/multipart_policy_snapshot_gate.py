import hashlib
import json
import os
import sys

BASELINE_FILE = "multipart_policy_baseline.json"
APPROVAL_FILE = ".multipart_changes_approved"

def compute_snapshot():
    config = {"UPLOAD_LIMIT": os.getenv("UPLOAD_LIMIT", "10MB")}
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()

def main():
    snapshot = compute_snapshot()
    if not os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, "w") as f:
            json.dump({"hash": snapshot}, f)
        print("Baseline created. Commit this file.")
        sys.exit(1)
    with open(BASELINE_FILE) as f:
        baseline = json.load(f)
    if baseline["hash"] != snapshot:
        if os.path.exists(APPROVAL_FILE):
            with open(BASELINE_FILE, "w") as f:
                json.dump({"hash": snapshot}, f)
            print("Baseline updated with approval.")
            sys.exit(0)
        print("Policy drift detected! Approval required.")
        sys.exit(1)
    print("Policy unchanged.")
    sys.exit(0)

if __name__ == "__main__":
    main()
