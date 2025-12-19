import requests

LLM_ACTIONS_URL = "https://backendllm-uoeo.onrender.com/actions"


def fetch_llm_actions(timeout=3):
    """
    Fetch manual actions from LLM backend.
    Expected response:
    {
      "actions": [
        {
          "device_id": "ac_1",
          "device_type": "AC",
          "room": "living_room",
          "action": "ON",
          "value": null
        }
      ]
    }
    """
    try:
        response = requests.get(LLM_ACTIONS_URL, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "actions": []
        }
