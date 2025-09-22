from prometheus_client import Counter

jwt_replay_total = Counter(
    "jwt_replay_total", "Total number of detected JWT replay attempts"
)
