import os
import cv2
import face_recognition
from app.config import KNOWN_FACES_DIR

class FaceEnrollment:
    def __init__(self, camera_manager, face_engine):
        self.camera_manager = camera_manager
        self.face_engine = face_engine

    def capture_and_enroll(self, person_name, role="person"):
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

        print(f"Starting enrollment for {person_name} ({role})")
        print("Press S to capture face, Q to quit")

        while True:
            ret, frame = self.camera_manager.read_frame()

            if not ret or frame is None:
                print("Camera frame not received")
                return False

            display = frame.copy()

            cv2.putText(
                display,
                f"Press S to capture | {person_name}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow("VaaniAI Face Enrollment", display)

            key = cv2.waitKey(1)

            # SAVE IMAGE
            if key == ord('s') or key == ord('S'):

                filename = f"{person_name.lower().replace(' ','_')}.jpg"
                filepath = os.path.join(KNOWN_FACES_DIR, filename)

                cv2.imwrite(filepath, frame)

                print("Image saved:", filepath)

                # CHECK face exists before encoding
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                faces = face_recognition.face_locations(rgb)

                if len(faces) == 0:
                    print("No face detected. Try better lighting.")
                    continue

                try:
                    self.face_engine.add_face_from_image(filepath, person_name, role)
                    print("Face encoding stored successfully")
                    cv2.destroyWindow("VaaniAI Face Enrollment")
                    return True

                except Exception as e:
                    print("Encoding failed:", e)
                    return False

            # QUIT
            elif key == ord('q') or key == ord('Q'):
                print("Enrollment cancelled")
                cv2.destroyWindow("VaaniAI Face Enrollment")
                return False

    def auto_capture_and_enroll(self, person_name: str, role="visitor", timeout: float = 3.0) -> bool:
        """
        Silently captures a face embedding without showing an OpenCV GUI.
        Loops for up to `timeout` seconds until a clear face is found.
        """
        import time
        start_time = time.time()
        
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
        filename = f"{person_name.lower().replace(' ','_')}.jpg"
        filepath = os.path.join(KNOWN_FACES_DIR, filename)

        print(f"[VISION] Attempting to auto-enroll {person_name} (will try for {timeout}s)...")

        while time.time() - start_time < timeout:
            ret, frame = self.camera_manager.read_frame()
            if not ret or frame is None:
                time.sleep(0.1)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb)

            if len(faces) == 0:
                time.sleep(0.1)
                continue  # Keep trying until timeout

            # Face found!
            try:
                # Save the image for debugging and storage
                cv2.imwrite(filepath, frame)
                # Add to memory
                self.face_engine.add_face_from_image(filepath, person_name, role)
                print(f"[VISION] Successfully auto-enrolled face for {person_name}!")
                return True
            except Exception as e:
                print(f"[VISION] Auto-enrollment error for {person_name}: {e}")
                return False

        print(f"[VISION] Timeout: Could not detect a clear face for {person_name} within {timeout}s.")
        return False