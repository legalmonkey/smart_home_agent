import time
import threading

from ml.predictor import EnergyPredictor


class SimulatorEngine:
    def __init__(self, devices, rule_engine=None, tick_seconds=5):
        self.devices = devices
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
            # 1. Update device sensors and energy
            for device in self.devices.values():
                device.update_sensors()
                device.update_energy(self.tick_seconds)

            # 2. ML + rule evaluation
            if self.rule_engine:
                ml_snapshot = aggregate_state(
                    self.devices,
                    current_hour=self.current_hour
                )

                predicted_energy = self.predictor.predict(ml_snapshot)

                # Rule engine handles conflicts & priorities
                self.rule_engine.evaluate(
                    self.devices,
                    ml_prediction=predicted_energy
                )

            # 3. Advance simulated time
            self.current_hour = (self.current_hour + 1) % 24

            time.sleep(self.tick_seconds)


def aggregate_state(devices, current_hour):
    """
    Build an ML-compatible global state from device snapshots.
    This function makes NO assumptions about device internals.
    """

    # Collect snapshots once
    snapshots = {
        device_id: device.snapshot()
        for device_id, device in devices.items()
    }

    # Prefer AC snapshot for environmental context
    ref = snapshots.get("ac_1") or next(iter(snapshots.values()))

    return {
        # Time (system-level, not device-level)
        "hour_of_day": current_hour,

        # Environment (best-effort, safe defaults)
        "ambient_temperature": ref.get("ambient_temperature", 25),
        "occupancy": ref.get("occupancy", 0),

        # AC state
        "ac_power": snapshots.get("ac_1", {}).get("power") == "ON",
        "set_temperature": snapshots.get("ac_1", {}).get("set_temperature", 0),

        # ✅ Aggregate power safely from snapshots
        "total_current_load": sum(
            snap.get("power_draw", 0)
            for snap in snapshots.values()
        ),

        # Energy tracking
        "cumulative_energy": ref.get("cumulative_energy", 0)
    }
