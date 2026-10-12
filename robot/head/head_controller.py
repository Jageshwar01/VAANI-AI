import time

class HeadController:
    def __init__(self, serial_bridge):
        self.serial_bridge = serial_bridge
        self.current_state = "STOP"
        self.last_cmd_time = 0.0

    def _send(self, command: str):
        if not self.serial_bridge:
            print("[WARN] No serial bridge")
            return False
        return self.serial_bridge.send(command)

    def look_left(self):
        now = time.time()
        # Allow repeated LEFT commands for relative stepping, but throttle to 300ms
        if self.current_state == "LEFT" and (now - self.last_cmd_time) < 0.3:
            return
        self.current_state = "LEFT"
        self.last_cmd_time = now
        self._send("HEAD_LEFT")

    def look_right(self):
        now = time.time()
        # Allow repeated RIGHT commands for relative stepping, but throttle to 300ms
        if self.current_state == "RIGHT" and (now - self.last_cmd_time) < 0.3:
            return
        self.current_state = "RIGHT"
        self.last_cmd_time = now
        self._send("HEAD_RIGHT")

    def look_center(self):
        if self.current_state == "STOP":
            return
        self.current_state = "STOP"
        self.last_cmd_time = time.time()
        self._send("HEAD_STOP")

    def stop(self):
        self.current_state = "STOP"
        self._send("HEAD_STOP")

    def trim(self, value: int):
        self._send(f"HEAD_TRIM:{int(value)}")