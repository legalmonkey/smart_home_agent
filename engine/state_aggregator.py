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
        # Time (system-level, simulated)
        "hour_of_day": current_hour,

        # Environment (safe defaults)
        "ambient_temperature": ref.get("ambient_temperature", 25),
        "occupancy": ref.get("occupancy", 0),

        # AC state
        "ac_power": snapshots.get("ac_1", {}).get("power") == "ON",
        "set_temperature": snapshots.get("ac_1", {}).get("set_temperature", 0),

        # Aggregate electrical load (FIXED KEY)
        "total_current_load": sum(
            snap.get("current_watts", 0)
            for snap in snapshots.values()
        ),

        # Energy tracking
        "cumulative_energy": ref.get("cumulative_energy", 0)
    }
