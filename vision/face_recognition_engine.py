import os
import cv2
import pickle
import numpy as np
import face_recognition

from app.config import (
    KNOWN_FACES_DIR,
    FACE_TOLERANCE,
    FRAME_RESIZE_SCALE,
    OWNER_NAME
)


class FaceRecognitionEngine:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_roles = []
        self.encodings_file = os.path.join(KNOWN_FACES_DIR, "encodings.pkl")
        os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

    def load_known_faces(self):
        if os.path.exists(self.encodings_file):
            with open(self.encodings_file, "rb") as f:
                data = pickle.load(f)
                self.known_face_encodings = data.get("encodings", [])
                self.known_face_names = data.get("names", [])
                self.known_face_roles = data.get("roles", [])
            print(f"Loaded {len(self.known_face_names)} known faces.")
        else:
            print("No saved encodings found yet.")

    def save_known_faces(self):
        data = {
            "encodings": self.known_face_encodings,
            "names": self.known_face_names,
            "roles": self.known_face_roles
        }
        with open(self.encodings_file, "wb") as f:
            pickle.dump(data, f)
        print("Face encodings saved.")

    def add_face_from_image(self, image_path, person_name, role="person"):
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image, num_jitters=1)

        if not encodings:
            raise ValueError(f"No face found in image: {image_path}")

        encoding = encodings[0]
        self.known_face_encodings.append(encoding)
        self.known_face_names.append(person_name)
        self.known_face_roles.append(role)
        self.save_known_faces()

    def recognize_faces_in_frame(self, frame):
        small_frame = cv2.resize(
            frame,
            (0, 0),
            fx=FRAME_RESIZE_SCALE,
            fy=FRAME_RESIZE_SCALE
        )
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(
            rgb_small_frame,
            model="hog"
        )

        if not face_locations:
            return []

        face_encodings = face_recognition.face_encodings(
            rgb_small_frame,
            face_locations,
            num_jitters=1
        )

        results = []

        for encoding, location in zip(face_encodings, face_locations):
            name = "Unknown"
            role = "unknown"

            if self.known_face_encodings:
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings,
                    encoding
                )

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    best_distance = face_distances[best_match_index]

                    if best_distance <= FACE_TOLERANCE:
                        name = self.known_face_names[best_match_index]
                        role = self.known_face_roles[best_match_index]

            top, right, bottom, left = location
            top = int(top / FRAME_RESIZE_SCALE)
            right = int(right / FRAME_RESIZE_SCALE)
            bottom = int(bottom / FRAME_RESIZE_SCALE)
            left = int(left / FRAME_RESIZE_SCALE)

            results.append({
                "name": name,
                "role": role,
                "location": (top, right, bottom, left),
                "is_owner": name.lower() == OWNER_NAME.lower()
            })

        return results

    def draw_face_labels(self, frame, results):
        for item in results:
            top, right, bottom, left = item["location"]
            name = item["name"]
            role = item["role"]

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            label = f"{name} ({role})"
            cv2.rectangle(frame, (left, bottom - 30), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(
                frame,
                label,
                (left + 6, bottom - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                1
            )
        return frame