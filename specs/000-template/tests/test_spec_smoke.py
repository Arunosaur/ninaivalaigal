import os, time, httpx

BASE = os.getenv("API_BASE", "http://localhost:13370")

def test_health():
    r = httpx.get(f"{BASE}/health", timeout=10)
    assert r.status_code == 200

def test_memory_roundtrip():
    write = httpx.post(f"{BASE}/memory/remember",
                       json={"text": "spec smoke", "metadata":{"t":"spec"}},
                       timeout=15)
    assert write.status_code == 200
    time.sleep(0.5)
    read = httpx.get(f"{BASE}/memory/recall", params={"q":"spec","k":5}, timeout=15)
    assert read.status_code == 200
