import time

import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    password="nina_redis_dev_password",
    decode_responses=True,
)

start = time.time()
r.set("test-key", "ninaivalaigal")
val = r.get("test-key")
end = time.time()

print(f"Value: {val}")
print(f"Roundtrip Time: {(end - start) * 1000:.2f} ms")
