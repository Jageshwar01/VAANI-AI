import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brain import VaaniBrain


def main():
    robot = VaaniBrain()

    try:
        robot.initialize()
        robot.run()

    except KeyboardInterrupt:
        print("\n[VaaniAI] Stopped by user.")
        robot.shutdown()

    except Exception as e:
        print(f"[VaaniAI] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        robot.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()