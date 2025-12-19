import requests
from datetime import datetime

AUTOMATION_ENDPOINT = "http://localhost:8000/automation-events"


def emit_decision(decision: dict):
    decision["timestamp"] = datetime.utcnow().isoformat()

    try:
        requests.post(AUTOMATION_ENDPOINT, json=decision, timeout=0.5)
    except Exception as e:
        # Do NOT crash simulator if API is down
        print("[WARN] Automation event not delivered:", e)
