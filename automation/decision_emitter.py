import os
import requests
from datetime import datetime

AUTOMATION_ENDPOINT = os.getenv(
    "AUTOMATION_ENDPOINT",
    "http://localhost:8000/automation-events"
)


def emit_decision(decision: dict):
    decision["timestamp"] = datetime.utcnow().isoformat()

    try:
        requests.post(AUTOMATION_ENDPOINT, json=decision, timeout=1.0)
    except Exception as e:
        print("[WARN] Automation event not delivered:", e)
