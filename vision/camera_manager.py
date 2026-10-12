import cv2
import threading
from app.config import CAMERA_INDEX, USE_CAMERA


class CameraManager:
    def __init__(self, camera_index=CAMERA_INDEX):
        self.camera_index = camera_index
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None

    def start(self):
        if not USE_CAMERA:
            return False

        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            print("Camera could not be opened.")
            self.cap = None
            return False

        # Performance settings
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

        print("Camera started successfully (threaded).")
        return True

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                self.frame = cv2.flip(frame, 1)

    def read_frame(self):
        if self.frame is None:
            return False, None
        return True, self.frame.copy()

    def release(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()