from fastapi import FastAPI, APIRouter

from devices.light import Light
from devices.fan import Fan
from devices.ac import AC

from engine.simulator_loop import SimulatorEngine
from rules.loader import load_rules
from rules.engine import RuleEngine
from api.routes import attach_routes


# ---------- FastAPI App ----------
app = FastAPI()


# ---------- Device Registry ----------
devices = {
    "light_1": Light("light_1", "living_room"),
    "fan_1": Fan("fan_1", "bedroom"),
    "ac_1": AC("ac_1", "living_room"),
}


# ---------- Rule Engine ----------
rules = load_rules("rules/rules.json", devices)
rule_engine = RuleEngine(rules)


# ---------- Simulator ----------
simulator = SimulatorEngine(
    devices,
    rule_engine=rule_engine,
)


# ---------- API Routes ----------
router = APIRouter()
attach_routes(
    router,
    devices,
    rule_engine,
    simulator.predictor,   # ✅ use the simulator’s predictor
)
app.include_router(router)


# ---------- Startup Hook ----------
@app.on_event("startup")
def start_simulator():
    """
    Start the simulator exactly once when the app boots.
    This is REQUIRED for Render deployment.
    """
    simulator.start()
