from fastapi import APIRouter
from datetime import datetime

# In-memory store for automation events
AUTOMATION_EVENTS = []


def attach_routes(router, devices, rule_engine, predictor, engine):

    # ==============================
    # DEVICE STATE
    # ==============================
    @router.get("/state")
    def get_state():
        return {
            device_id: d.snapshot()
            for device_id, d in devices.items()
        }

    # ==============================
    # DECISION PREVIEW (AUTO MODE)
    # ==============================
    @router.get("/decision")
    def get_decision():
        """
        Dry-run decision endpoint.
        Does NOT affect simulator state.
        Always reflects AUTO logic.
        """

        snapshots = {
            device_id: d.snapshot()
            for device_id, d in devices.items()
        }

        # Real-world clock for API preview
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
            "mode": "AUTO_PREVIEW",
            "predicted_energy": round(predicted_energy, 3),
            "actions": actions,
            "explanations": explanations
        }

    # ==============================
    # 🔀 MODE TOGGLE ENDPOINTS
    # ==============================
    @router.post("/mode/manual")
    def activate_manual_mode(payload: dict):
        """
        Activates MANUAL mode.

        Expected payload (from LLM):
        {
          "mode": "MANUAL",
          "actions": [
            {
              "device_id": "ac_1",
              "device_type": "AC",
              "room": "living_room",
              "action": "ON",
              "value": null
            }
          ]
        }
        """
        engine.set_manual_mode(payload)
        return {
            "status": "MANUAL mode activated",
            "active_mode": "MANUAL"
        }

    @router.post("/mode/auto")
    def activate_auto_mode():
        """
        Switches back to AUTO mode.
        """
        engine.set_auto_mode()
        return {
            "status": "AUTO mode activated",
            "active_mode": "AUTO"
        }

    @router.get("/mode")
    def get_current_mode():
        """
        Returns current simulator control mode.
        """
        return {
            "active_mode": engine.mode.value
        }

    # ==============================
    # AUTOMATION EVENTS STREAM
    # ==============================
    @router.post("/automation-events")
    def receive_automation_event(event: dict):
        """
        Receives low-level automation decision JSON
        streamed from rule engine or simulator.
        """
        AUTOMATION_EVENTS.append(event)
        return {"status": "received"}

    @router.get("/automation-events")
    def list_automation_events():
        return AUTOMATION_EVENTS
