from datetime import datetime


class BaseDevice:
    def __init__(self, device_id, device_type, room):
        self.device_id = device_id
        self.device_type = device_type
        self.room = room

        self.state = {}
        self.sensors = {}
        self.energy = {
            "current_watts": 0.0,
            "total_kwh": 0.0
        }

        # ✅ Manual / LLM override flag
        # When True, automation must NOT change this device
        self.manual_override = False

    def update_sensors(self):
        pass

    def update_state(self):
        """
        Hook for child devices if they need side-effects
        after a state change.
        """
        pass

    def apply_state(self, payload: dict, *, manual: bool = False):
        """
        Apply a rule / manual / LLM action payload to device state.

        If manual=True:
        - Marks this device as manually overridden
        - Automation will not fight user intent
        """
        if not payload:
            return payload

        # ✅ Mark manual override when explicitly requested
        if manual:
            self.manual_override = True

        for key, value in payload.items():
            self.state[key] = value

        # Allow subclasses to react to state change
        self.update_state()

        return payload

    def clear_manual_override(self):
        """
        Allows automation to resume control of this device.
        Can be called by a timer or UI action.
        """
        self.manual_override = False

    def update_energy(self, tick_seconds=5):
        self.energy["total_kwh"] += (
            self.energy["current_watts"] * tick_seconds
        ) / (1000 * 3600)

    def snapshot(self):
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "room": self.room,
            **self.sensors,
            **self.state,
            "current_watts": self.energy["current_watts"],
            "cumulative_energy": self.energy["total_kwh"],
            "manual_override": self.manual_override,
            "timestamp": datetime.utcnow().isoformat()
        }
