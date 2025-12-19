# automation/rules.py
from .config import automation_config
from automation.time_utils import get_time_of_day_from_hour
from automation.decision_emitter import emit_decision


def _log_automation(device, current_hour):
    print(
        f"[AUTOMATION] {device.device_id} | "
        f"type={device.device_type} | "
        f"hour={current_hour} | "
        f"temp={device.sensors.get('ambient_temperature')} | "
        f"occ={device.sensors.get('occupancy')} | "
        f"state={device.state.get('power')}"
    )


def build_explanation(
    device_type: str,
    action: str,
    *,
    time_of_day: str,
    occupied: bool | None = None,
    predicted_energy: float | None = None,
    ml_blocked: bool = False
) -> str:
    """
    Generate a human-readable explanation that matches
    the exact rule that fired.
    """

    # ---------- AC ----------
    if device_type == "AC":
        if ml_blocked:
            return "AC turned OFF due to high predicted energy usage"

        if action == "ON":
            return (
                f"AC turned ON because the room is occupied "
                f"and the temperature exceeded the {time_of_day} threshold"
            )

        return "AC turned OFF because the room is unoccupied or sufficiently cool"

    # ---------- FAN ----------
    if device_type == "Fan":
        if action == "ON":
            return f"Fan turned ON because the room is occupied during {time_of_day}"
        return "Fan turned OFF because the room is unoccupied or it is night"

    # ---------- LIGHT ----------
    if device_type == "Light":
        if action == "ON":
            return f"Light turned ON because the room is occupied at {time_of_day}"
        return "Light turned OFF because it is daytime or the room is empty"

    return "Automation rule applied"


def evaluate_automation(device, current_hour: int, predicted_energy: float | None = None):

    # Respect manual / LLM override
    if getattr(device, "manual_override", False):
        return False

    time_of_day = get_time_of_day_from_hour(current_hour)

    # ---------- AC ----------
    if device.device_type == "AC":
        temp = device.sensors.get("ambient_temperature")
        occupied = device.sensors.get("occupancy")

        if temp is None or occupied is None:
            return False

        profile = automation_config["ac_thresholds"].get(time_of_day)
        if not profile:
            return False

        on_temp = profile["on_temp"]
        off_temp = profile["off_temp"]

        ml_policy = automation_config.get("ml_policy", {})
        ml_adjusted = False

        if ml_policy.get("enabled") and predicted_energy is not None:
            limits = ml_policy["energy_limits"]
            adjust = ml_policy["ac_adjustment"]

            if predicted_energy >= limits["high"]:
                on_temp += adjust["high_energy_delta"]
                ml_adjusted = True
            elif predicted_energy <= limits["low"]:
                on_temp += adjust["low_energy_delta"]

        if occupied and temp >= on_temp:
            if device.state.get("power") != "ON":
                device.apply_state({"power": "ON"})
                _log_automation(device, current_hour)

                emit_decision({
                    "device_id": device.device_id,
                    "device_type": device.device_type,
                    "hour": current_hour,
                    "time_of_day": time_of_day,
                    "sensors": device.sensors,
                    "new_state": device.state,
                    "predicted_energy": predicted_energy,
                    "action_taken": True,
                    "explanation": build_explanation(
                        "AC",
                        "ON",
                        time_of_day=time_of_day,
                        occupied=occupied,
                        predicted_energy=predicted_energy
                    )
                })

                return True

        if (not occupied) or temp <= off_temp:
            if device.state.get("power") != "OFF":
                device.apply_state({"power": "OFF"})
                _log_automation(device, current_hour)

                emit_decision({
                    "device_id": device.device_id,
                    "device_type": device.device_type,
                    "hour": current_hour,
                    "time_of_day": time_of_day,
                    "sensors": device.sensors,
                    "new_state": device.state,
                    "predicted_energy": predicted_energy,
                    "action_taken": True,
                    "explanation": build_explanation(
                        "AC",
                        "OFF",
                        time_of_day=time_of_day,
                        occupied=occupied,
                        predicted_energy=predicted_energy,
                        ml_blocked=ml_adjusted
                    )
                })

                return True

       # ---------- FAN (TIME-AWARE) ----------
    elif device.device_type == "Fan":
        rules = automation_config.get("fan_rules", {}).get(time_of_day)

        occupied = device.sensors.get("occupancy", False)

        # ✅ FAIL-SAFE DEFAULT:
        # If rules or use_occupancy not defined, fall back to occupancy-based control
        if rules is None:
            desired = "ON" if occupied else "OFF"
        else:
            if rules.get("use_occupancy", True):
                desired = "ON" if occupied else "OFF"
            else:
                desired = "OFF"

        if device.state.get("power") != desired:
            device.apply_state({"power": desired})
            _log_automation(device, current_hour)

            emit_decision({
                "device_id": device.device_id,
                "device_type": device.device_type,
                "hour": current_hour,
                "time_of_day": time_of_day,
                "sensors": device.sensors,
                "new_state": device.state,
                "predicted_energy": predicted_energy,
                "action_taken": True,
                "explanation": build_explanation(
                    "Fan",
                    desired,
                    time_of_day=time_of_day,
                    occupied=occupied
                )
            })

            return True


    # ---------- LIGHT (TIME + ML AWARE) ----------
    elif device.device_type == "Light":
        rules = automation_config["light_rules"].get(time_of_day, {})
        occupied = device.sensors.get("occupancy", False)

        allow_light = rules.get("allow", False)

        ml_light = automation_config.get("ml_light_policy", {})
        if (
            ml_light.get("enabled")
            and predicted_energy is not None
            and predicted_energy >= ml_light["high_energy_cutoff"]
        ):
            allow_light = False

        desired = "ON" if (allow_light and occupied) else "OFF"

        if device.state.get("power") != desired:
            device.apply_state({"power": desired})
            _log_automation(device, current_hour)

            emit_decision({
                "device_id": device.device_id,
                "device_type": device.device_type,
                "hour": current_hour,
                "time_of_day": time_of_day,
                "sensors": device.sensors,
                "new_state": device.state,
                "predicted_energy": predicted_energy,
                "action_taken": True,
                "explanation": build_explanation(
                    "Light",
                    desired,
                    time_of_day=time_of_day,
                    occupied=occupied,
                    predicted_energy=predicted_energy
                )
            })

            return True

    return False
