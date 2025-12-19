def get_time_of_day_from_hour(hour: int) -> str:
    if 6 <= hour < 18:
        return "day"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"
