def evaluate_operator(left, operator, right):
    if operator == ">":
        return left > right
    if operator == "<":
        return left < right
    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right
    if operator == ">=":
        return left >= right
    if operator == "<=":
        return left <= right
    return False
