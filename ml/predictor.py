import joblib
import os
import pandas as pd

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "models",
    "energy_predictor.pkl"
)

class EnergyPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)

    def predict(self, state: dict) -> float:
        """
        state: aggregated simulator state
        """
        df = pd.DataFrame([state])
        return float(self.model.predict(df)[0])
