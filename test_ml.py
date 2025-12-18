from ml.predictor import EnergyPredictor

predictor = EnergyPredictor()

sample = {
    "hour_of_day": 14,
    "ambient_temperature": 30,
    "occupancy": 2,
    "ac_power": True,
    "set_temperature": 24,
    "total_current_load": 2.2,
    "cumulative_energy": 55
}

print(predictor.predict(sample))
