import time
import threading
from enum import Enum
import requests

from ml.predictor import EnergyPredictor
from automation.rules import evaluate_automation
from automation.state_utils import aggregate_state
from automation.log_store import add_log


# ==============================
# CONTROL MODE
# ==============================
class ControlMode(Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


# ==============================
# LLM ACTION FETCHER
# ==============================
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
        add_log({
            "type": "llm_error",
            "error": str(e)
        })
        return {"actions": []}


# ==============================
# ACTION MAPPER (LLM → DEVICE)
# ==============================
class ActionMapper:
    @staticmethod
    def apply(device, action: str, value):
        action = action.upper()

        if device.__class__.__name__ == "AC":
            if action == "ON":
                device.turn_on()
            elif action == "OFF":
                device.turn_off()
            elif action == "SET_TEMPERATURE":
                device.set_temperature(value)
            else:
                raise ValueError("Unsupported AC action")

        elif device.__class__.__name__ == "Light":
            if action == "ON":
                device.turn_on()
            elif action == "OFF":
                device.turn_off()
            elif action == "SET_BRIGHTNESS":
                device.set_brightness(value)
            else:
                raise ValueError("Unsupported Light action")

        elif device.__class__.__name__ == "Fan":
            if action == "ON":
                device.turn_on()
            elif action == "OFF":
                device.turn_off()
            elif action == "SET_SPEED":
                device.set_speed(value)
            else:
                raise ValueError("Unsupported Fan action")

        else:
            raise ValueError("Unknown device type")


# ==============================
# SIMULATOR ENGINE
# ==============================
class SimulatorEngine:
    """
    Render-safe, deterministic simulator engine.
    """

    # 🔒 Cold-start guard
    _start_lock = threading.Lock()
    _started = False

    def __init__(self, devices, rule_engine=None, tick_seconds=15):
        self.devices = devices
        self.rule_engine = rule_engine
        self.tick_seconds = tick_seconds
        self.running = False

        # ML predictor
        self.predictor = EnergyPredictor()

        # Deterministic simulated clock
        self.current_hour = 0
        self.current_day = 1

        # 🔀 MODE CONTROL
        self.mode = ControlMode.AUTO
        self.manual_payload = None  # preserved (API compatibility)

    # ==============================
    # MODE TOGGLES
    # ==============================
    def set_manual_mode(self, payload: dict = None):
        self.mode = ControlMode.MANUAL
        self.manual_payload = payload  # optional, preserved

        add_log({
            "type": "mode_change",
            "mode": "MANUAL"
        })

    def set_auto_mode(self):
        self.mode = ControlMode.AUTO
        self.manual_payload = None

        add_log({
            "type": "mode_change",
            "mode": "AUTO"
        })

    # ==============================
    # ENGINE START
    # ==============================
    def start(self):
        with SimulatorEngine._start_lock:
            if SimulatorEngine._started:
                return

            self.running = True
            thread = threading.Thread(target=self.loop, daemon=True)
            thread.start()

            SimulatorEngine._started = True

    # ==============================
    # MAIN LOOP
    # ==============================
    def loop(self):

        time.sleep(1)  # allow app + ML to initialize

        while self.running:

            print(
                f"\n========== DAY {self.current_day} | "
                f"HOUR {self.current_hour} | "
                f"MODE {self.mode.value} =========="
            )

            # ⏱️ Log time
            add_log({
                "type": "time",
                "day": self.current_day,
                "hour": self.current_hour
            })

            # 1️⃣ Update sensors
            for device in self.devices.values():
                device.update_sensors()

            # 2️⃣ ML snapshot
            ml_snapshot = aggregate_state(
                self.devices,
                current_hour=self.current_hour
            )

            predicted_energy = self.predictor.predict(ml_snapshot)
            print(f"[ML] Predicted energy usage: {predicted_energy:.3f}")

            add_log({
                "type": "ml",
                "day": self.current_day,
                "hour": self.current_hour,
                "predicted_energy": round(predicted_energy, 3)
            })

            # ==================================================
            # 🔁 AUTO MODE → RULE ENGINE + ML
            # ==================================================
            if self.mode == ControlMode.AUTO:

                for device in self.devices.values():
                    evaluate_automation(
                        device,
                        current_hour=self.current_hour,
                        predicted_energy=predicted_energy
                    )

                actions = {}
                if self.rule_engine:
                    actions, _ = self.rule_engine.evaluate(
                        self.devices,
                        ml_prediction=predicted_energy
                    )

                for device_id, payload in actions.items():
                    device = self.devices.get(device_id)
                    if device:
                        device.apply_state(payload)

            # ==================================================
            # 🧠 MANUAL MODE → LLM ACTIONS (REMOTE)
            # ==================================================
            elif self.mode == ControlMode.MANUAL:

                llm_payload = fetch_llm_actions()
                actions = llm_payload.get("actions", [])

                for act in actions:
                    device_id = act["device_id"]
                    action = act["action"]
                    value = act.get("value")

                    device = self.devices.get(device_id)
                    if not device:
                        add_log({
                            "type": "manual_action",
                            "device_id": device_id,
                            "status": "FAILED",
                            "reason": "Device not found",
                            "source": "LLM"
                        })
                        continue

                    try:
                        ActionMapper.apply(device, action, value)
                        add_log({
                            "type": "manual_action",
                            "device_id": device_id,
                            "action": action,
                            "status": "SUCCESS",
                            "source": "LLM"
                        })
                    except Exception as e:
                        add_log({
                            "type": "manual_action",
                            "device_id": device_id,
                            "action": action,
                            "status": "FAILED",
                            "reason": str(e),
                            "source": "LLM"
                        })

            # ==================================================
            # 🔋 ENERGY UPDATE
            # ==================================================
            for device in self.devices.values():
                device.update_energy(self.tick_seconds)

            # ⏭️ Advance deterministic time
            self.current_hour += 1
            if self.current_hour == 24:
                self.current_hour = 0
                self.current_day += 1

            time.sleep(self.tick_seconds)
