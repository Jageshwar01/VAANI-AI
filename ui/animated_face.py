import tkinter as tk
import threading
import time
import random


class AnimatedFace:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VaaniAI")
        self.root.geometry("480x520")
        self.root.configure(bg="#0a0a0a")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            self.root,
            width=480,
            height=480,
            bg="#0a0a0a",
            highlightthickness=0
        )
        self.canvas.pack()

        self.status_label = tk.Label(
            self.root,
            text="IDLE",
            font=("Courier", 13),
            fg="#00ff99",
            bg="#0a0a0a"
        )
        self.status_label.pack()

        self.expression = "neutral"
        self.blink_open = True
        self.running = True

        self.left_eye_center = (160, 200)
        self.right_eye_center = (320, 200)
        self.eye_rx = 50
        self.eye_ry = 55

        self.mouth_points = self._get_mouth_points("neutral")

        self._draw_face()

        self.blink_thread = threading.Thread(target=self._blink_loop, daemon=True)
        self.blink_thread.start()

    def _get_mouth_points(self, expression):
        cx, cy = 240, 330
        if expression == "happy":
            return [cx - 60, cy, cx - 30, cy + 30, cx, cy + 40, cx + 30, cy + 30, cx + 60, cy]
        elif expression == "thinking":
            return [cx - 40, cy + 10, cx - 10, cy, cx + 20, cy + 5, cx + 40, cy - 5]
        elif expression == "listening":
            return [cx - 50, cy, cx, cy + 15, cx + 50, cy]
        elif expression == "speaking":
            return [cx - 55, cy, cx - 20, cy + 25, cx, cy + 30, cx + 20, cy + 25, cx + 55, cy]
        else:
            return [cx - 50, cy, cx, cy + 8, cx + 50, cy]

    def _draw_face(self):
        self.canvas.delete("all")

        # Outer glow ring
        self.canvas.create_oval(
            60, 60, 420, 420,
            outline="#003322", width=2
        )
        self.canvas.create_oval(
            70, 70, 410, 410,
            outline="#005533", width=1
        )

        # Face circle
        self.canvas.create_oval(
            80, 80, 400, 400,
            fill="#111111", outline="#00ff99", width=2
        )

        # Eyes
        lx, ly = self.left_eye_center
        rx2, ry2 = self.right_eye_center
        ew, eh = self.eye_rx, self.eye_ry if self.blink_open else 4

        # Left eye
        self.canvas.create_oval(
            lx - ew, ly - eh, lx + ew, ly + eh,
            fill="#001a0d", outline="#00ff99", width=2
        )
        if self.blink_open:
            self.canvas.create_oval(
                lx - 20, ly - 20, lx + 20, ly + 20,
                fill="#00ff99"
            )
            self.canvas.create_oval(
                lx - 8, ly - 8, lx + 8, ly + 8,
                fill="#003311"
            )
            self.canvas.create_oval(
                lx + 10, ly - 18, lx + 18, ly - 10,
                fill="#66ffcc"
            )

        # Right eye
        self.canvas.create_oval(
            rx2 - ew, ry2 - eh, rx2 + ew, ry2 + eh,
            fill="#001a0d", outline="#00ff99", width=2
        )
        if self.blink_open:
            self.canvas.create_oval(
                rx2 - 20, ry2 - 20, rx2 + 20, ry2 + 20,
                fill="#00ff99"
            )
            self.canvas.create_oval(
                rx2 - 8, ry2 - 8, rx2 + 8, ry2 + 8,
                fill="#003311"
            )
            self.canvas.create_oval(
                rx2 + 10, ry2 - 18, rx2 + 18, ry2 - 10,
                fill="#66ffcc"
            )

        # Eyebrow lines
        if self.expression == "thinking":
            self.canvas.create_line(
                lx - 50, ly - 70, lx + 50, ly - 80,
                fill="#00ff99", width=3
            )
            self.canvas.create_line(
                rx2 - 50, ry2 - 80, rx2 + 50, ry2 - 70,
                fill="#00ff99", width=3
            )
        else:
            self.canvas.create_line(
                lx - 50, ly - 75, lx + 50, ly - 75,
                fill="#00ff99", width=2
            )
            self.canvas.create_line(
                rx2 - 50, ry2 - 75, rx2 + 50, ry2 - 75,
                fill="#00ff99", width=2
            )

        # Mouth
        pts = self.mouth_points
        if len(pts) >= 8:
            self.canvas.create_line(
                pts,
                fill="#00ff99", width=3,
                smooth=True
            )

        # Corner decorations
        for cx2, cy2 in [(100, 100), (380, 100), (100, 380), (380, 380)]:
            self.canvas.create_oval(
                cx2 - 5, cy2 - 5, cx2 + 5, cy2 + 5,
                fill="#003322", outline="#00ff99"
            )

    def _blink_loop(self):
        while self.running:
            wait = random.uniform(2.5, 5.5)
            time.sleep(wait)

            for _ in range(2):
                self.blink_open = False
                self.root.after(0, self._draw_face)
                time.sleep(0.08)
                self.blink_open = True
                self.root.after(0, self._draw_face)
                time.sleep(0.05)

    def set_expression(self, expression: str):
        valid = ["neutral", "happy", "thinking", "listening", "speaking"]
        if expression in valid:
            self.expression = expression
            self.mouth_points = self._get_mouth_points(expression)
            self.root.after(0, self._draw_face)

    def set_status(self, text: str):
        self.root.after(0, lambda: self.status_label.config(text=text.upper()))

    def speak_animate(self, duration=2.0):
        def animate():
            end_time = time.time() + duration
            while time.time() < end_time:
                self.set_expression("speaking")
                time.sleep(0.15)
                self.set_expression("neutral")
                time.sleep(0.12)
            self.set_expression("neutral")

        t = threading.Thread(target=animate, daemon=True)
        t.start()

    def run(self):
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.after(0, self.root.destroy)


if __name__ == "__main__":
    face = AnimatedFace()
    face.set_status("VaaniAI Online")
    face.set_expression("happy")
    face.run()