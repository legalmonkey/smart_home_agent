def aggregate_state(devices, current_hour: int, day: int):
    print("aggregate_state called with day =", day)

    snapshots = {
        device_id: device.snapshot()
        for device_id, device in devices.items()
    }

    ref = snapshots.get("ac_1") or next(iter(snapshots.values()))

    return {
        "day": day,
        "hour_of_day": current_hour,
        "ambient_temperature": ref.get("ambient_temperature", 25),
        "occupancy": ref.get("occupancy", 0),
        "ac_power": snapshots.get("ac_1", {}).get("power") == "ON",
        "set_temperature": snapshots.get("ac_1", {}).get("set_temperature", 0),
        "total_current_load": sum(
            snap.get("current_watts", 0)
            for snap in snapshots.values()
        ),
        "cumulative_energy": ref.get("cumulative_energy", 0),
    }
