import time
import threading

from ml.predictor import EnergyPredictor
from automation.rules import evaluate_automation
from automation.state_utils import aggregate_state


class SimulatorEngine:
    def __init__(self, devices, rule_engine=None, tick_seconds=1):
        self.devices = devices          # dict: device_id -> device
        self.rule_engine = rule_engine
        self.tick_seconds = tick_seconds
        self.running = False

        # ML predictor
        self.predictor = EnergyPredictor()

        # 🔑 Deterministic simulated clock
        self.current_hour = 0
        self.current_day = 1

    def start(self):
        self.running = True
        thread = threading.Thread(target=self.loop, daemon=True)
        thread.start()

    def loop(self):
        while self.running:

            # ===== SIMULATION HEADER =====
            print(
                f"\n========== DAY {self.current_day} | HOUR {self.current_hour} =========="
            )

            # 1️⃣ Update sensors (occupancy, temperature, etc.)
            for device in self.devices.values():
                device.update_sensors()

            # 2️⃣ Build ML snapshot (ADD DAY → fixes duplicate predictions)
            ml_snapshot = aggregate_state(
                self.devices,
                current_hour=self.current_hour
            )


            predicted_energy = self.predictor.predict(ml_snapshot)
            print(f"[ML] Predicted energy usage: {predicted_energy:.3f}")

            # 3️⃣ Device-level automation (Fan / Light / AC)
            for device in self.devices.values():
                evaluate_automation(
                    device,
                    current_hour=self.current_hour,
                    predicted_energy=predicted_energy
                )

            # 4️⃣ High-level rule engine (DECISION ONLY)
            actions = {}
            if self.rule_engine:
                actions, _ = self.rule_engine.evaluate(
                    self.devices,
                    ml_prediction=predicted_energy
                )

            # 5️⃣ APPLY FINAL ACTIONS (single source of truth)
            for device_id, payload in actions.items():
                device = self.devices.get(device_id)
                if device:
                    device.apply_state(payload)

            # 6️⃣ Update energy AFTER final state is settled
            for device in self.devices.values():
                device.update_energy(self.tick_seconds)

            # 7️⃣ Advance deterministic simulation time
            self.current_hour += 1
            if self.current_hour == 24:
                self.current_hour = 0
                self.current_day += 1

            time.sleep(self.tick_seconds)
