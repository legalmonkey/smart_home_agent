from collections import deque
from datetime import datetime

# Keep last N log entries (avoid memory blow-up)
AUTOMATION_LOGS = deque(maxlen=1000)


def add_log(entry: dict):
    entry["timestamp"] = datetime.utcnow().isoformat()
    AUTOMATION_LOGS.append(entry)


def get_logs():
    return list(AUTOMATION_LOGS)
