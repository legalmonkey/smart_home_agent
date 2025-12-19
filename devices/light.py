from devices.base import BaseDevice


class Light(BaseDevice):
    def __init__(self, device_id, room):
        super().__init__(device_id, "Light", room)

        # 🔑 REQUIRED FOR AUTOMATION
        self.sensors = {
            "occupancy": False
        }

        self.state = {
            "power": "OFF"
        }

    def update_energy(self, tick_seconds=5):
        self.energy["current_watts"] = 10 if self.state["power"] == "ON" else 0
        super().update_energy(tick_seconds)
