def create_action(action_block, devices):
    action_type = action_block["action"]
    payload = action_block.get("payload", {})

    def action(snapshot):
        device_id = snapshot["device_id"]
        device = devices.get(device_id)

        if device is None:
            return None

        if action_type == "SET_STATE":
            device.apply_state(payload)
            return payload  # ✅ RETURN WHAT WAS APPLIED

        return None

    return action
