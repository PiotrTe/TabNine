import sys
import time
import threading
import tkinter as tk
import keyboard
from tkinter import ttk, messagebox



# --- Core configuration/state -------------------------------------------------

# Default number of Tab presses and delay between them (seconds)
_DEFAULT_TAB_COUNT = 9
_DEFAULT_TAB_DELAY = 0.01

# Prevent recursion when we synthesize Tab presses
_sending_lock = threading.Event()

# Current configuration (updated from GUI)
_TAB_COUNT = _DEFAULT_TAB_COUNT
_TAB_DELAY = _DEFAULT_TAB_DELAY

# Hook ids
_tab_hook = None
_any_hook = None

# --- Core behavior (keyboard hooks) -------------------------------------------

def send_tabs(count: int, delay: float) -> None:
    """Send `count` Tab presses with `delay` between them, avoiding recursion."""
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
    """Handle physical Tab key presses."""
    if event.event_type != "down":
        return
    send_tabs(_TAB_COUNT, _TAB_DELAY)


def _on_any_key(event) -> None:
    """
    When CapsLock is held and a letter key is pressed, trigger the Tab sequence.
    Does not block the original key press.
    """
    if event.event_type != "down":
        return

    if _sending_lock.is_set():
        return

    name = event.name
    if not name or len(name) != 1 or not name.isalpha():
        return

    # Turbo mode is always enabled: CapsLock + letter triggers tabs
    if keyboard.is_pressed("capslock"):
        send_tabs(_TAB_COUNT, _TAB_DELAY)


def start_hooks(count: int, delay: float) -> None:
    """
    Start global keyboard hooks with the given settings.
    - count:  how many Tab presses to send
    - delay:  delay between Tab presses
    """
    global _tab_hook, _any_hook, _TAB_COUNT, _TAB_DELAY

    _TAB_COUNT = count
    _TAB_DELAY = delay

    stop_hooks()
    # Always suppress physical Tab
    _tab_hook = keyboard.on_press_key("tab", _on_tab, suppress=True)
    _any_hook = keyboard.on_press(_on_any_key)


def stop_hooks() -> None:
    """Remove any active keyboard hooks."""
    global _tab_hook, _any_hook

    if _tab_hook is not None:
        try:
            keyboard.unhook(_tab_hook)
        except Exception:
            pass
        _tab_hook = None

    if _any_hook is not None:
        try:
            keyboard.unhook(_any_hook)
        except Exception:
            pass
        _any_hook = None


# --- GUI ----------------------------------------------------------------------

def build_gui() -> None:
    root = tk.Tk()
    root.title("Tab-9")
    root.minsize(360, 220)
    root.resizable(False, False)

    main = ttk.Frame(root, padding=16)
    main.grid(sticky="nsew")

    # Simple usage instructions
    instructions = (
        "1. Set how many Tabs to send and the delay between them.\n"
        "2. Press Tab to skip multiple lines.\n"
        "3. Hold CapsLock to skip lines after any input."
    )
    lbl_info = ttk.Label(main, text=instructions, justify="left")
    lbl_info.grid(column=0, row=0, columnspan=2, sticky="w", pady=(0, 10))

    # Tab count
    ttk.Label(main, text="Tab count:").grid(column=0, row=1, sticky="w", padx=(0, 8))
    count_var = tk.IntVar(value=_DEFAULT_TAB_COUNT)
    # limit between 1 and 99
    count_spin = ttk.Spinbox(main, from_=1, to=99, textvariable=count_var, width=6)
    count_spin.grid(column=1, row=1, sticky="w")

    # Delay
    ttk.Label(main, text="Delay (seconds):").grid(
        column=0, row=2, sticky="w", padx=(0, 8), pady=(4, 0)
    )
    delay_var = tk.DoubleVar(value=_DEFAULT_TAB_DELAY)
    delay_entry = ttk.Entry(main, textvariable=delay_var, width=8)
    delay_entry.grid(column=1, row=2, sticky="w", pady=(4, 0))

    # Status
    status_var = tk.StringVar(value="Stopped")
    ttk.Label(main, text="Status:").grid(column=0, row=3, sticky="w", pady=(10, 0))
    status_lbl = ttk.Label(main, textvariable=status_var)
    status_lbl.grid(column=1, row=3, sticky="w", pady=(10, 0))

    # Start/Stop buttons
    def on_start() -> None:
        try:
            c = int(count_var.get())
            d = float(delay_var.get())
        except Exception:
            messagebox.showerror(
                "Invalid input", "Please enter valid numbers for count and delay."
            )
            return

        # clamp tab count between 1 and 99
        if c < 1:
            c = 1
            count_var.set(1)
        elif c > 99:
            c = 99
            count_var.set(99)

        try:
            start_hooks(c, d)
        except Exception as e:
            messagebox.showerror("Hook error", f"Failed to start keyboard hooks:\n{e}")
            status_var.set("Error")
            return

        status_var.set("Running")

    def on_stop() -> None:
        stop_hooks()
        status_var.set("Stopped")

    btn_start = ttk.Button(main, text="Start", command=on_start)
    btn_start.grid(column=0, row=4, pady=(10, 0), sticky="w")

    btn_stop = ttk.Button(main, text="Stop", command=on_stop)
    btn_stop.grid(column=1, row=4, pady=(10, 0), sticky="w")

    # Clean shutdown
    def on_close() -> None:
        stop_hooks()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    main.columnconfigure(0, weight=0)
    main.columnconfigure(1, weight=1)

    root.mainloop()


def main() -> None:
    build_gui()


if __name__ == "__main__":
    main()