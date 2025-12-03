import sys
import time
import threading

try:
    import keyboard
except Exception:
    keyboard = None

if keyboard is None:
    print("This script requires the 'keyboard' package. Install with: pip install keyboard")
    sys.exit(1)

# Prevent recursion when we synthesize Tab presses
_sending_lock = threading.Event()

def _on_tab(event) -> None:
    # Only react on physical key down
    if event.event_type != "down":
        return
    if _sending_lock.is_set():
        return
    _sending_lock.set()
    try:
        # Send 9 Tab presses (one original + 8 repeats)
        for _ in range(9):
            keyboard.send("tab")
            time.sleep(0.01)  # tiny gap to ensure target app processes keys
    finally:
        _sending_lock.clear()

def main() -> None:
    print("Running: press Tab to emit 9 Tab keys. Press Esc to exit, or Ctrl+C in this console.")
    # Intercept Tab and suppress the original so only the synthesized tabs are seen
    keyboard.on_press_key("tab", _on_tab, suppress=True)
    try:
        # Block until user presses Esc
        keyboard.wait("esc")
    except KeyboardInterrupt:
        pass
    finally:
        print("Exiting.")
        # Remove hooks and exit
        keyboard.unhook_all()
        sys.exit(0)

if __name__ == "__main__":
    main()