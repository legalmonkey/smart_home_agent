import random

class TemperatureSensor:
    def __init__(self, value=28.0):
        self.value = value

    def update(self):
        self.value += random.uniform(-0.3, 0.4)
        return round(self.value, 2)

class MotionSensor:
    def update(self):
        return random.choice([True, False])
