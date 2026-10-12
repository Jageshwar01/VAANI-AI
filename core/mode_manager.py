class ModeManager:
    IDLE = "idle"
    SOCIAL = "social"
    INTERVIEW = "interview"
    ADMIN = "admin"

    def __init__(self, default_mode=IDLE):
        self.current_mode = default_mode

    def set_mode(self, mode):
        self.current_mode = mode

    def get_mode(self):
        return self.current_mode