import time
import threading

from ml.predictor import EnergyPredictor
from automation.rules import evaluate_automation
from automation.state_utils import aggregate_state
from automation.log_store import add_log

from enum import Enum


# ==============================
# CONTROL MODE
# ==============================
class ControlMode(Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


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
    def __init__(self, devices, rule_engine=None, tick_seconds=1):
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
        self.manual_payload = None

    # ==============================
    # MODE TOGGLES
    # ==============================
    def set_manual_mode(self, payload: dict):
        """
        payload format (from LLM):
        {
          "mode": "MANUAL",
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
        self.mode = ControlMode.MANUAL
        self.manual_payload = payload

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
    # ENGINE LIFECYCLE
    # ==============================
    def start(self):
        self.running = True
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()

    def loop(self):
        while self.running:

            print(
                f"\n========== DAY {self.current_day} | HOUR {self.current_hour} | MODE {self.mode.value} =========="
            )

            # ⏱️ Log simulation time
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

                # Device-level automation
                for device in self.devices.values():
                    evaluate_automation(
                        device,
                        current_hour=self.current_hour,
                        predicted_energy=predicted_energy
                    )

                # High-level rules (DECISION ONLY)
                actions = {}
                if self.rule_engine:
                    actions, _ = self.rule_engine.evaluate(
                        self.devices,
                        ml_prediction=predicted_energy
                    )

                # Apply final rule actions
                for device_id, payload in actions.items():
                    device = self.devices.get(device_id)
                    if device:
                        device.apply_state(payload)

            # ==================================================
            # 🧠 MANUAL MODE → LLM ACTIONS
            # ==================================================
            elif self.mode == ControlMode.MANUAL and self.manual_payload:

                for act in self.manual_payload.get("actions", []):
                    device_id = act["device_id"]
                    action = act["action"]
                    value = act.get("value")

                    device = self.devices.get(device_id)
                    if not device:
                        add_log({
                            "type": "manual_action",
                            "device_id": device_id,
                            "status": "FAILED",
                            "reason": "Device not found"
                        })
                        continue

                    try:
                        ActionMapper.apply(device, action, value)
                        add_log({
                            "type": "manual_action",
                            "device_id": device_id,
                            "action": action,
                            "status": "SUCCESS"
                        })
                    except Exception as e:
                        add_log({
                            "type": "manual_action",
                            "device_id": device_id,
                            "action": action,
                            "status": "FAILED",
                            "reason": str(e)
                        })

            # ==================================================
            # 🔋 Energy update AFTER final state
            # ==================================================
            for device in self.devices.values():
                device.update_energy(self.tick_seconds)

            # ⏭️ Advance deterministic time
            self.current_hour += 1
            if self.current_hour == 24:
                self.current_hour = 0
                self.current_day += 1

            time.sleep(self.tick_seconds)
