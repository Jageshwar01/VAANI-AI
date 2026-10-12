import time


class MotorController:
    def __init__(self, serial_bridge):
        self.serial_bridge = serial_bridge
        self.current_state = "STOP"
        self.current_speed = 240
        self._move_start_time = 0       # When movement started
        self._move_timeout = 3.0        # Auto-stop after 3 seconds of continuous movement

    def _send(self, command: str):
        if not self.serial_bridge:
            print("[WARN] No serial bridge")
            return False

        return self.serial_bridge.send(command)

    def _change_state(self, new_state: str):
        if self.current_state == new_state:
            return  # avoid duplicate commands

        # smooth transition
        if self.current_state != "STOP":
            self._send("STOP")

        self.current_state = new_state

    # -------- MOVEMENT --------

    def forward(self):
        self._change_state("FORWARD")
        self._send("MOVE_FORWARD")
        self._move_start_time = time.time()

    def backward(self):
        self._change_state("BACKWARD")
        self._send("MOVE_BACKWARD")
        self._move_start_time = time.time()

    def left(self):
        self._change_state("LEFT")
        self._send("TURN_LEFT")
        self._move_start_time = time.time()

    def right(self):
        self._change_state("RIGHT")
        self._send("TURN_RIGHT")
        self._move_start_time = time.time()

    def stop(self):
        if self.current_state == "STOP":
            return
        self.current_state = "STOP"
        self._move_start_time = 0
        self._send("STOP")

    # -------- SAFETY TIMEOUT --------

    def check_timeout(self):
        """Auto-stop if movement runs longer than timeout. Call from main loop."""
        if self.current_state != "STOP" and self._move_start_time > 0:
            if time.time() - self._move_start_time >= self._move_timeout:
                print(f"[MOTOR] Auto-stop: movement timed out after {self._move_timeout}s")
                self.stop()

    # -------- SPEED --------

    def set_speed(self, speed: int):
        speed = max(0, min(255, int(speed)))

        if speed == self.current_speed:
            return

        self.current_speed = speed
        self._send(f"SPEED:{speed}")