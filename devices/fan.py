from devices.base import BaseDevice


class Fan(BaseDevice):
    def __init__(self, device_id, room):
        super().__init__(device_id, "Fan", room)
        self.state = {"power": "OFF", "speed": 1}

    def update_energy(self, tick_seconds=5):
        if self.state["power"] == "ON":
            self.energy["current_watts"] = 40 + self.state["speed"] * 20
        else:
            self.energy["current_watts"] = 0

        super().update_energy(tick_seconds)
