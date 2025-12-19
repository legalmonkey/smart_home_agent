# automation/config.py

automation_config = {
    # -------- AC RULES --------
    "ac_thresholds": {
        "morning": {
            "on_temp": 26,
            "off_temp": 22
        },
        "afternoon": {
            "on_temp": 24,
            "off_temp": 20
        },
        "night": {
            "on_temp": 27,
            "off_temp": 23
        }
    },

    # -------- FAN RULES --------
    "fan_rules": {
        "morning": {
            "use_occupancy": True
        },
        "afternoon": {
            "use_occupancy": True
        },
        "night": {
            "use_occupancy": False  # fans stay off at night unless overridden
        }
    },

    # -------- LIGHT RULES --------
    "light_rules": {
        "morning": {
            "use_occupancy": False  # daylight
        },
        "afternoon": {
            "use_occupancy": False  # daylight
        },
        "night": {
            "use_occupancy": True
        }
    }
}
# automation/config.py  (ADD this section)

automation_config["ml_policy"] = {
    "enabled": True,

    # kWh thresholds
    "energy_limits": {
        "low": 2.0,
        "high": 4.5
    },

    # How much to tighten AC thresholds when energy is high
    "ac_adjustment": {
        "high_energy_delta": +2,   # make AC harder to turn ON
        "low_energy_delta": -1     # make AC easier to turn ON
    }
}
automation_config.update({

    # -------- FAN RULES --------
    "fan_rules": {
        "morning": {"use_occupancy": True},
        "afternoon": {"use_occupancy": True},
        "night": {"use_occupancy": False}
    },

    # -------- LIGHT RULES --------
    "light_rules": {
        "morning": {"allow": False},
        "afternoon": {"allow": False},
        "night": {"allow": True}
    },

    # -------- ML LIGHT POLICY --------
    "ml_light_policy": {
        "enabled": True,
        "high_energy_cutoff": 4.5  # kWh
    }
})
