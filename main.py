from fastapi import FastAPI, APIRouter

from devices.light import Light
from devices.fan import Fan
from devices.ac import AC

from engine.simulator_loop import SimulatorEngine
from rules.loader import load_rules
from rules.engine import RuleEngine
from api.routes import attach_routes


# ==============================
# FASTAPI APP
# ==============================
app = FastAPI()


# ==============================
# DEVICE REGISTRY
# ==============================
devices = {
    "light_1": Light("light_1", "living_room"),
    "fan_1": Fan("fan_1", "bedroom"),
    "ac_1": AC("ac_1", "living_room"),
}


# ==============================
# RULE ENGINE
# ==============================
rules = load_rules("rules/rules.json", devices)
rule_engine = RuleEngine(rules)


# ==============================
# SIMULATOR ENGINE
# ==============================
simulator = SimulatorEngine(
    devices=devices,
    rule_engine=rule_engine,
)


# ==============================
# API ROUTES
# ==============================
router = APIRouter()

attach_routes(
    router=router,
    devices=devices,
    rule_engine=rule_engine,
    predictor=simulator.predictor,  # ✅ single source of truth
    engine=simulator                # ✅ REQUIRED for mode toggle
)

app.include_router(router)


# ==============================
# STARTUP HOOK (RENDER SAFE)
# ==============================
@app.on_event("startup")
def start_simulator():
    """
    Start the simulator exactly once when the app boots.
    REQUIRED for Render / production deployment.
    """
    simulator.start()
