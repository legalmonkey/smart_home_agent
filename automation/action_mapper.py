class ActionMapper:

    @staticmethod
    def map_action(device, action: str, value):
        action = action.upper()

        if device.__class__.__name__ == "AC":
            if action == "ON":
                device.turn_on()
            elif action == "OFF":
                device.turn_off()
            elif action == "SET_TEMPERATURE":
                device.set_temperature(value)
            else:
                raise ValueError("Unsupported AC action")

        elif device.__class__.__name__ == "Light":
            if action == "ON":
                device.turn_on()
            elif action == "OFF":
                device.turn_off()
            elif action == "SET_BRIGHTNESS":
                device.set_brightness(value)
            else:
                raise ValueError("Unsupported Light action")

        elif device.__class__.__name__ == "Fan":
            if action == "ON":
                device.turn_on()
            elif action == "OFF":
                device.turn_off()
            elif action == "SET_SPEED":
                device.set_speed(value)
            else:
                raise ValueError("Unsupported Fan action")

        else:
            raise ValueError("Unknown device type")
