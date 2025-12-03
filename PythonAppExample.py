import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import keyboard
except Exception:
    keyboard = None

if keyboard is None:
    messagebox.showerror("Missing dependency", "This app requires the 'keyboard' package.\nInstall with: pip install keyboard")
    sys.exit(1)

# Prevent recursion when we synthesize Tab presses
_sending_lock = threading.Event()

# Number of Tab presses and inter-key delay (seconds)
_TAB_COUNT = 9
_TAB_DELAY = 0.01

# Hook ids
_tab_hook = None
_any_hook = None

# GUI state
# Don't create tkinter variables before a root window exists.
# Use a simple thread-safe flag for code running outside the GUI thread.
_turbo_enabled_flag = True
_turbo_lock = threading.Lock()


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
    """Listen to all physical key downs. If CapsLock is held and a letter is pressed,
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

    # If turbo is enabled and CapsLock is currently pressed, trigger the tab sequence.
    # Use the thread-safe flag (GUI will update it).
    with _turbo_lock:
        enabled = _turbo_enabled_flag
    if enabled and keyboard.is_pressed("capslock"):
        send_tabs()


def start_hooks(count: int, delay: float, suppress_tab: bool = True) -> None:
    global _tab_hook, _any_hook, _TAB_COUNT, _TAB_DELAY
    _TAB_COUNT = count
    _TAB_DELAY = delay

    # If already hooked, unhook first to re-register with new params
    stop_hooks()

    _tab_hook = keyboard.on_press_key("tab", _on_tab, suppress=suppress_tab)
    _any_hook = keyboard.on_press(_on_any_key)


def stop_hooks() -> None:
    global _tab_hook, _any_hook
    try:
        if _tab_hook:
            keyboard.unhook(_tab_hook)
            _tab_hook = None
    except Exception:
        pass
    try:
        if _any_hook:
            keyboard.unhook(_any_hook)
            _any_hook = None
    except Exception:
        pass


def build_gui() -> None:
    root = tk.Tk()
    root.title("Tab9")
    root.resizable(False, False)

    frm = ttk.Frame(root, padding=12)
    frm.grid()

    ttk.Label(frm, text="Tab Count:").grid(column=0, row=0, sticky="w")
    count_var = tk.IntVar(value=_TAB_COUNT)
    count_spin = ttk.Spinbox(frm, from_=1, to=50, textvariable=count_var, width=6)
    count_spin.grid(column=1, row=0, sticky="w")
    
    ttk.Label(frm, text="Delay (s):").grid(column=0, row=1, sticky="w")
    delay_var = tk.DoubleVar(value=_TAB_DELAY)
    delay_entry = ttk.Entry(frm, textvariable=delay_var, width=8)
    delay_entry.grid(column=1, row=1, sticky="w")

    # Create the tkinter BooleanVar after the root exists and keep the keyboard thread
    # informed by updating the thread-safe flag when the checkbox changes.
    turbo_var = tk.BooleanVar(value=_turbo_enabled_flag)
    def _on_turbo_toggle():
        with _turbo_lock:
            global _turbo_enabled_flag
            _turbo_enabled_flag = bool(turbo_var.get())

    suppress_var = tk.BooleanVar(value=True)

    status_var = tk.StringVar(value="Stopped")
    ttk.Label(frm, text="Status:").grid(column=0, row=4, sticky="w", pady=(8, 0))
    status_lbl = ttk.Label(frm, textvariable=status_var)
    status_lbl.grid(column=1, row=4, sticky="w", pady=(8, 0))

    def on_start():
        try:
            c = int(count_var.get())
            d = float(delay_var.get())
        except Exception:
            messagebox.showerror("Invalid input", "Please enter valid numeric values for count and delay.")
            return
        start_hooks(c, d, suppress_tab=suppress_var.get())
        status_var.set("Running")

    def on_stop():
        stop_hooks()
        status_var.set("Stopped")

    btn_start = ttk.Button(frm, text="Start", command=on_start)
    btn_start.grid(column=0, row=5, pady=(10, 0))
    btn_stop = ttk.Button(frm, text="Stop", command=on_stop)
    btn_stop.grid(column=1, row=5, pady=(10, 0))

    # Ensure hooks are stopped when window is closed
    def _on_close():
        stop_hooks()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


def main() -> None:
    build_gui()


if __name__ == "__main__":
    main()