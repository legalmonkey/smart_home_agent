from fastapi import FastAPI, APIRouter

from devices.light import Light
from devices.fan import Fan
from devices.ac import AC

from engine.simulator_loop import SimulatorEngine
from rules.loader import load_rules
from rules.engine import RuleEngine
from api.routes import attach_routes
from ml.predictor import EnergyPredictor

app = FastAPI(title="IoT Simulator with ML + Rules")

devices = {
    "light_1": Light("light_1", "living_room"),
    "fan_1": Fan("fan_1", "bedroom"),
    "ac_1": AC("ac_1", "living_room")
}

rules = load_rules("rules/rules.json", devices)
rule_engine = RuleEngine(rules)
predictor = EnergyPredictor()

engine = SimulatorEngine(devices, rule_engine=rule_engine)
#engine = SimulatorEngine(devices)

engine.start()

router = APIRouter()
attach_routes(router, devices, rule_engine, predictor)
app.include_router(router)
