import time
from devices.ac import AC
from automation.rules import evaluate_automation

ac = AC("ac_1", "living_room")

# Simulate sensors
ac.sensors["ambient_temperature"] = 30
ac.sensors["occupancy"] = True

for hour in [10, 14, 20, 23]:
    print(f"\n--- Hour {hour} ---")
    evaluate_automation(ac, current_hour=hour)
    print("AC power:", ac.state["power"])
    time.sleep(1)
