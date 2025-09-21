import json
import os
import pathlib
import shutil
import subprocess
import sys

SCRIPT = "scripts/multipart_policy_snapshot_gate.py"

def run(py, *args, cwd=None, env=None):
    return subprocess.run([py, *args], cwd=cwd, env=env or os.environ.copy(), capture_output=True, text=True)

def test_policy_gate_creates_and_updates_baseline(tmp_path):
    repo = tmp_path
    (repo / "scripts").mkdir()
    # Copy the gate script from the project root (pytest runs at project root)
    src = pathlib.Path(SCRIPT)
    assert src.exists(), "gate script must exist"
    shutil.copy2(src, repo / "scripts" / "multipart_policy_snapshot_gate.py")

    py = sys.executable

    r1 = run(py, "scripts/multipart_policy_snapshot_gate.py", cwd=repo)
    assert r1.returncode != 0
    baseline = repo / "multipart_policy_baseline.json"
    assert baseline.exists()

    r2 = run(py, "scripts/multipart_policy_snapshot_gate.py", cwd=repo)
    assert r2.returncode == 0

    env = os.environ.copy()
    env["UPLOAD_LIMIT"] = "20MB"
    r3 = run(py, "scripts/multipart_policy_snapshot_gate.py", cwd=repo, env=env)
    assert r3.returncode != 0

    (repo / ".multipart_changes_approved").write_text("ok")
    r4 = run(py, "scripts/multipart_policy_snapshot_gate.py", cwd=repo, env=env)
    assert r4.returncode == 0
    data = json.loads(baseline.read_text())
    assert "hash" in data
