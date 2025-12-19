from datetime import datetime
import random


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

        # Manual / LLM override flag
        self.manual_override = False

    def update_sensors(self):
        """
        Simulate realistic sensor dynamics.
        This enables Fan and Light automation to work correctly.
        """

        # -------- OCCUPANCY DYNAMICS --------
        if "occupancy" in self.sensors:
            # 15% chance per tick to flip occupancy
            if random.random() < 0.15:
                self.sensors["occupancy"] = not self.sensors["occupancy"]

        # -------- AMBIENT TEMPERATURE DRIFT --------
        if "ambient_temperature" in self.sensors:
            # Small random walk
            self.sensors["ambient_temperature"] += random.uniform(-0.3, 0.4)

            # Clamp to realistic bounds
            self.sensors["ambient_temperature"] = max(
                16.0, min(40.0, self.sensors["ambient_temperature"])
            )

    def update_state(self):
        """
        Hook for child devices if they need side-effects
        after a state change.
        """
        pass

    def apply_state(self, payload: dict, *, manual: bool = False):
        """
        Apply a rule / manual / LLM action payload to device state.
        """
        if not payload:
            return payload

        if manual:
            self.manual_override = True

        for key, value in payload.items():
            self.state[key] = value

        self.update_state()
        return payload

    def clear_manual_override(self):
        """
        Allows automation to resume control of this device.
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
