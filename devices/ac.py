print("LOADED AC FROM:", __file__)


from devices.base import BaseDevice
from devices.sensors import TemperatureSensor, MotionSensor


class AC(BaseDevice):
    def __init__(self, device_id, room):
        super().__init__(device_id, "AC", room)

        self.state = {
            "power": "OFF",
            "set_temperature": 24
        }

        self.temp_sensor = TemperatureSensor()
        self.motion_sensor = MotionSensor()

    def update_sensors(self):
        self.sensors["ambient_temperature"] = self.temp_sensor.update()
        self.sensors["occupancy"] = self.motion_sensor.update()

    def update_state(self):
        """
        Optional hook if AC-specific side effects are needed
        after state change.
        """
        pass

    def update_energy(self, tick_seconds=5):
        if self.state["power"] == "ON":
            delta = self.sensors["ambient_temperature"] - self.state["set_temperature"]
            self.energy["current_watts"] = 1200 + max(delta, 0) * 50
        else:
            self.energy["current_watts"] = 0

        super().update_energy(tick_seconds)
    def turn_on(self):
        self.state["power"] = "ON"

    def turn_off(self):
        self.state["power"] = "OFF"

    def set_temperature(self, value):
        if value is not None:
            self.state["set_temperature"] = int(value)
