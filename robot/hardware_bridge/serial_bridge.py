import time
import threading
from typing import Optional

try:
    import serial
    from serial import SerialException
except ImportError:
    serial = None
    SerialException = Exception

from app.config import SERIAL_PORT, SERIAL_BAUDRATE, USE_HARDWARE


class SerialBridge:
    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        use_hardware: Optional[bool] = None,
        timeout: float = 1.0,
        startup_delay: float = 2.0,
    ):
        self.port = port if port is not None else SERIAL_PORT
        self.baudrate = baudrate if baudrate is not None else SERIAL_BAUDRATE
        self.use_hardware = use_hardware if use_hardware is not None else USE_HARDWARE
        self.timeout = timeout
        self.startup_delay = startup_delay

        self.connection = None
        self.latest_distance: Optional[float] = None
        self.last_message: Optional[str] = None

        self._reader_thread: Optional[threading.Thread] = None
        self._running = False

        # ✅ Thread-safety lock: prevents reader and sender from
        # accessing the serial port simultaneously (cause of PermissionError crash)
        self._serial_lock = threading.Lock()

    def connect(self) -> bool:
        if not self.use_hardware:
            print("[INFO] Hardware disabled in config.")
            return False

        if serial is None:
            print("[ERROR] pyserial is not installed.")
            return False

        if self.is_connected():
            print(f"[INFO] Serial already connected on {self.port}")
            return True

        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )
            time.sleep(self.startup_delay)
            print(f"[INFO] Serial connected on {self.port}")

            self._start_reader()
            return True

        except SerialException as e:
            print(f"[ERROR] Serial connection failed: {e}")
            self.connection = None
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected serial connection error: {e}")
            self.connection = None
            return False

    def is_connected(self) -> bool:
        return self.connection is not None and getattr(self.connection, "is_open", False)

    def send(self, command: str) -> bool:
        if not command or not command.strip():
            return False

        command = command.strip()

        if not self.is_connected():
            print(f"[SIMULATED SEND] {command}")
            return False

        with self._serial_lock:
            try:
                data = (command + "\n").encode("utf-8")
                self.connection.write(data)
                self.connection.flush()
                print(f"[SERIAL SENT] {command}")

                # ✅ Small stabilization delay after motor commands
                # Motors draw heavy current — give ESP32 time to stabilize
                if command.startswith("MOVE_") or command == "STOP":
                    time.sleep(0.05)

                return True

            except (SerialException, OSError, PermissionError) as e:
                print(f"[ERROR] Serial send failed: {e}")
                try:
                    if self.connection and self.connection.is_open:
                        self.connection.close()
                except Exception:
                    pass
                self.connection = None
                return False
            except Exception as e:
                print(f"[ERROR] Unexpected serial send error: {e}")
                return False

    def read_line(self) -> Optional[str]:
        if not self.is_connected():
            return None

        with self._serial_lock:
            try:
                if self.connection.in_waiting > 0:
                    line = self.connection.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        self._handle_message(line)
                        return line

            except SerialException as e:
                print(f"[ERROR] Serial read failed: {e}")
            except Exception as e:
                print(f"[ERROR] Unexpected serial read error: {e}")

        return None

    def _start_reader(self) -> None:
        if self._reader_thread and self._reader_thread.is_alive():
            return

        self._running = True
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def _reader_loop(self) -> None:
        while self._running:
            if not self.is_connected():
                if not self._running:
                    break  # ✅ Stop reconnect attempts during shutdown

                print("[SERIAL] Connection lost. Attempting reconnect in 5s...")
                time.sleep(5)

                if not self._running:
                    break  # ✅ Check again after sleep

                try:
                    self.connection = serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        timeout=self.timeout,
                    )
                    time.sleep(self.startup_delay)
                    print(f"[SERIAL] Reconnected on {self.port}! ✅")
                except Exception as e:
                    print(f"[SERIAL] Reconnect failed: {e}")
                    self.connection = None
                continue

            with self._serial_lock:
                try:
                    if self.connection and self.connection.in_waiting > 0:
                        line = self.connection.readline().decode("utf-8", errors="ignore").strip()
                        if line:
                            # ✅ FILTER: Ignore null/heartbeat bytes from ESP32
                            # ESP32 sends "00" or "0" as idle keepalive — not meaningful
                            stripped = line.lstrip('0').strip()
                            is_junk = (stripped == '' or line in ('00', '0', '000'))
                            if is_junk:
                                pass  # Silently discard — don't print, don't handle
                            else:
                                self._handle_message(line)
                                if not line.startswith("DIST:"):
                                    print(f"[SERIAL RECEIVED] {line}")
                except (SerialException, OSError, PermissionError) as e:
                    print(f"[ERROR] Reader thread serial error: {e}")
                    try:
                        if self.connection and self.connection.is_open:
                            self.connection.close()
                    except Exception:
                        pass
                    self.connection = None
                    # Don't break — loop will auto-reconnect
                except Exception as e:
                    print(f"[ERROR] Reader thread unexpected error: {e}")

            time.sleep(0.05)  # ✅ Reduced CPU usage

    def _handle_message(self, message: str) -> None:
        self.last_message = message

        if message.startswith("DIST:"):
            try:
                self.latest_distance = float(message.split(":", 1)[1].strip())
            except ValueError:
                pass

    def get_latest_distance(self) -> Optional[float]:
        return self.latest_distance

    def disconnect(self) -> None:
        self.close()

    def close(self) -> None:
        self._running = False

        if self.connection is not None:
            try:
                if getattr(self.connection, "is_open", False):
                    self.connection.close()
                print("[INFO] Serial connection closed.")
            except Exception:
                pass
            finally:
                self.connection = None


if __name__ == "__main__":
    bridge = SerialBridge()

    print("Starting SerialBridge test...")

    if bridge.connect():
        bridge.send("PING")
        time.sleep(1)

        for _ in range(20):
            msg = bridge.read_line()
            if msg:
                print(f"[MANUAL READ] {msg}")
            time.sleep(0.2)

        print(f"[INFO] Latest Distance: {bridge.get_latest_distance()}")

        bridge.send("STOP")
        bridge.close()
    else:
        print("Could not connect to ESP32.")