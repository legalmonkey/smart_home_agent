import time
import threading

from ml.predictor import EnergyPredictor
from automation.rules import evaluate_automation
from automation.state_utils import aggregate_state   # assuming this exists


class SimulatorEngine:
    def __init__(self, devices, rule_engine=None, tick_seconds=5):
        self.devices = devices          # dict: device_id -> device
        self.rule_engine = rule_engine
        self.tick_seconds = tick_seconds
        self.running = False

        # ML predictor
        self.predictor = EnergyPredictor()

        # System-level simulated clock
        self.current_hour = 12  # start at noon

    def start(self):
        self.running = True
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()

    def loop(self):
        while self.running:

            # 1️⃣ Update sensors
            for device in self.devices.values():
                device.update_sensors()

            # 2️⃣ Build ML snapshot BEFORE automation
            ml_snapshot = aggregate_state(
                self.devices,
                current_hour=self.current_hour
            )

            predicted_energy = self.predictor.predict(ml_snapshot)

            # 3️⃣ Automation (ML-aware, emits events)
            for device in self.devices.values():
                evaluate_automation(
                    device,
                    current_hour=self.current_hour,
                    predicted_energy=predicted_energy
                )

            # 4️⃣ Energy update (reflects automation decisions)
            for device in self.devices.values():
                device.update_energy(self.tick_seconds)

            # 5️⃣ (Optional) high-level rule engine
            if self.rule_engine:
                self.rule_engine.evaluate(
                    self.devices,
                    ml_prediction=predicted_energy
                )

            # 6️⃣ Advance simulated time
            self.current_hour = (self.current_hour + 1) % 24

            time.sleep(self.tick_seconds)
