import os
import sys
import time


def main() -> int:
    path = os.environ.get("SIMULATOR_HEARTBEAT_FILE", "/tmp/simulator-heartbeat")
    interval = float(os.environ.get("SIMULATOR_INTERVAL_SECONDS", "5"))
    max_age = max(interval * 3, 15.0)
    try:
        age = time.time() - os.path.getmtime(path)
    except OSError:
        return 1
    return 0 if age < max_age else 1


if __name__ == "__main__":
    sys.exit(main())
