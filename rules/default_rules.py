from rules.rule import Rule
from rules.actions import set_device_state

def build_rules(devices):
    rules = []

    # Rule 1: High temperature → AC ON
    rules.append(
        Rule(
            rule_id="high_temp_ac_on",
            description="Turn AC ON if temperature exceeds 28C",
            condition=lambda snap: (
                snap["device_type"] == "AC"
                and snap["sensors"].get("ambient_temperature", 0) > 28
                and snap["state"]["power"] == "OFF"
            ),
            action=lambda snap: set_device_state(
                devices,
                snap["device_id"],
                {"power": "ON", "set_temperature": 24}
            )
        )
    )

    # Rule 2: No occupancy → AC OFF
    rules.append(
        Rule(
            rule_id="no_occupancy_ac_off",
            description="Turn AC OFF if no occupancy",
            condition=lambda snap: (
                snap["device_type"] == "AC"
                and snap["sensors"].get("occupancy") is False
                and snap["state"]["power"] == "ON"
            ),
            action=lambda snap: set_device_state(
                devices,
                snap["device_id"],
                {"power": "OFF"}
            )
        )
    )

    return rules
