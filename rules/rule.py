class Rule:
    def __init__(
        self,
        rule_id,
        description,
        priority,
        enabled,
        condition,
        action
    ):
        self.rule_id = rule_id
        self.description = description
        self.priority = priority
        self.enabled = enabled
        self.condition = condition
        self.action = action

    def evaluate(self, snapshot, ml_prediction=None):
        return self.condition(snapshot, ml_prediction)

    def execute(self, snapshot):
        return self.action(snapshot)

