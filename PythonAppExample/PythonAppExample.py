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

# Number of Tab presses and inter-key delay (seconds)
_TAB_COUNT = 9
_TAB_DELAY = 0.01


def send_tabs(count: int = _TAB_COUNT, delay: float = _TAB_DELAY) -> None:
    """Send `count` Tab presses, using a lock to avoid recursion from synthesized events."""
    if _sending_lock.is_set():
        return
    _sending_lock.set()
    try:
        for _ in range(count):
            keyboard.send("tab")
            time.sleep(delay)
    finally:
        _sending_lock.clear()


def _on_tab(event) -> None:
    # Only react on physical key down
    if event.event_type != "down":
        return
    send_tabs()


def _on_any_key(event) -> None:
    """Listen to all physical key downs. If Ctrl is held and a letter is pressed,
    emit the tab sequence but do NOT suppress the letter (do not block the original key)."""
    if event.event_type != "down":
        return

    # Ignore while we're sending tabs to avoid re-entrancy
    if _sending_lock.is_set():
        return

    # Only consider single-character alphabetic keys (letters)
    name = event.name
    if not name or len(name) != 1 or not name.isalpha():
        return

    # If either Ctrl key is currently pressed, trigger the tab sequence.
    # Do NOT suppress the original letter — we intentionally do not register with suppress=True.
    if keyboard.is_pressed("capslock"):
        send_tabs()


def main() -> None:
    print("Running: hold Ctrl and press any letter (e.g. P or A) to emit the Tab sequence without suppressing the letter.")
    print("Press Tab (alone) to emit Tab sequence as before. Press Esc to exit, or Ctrl+C in this console.")

    # Intercept Tab and suppress the original so only the synthesized tabs are seen
    keyboard.on_press_key("tab", _on_tab, suppress=True)

    # Hook all key presses to detect Ctrl + <letter>.
    # This does NOT suppress the letter key — the letter will still be delivered to the active app.
    keyboard.on_press(_on_any_key)

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