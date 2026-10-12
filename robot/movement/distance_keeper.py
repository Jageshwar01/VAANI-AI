import time
from app.config import SAFE_DISTANCE_CM, MIN_DISTANCE_CM


class DistanceKeeper:
    def __init__(self, serial_bridge, motor_controller):
        self.serial_bridge = serial_bridge
        self.motor_controller = motor_controller
        self.last_distance = None
        self.last_status = None

        # ✅ Throttle: only print/send STOP once, not 1000x per second
        self._last_stop_sent = 0         # timestamp of last STOP command
        self._stop_cooldown = 2.0        # seconds between repeated STOP sends
        self._last_print_time = 0        # timestamp of last warning print
        self._print_cooldown = 5.0       # only print warning every 5 seconds

    def get_distance(self):
        distance = self.serial_bridge.get_latest_distance()
        if distance is not None:
            self.last_distance = distance
        return distance

    def maintain_distance(self):
        distance = self.get_distance()

        if distance is None:
            return None

        # ignore invalid
        if distance < 0:
            return None

        now = time.time()

        # HARD STOP (emergency) — but throttled
        if distance < MIN_DISTANCE_CM:
            # Only send STOP command if cooldown has passed
            if now - self._last_stop_sent >= self._stop_cooldown:
                self.motor_controller.stop()
                self._last_stop_sent = now

            # Only print warning every N seconds to avoid log flood
            if now - self._last_print_time >= self._print_cooldown:
                print(f"⚠ EMERGENCY STOP (distance: {distance:.0f}cm)")
                self._last_print_time = now

            self.last_status = "too_close_stop"
            return "too_close_stop"

        # SAFE STOP (before collision) — also throttled
        elif distance < SAFE_DISTANCE_CM:
            if now - self._last_stop_sent >= self._stop_cooldown:
                self.motor_controller.stop()
                self._last_stop_sent = now

            if now - self._last_print_time >= self._print_cooldown:
                print(f"⚠ SAFE STOP (distance: {distance:.0f}cm)")
                self._last_print_time = now

            self.last_status = "safe_stop"
            return "safe_stop"

        self.last_status = "clear"
        return "clear"