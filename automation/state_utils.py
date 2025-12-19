# automation/state_utils.py

def aggregate_state(devices, current_hour: int):
    """
    Aggregate device state into a single ML-friendly snapshot.
    """

    snapshots = {
        device_id: d.snapshot()
        for device_id, d in devices.items()
    }

    # Prefer AC for environmental context
    ref = snapshots.get("ac_1") or next(iter(snapshots.values()))

    return {
        "hour_of_day": current_hour,
        "ambient_temperature": ref.get("ambient_temperature", 25),
        "occupancy": ref.get("occupancy", 0),
        "ac_power": snapshots.get("ac_1", {}).get("power") == "ON",
        "set_temperature": snapshots.get("ac_1", {}).get("set_temperature", 0),
        "total_current_load": sum(
            snap.get("power_draw", 0)
            for snap in snapshots.values()
        ),
        "cumulative_energy": ref.get("cumulative_energy", 0),
    }
