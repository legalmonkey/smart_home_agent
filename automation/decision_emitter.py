from automation.log_store import add_log
import requests
import os

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


def emit_decision(payload: dict):
    # Log locally
    add_log({
        "type": "automation",
        **payload
    })

    # Send to API endpoint
    try:
        requests.post(
            f"{BASE_URL}/automation-events",
            json=payload,
            timeout=2
        )
    except Exception as e:
        print("[WARN] Automation event not delivered:", e)
