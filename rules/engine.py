class DecisionContext:
    def __init__(self):
        self.actions = {}
        self.explanations = []

    def add(self, device_id, payload, rule):
        if device_id not in self.actions:
            self.actions[device_id] = payload or {}

        self.explanations.append({
            "rule_id": rule.rule_id,
            "device_id": device_id,
            "reason": rule.description
        })


class RuleEngine:
    def __init__(self, rules):
        self.rules = sorted(
            rules,
            key=lambda r: r.priority,
            reverse=True
        )

    def evaluate(self, devices, ml_prediction=None):
        context = DecisionContext()

        for device in devices.values():
            snapshot = device.snapshot()

            for rule in self.rules:
                if not rule.enabled:
                    continue

                if rule.evaluate(snapshot, ml_prediction):
                    payload = rule.execute(snapshot)
                    context.add(
                        snapshot["device_id"],
                        payload,
                        rule
                    )
                    break  # highest-priority rule per device

        return context.actions, context.explanations
