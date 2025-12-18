import json
from rules.rule import Rule
from rules.operators import evaluate_operator
from rules.actions import create_action


def load_rules(path, devices):
    with open(path) as f:
        raw_rules = json.load(f)

    rules = []

    for r in raw_rules:
        when = r["when"]

        def make_condition(when):
            def condition(snapshot, ml_prediction=None):

                # 1. Device type filter
                if snapshot.get("device_type") != when["device_type"]:
                    return False

                sensor = when["sensor"]

                # 2. ML-based rule
                if sensor == "predicted_energy":
                    if ml_prediction is None:
                        return False
                    return evaluate_operator(
                        ml_prediction,
                        when["operator"],
                        when["value"]
                    )

                # 3. Time-based rule (hour injected by simulator)
                if sensor == "hour_of_day":
                    left = snapshot.get("hour_of_day")
                    if left is None:
                        return False
                    return evaluate_operator(
                        left,
                        when["operator"],
                        when["value"]
                    )

                # 4. Normal sensor rule
                left = snapshot.get(sensor)

                # ✅ CRITICAL FIX: missing sensor → rule not applicable
                if left is None:
                    return False

                return evaluate_operator(
                    left,
                    when["operator"],
                    when["value"]
                )

            return condition

        rules.append(
            Rule(
                rule_id=r["rule_id"],
                description=r["description"],
                priority=r["priority"],
                enabled=r["enabled"],
                condition=make_condition(when),
                action=create_action(r["then"], devices)
            )
        )

    return rules
