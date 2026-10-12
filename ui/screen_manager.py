from flask import Flask, render_template, jsonify
import threading
import logging


class ScreenManager:
    def __init__(self):
        self.app = Flask(__name__, template_folder="templates")
        self.state = {
            "emotion": "neutral",
            "text": "Hello, I am Vaani.",
            "listening": False,
            "speaking": False,
            "connected": True,
        }

        # ✅ Suppress Flask/Werkzeug HTTP access logs (/state spam)
        # Only show WARNING and above (errors, startup) — not every GET request
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.WARNING)

        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/")
        def home():
            return render_template("face.html")

        @self.app.route("/state")
        def get_state():
            return jsonify(self.state)

    def update_state(self, **kwargs):
        self.state.update(kwargs)

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        self.app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)