import glob
import hashlib


def hash_migrations():
    paths = sorted(glob.glob("alembic/versions/*.py") + glob.glob("server/memory/db/migrations/*.sql"))
    h = hashlib.sha256()
    if not paths: return "no-migrations"
    for p in paths:
        with open(p, "rb") as f:
            h.update(p.encode("utf-8")); h.update(f.read())
    return h.hexdigest()
if __name__ == "__main__":
    print(hash_migrations())
