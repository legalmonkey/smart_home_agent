from fastapi import APIRouter
from datetime import datetime

# In-memory store for automation events
AUTOMATION_EVENTS = []


def attach_routes(router, devices, rule_engine, predictor):

    @router.get("/state")
    def get_state():
        return {
            device_id: d.snapshot()
            for device_id, d in devices.items()
        }

    @router.get("/decision")
    def get_decision():
        snapshots = {
            device_id: d.snapshot()
            for device_id, d in devices.items()
        }

        # Use real clock time for API (not simulator time)
        current_hour = datetime.now().hour

        # Prefer AC snapshot for environment context
        ref = snapshots.get("ac_1") or next(iter(snapshots.values()))

        ml_snapshot = {
            "hour_of_day": current_hour,
            "ambient_temperature": ref.get("ambient_temperature", 25),
            "occupancy": ref.get("occupancy", 0),
            "ac_power": snapshots.get("ac_1", {}).get("power") == "ON",
            "set_temperature": snapshots.get("ac_1", {}).get("set_temperature", 0),
            "total_current_load": sum(
                snap.get("power_draw", 0)
                for snap in snapshots.values()
            ),
            "cumulative_energy": ref.get("cumulative_energy", 0)
        }

        predicted_energy = predictor.predict(ml_snapshot)

        actions, explanations = rule_engine.evaluate(
            devices,
            ml_prediction=predicted_energy
        )

        return {
            "predicted_energy": round(predicted_energy, 3),
            "actions": actions,
            "explanations": explanations
        }

    # ---------- NEW: AUTOMATION EVENTS STREAM ----------
    @router.post("/automation-events")
    def receive_automation_event(event: dict):
        """
        Receives low-level automation decision JSON
        streamed from the rule engine.
        """
        AUTOMATION_EVENTS.append(event)
        return {"status": "received"}

    # (Optional but useful)
    @router.get("/automation-events")
    def list_automation_events():
        return AUTOMATION_EVENTS
