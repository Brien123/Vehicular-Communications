import asyncio
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from asyncio.subprocess import PIPE
import logging
import threading

logging.basicConfig(level=logging.INFO)


class OBUApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OBU System Monitor")

        # UI components for each OBU system
        self.create_obu_section("Keyless")
        self.create_obu_section("Toll")
        self.create_obu_section("Infotainment")
        self.create_obu_section("HMI")

    def create_obu_section(self, system_name):
        """Section in the UI for an OBU system."""
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        label = tk.Label(frame, text=f"{system_name} System", font=("Arial", 12, "bold"))
        label.pack(anchor="w")

        text_area = ScrolledText(frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        text_area.pack(fill=tk.BOTH, expand=True)

        setattr(self, f"{system_name.lower()}_text_area", text_area)

    def append_text(self, system_name, message, color="black"):
        """Message to the appropriate text area."""
        text_area = getattr(self, f"{system_name.lower()}_text_area")
        text_area.configure(state=tk.NORMAL)
        text_area.insert(tk.END, f"{message}\n", ("color",))
        text_area.tag_configure("color", foreground=color)
        text_area.see(tk.END)
        text_area.configure(state=tk.DISABLED)


async def start_obu_system(command, system_name, app):
    """Running OBU system and update the UI in real-time."""
    process = await asyncio.create_subprocess_exec(*command, stdout=PIPE, stderr=PIPE)

    async def read_stream(stream, stream_type):
        color = "green" if stream_type == "stdout" else "red"
        while True:
            line = await stream.readline()
            if not line:
                break
            message = line.decode().strip()
            app.append_text(system_name, f"{stream_type.upper()}: {message}", color)

    await asyncio.gather(
        read_stream(process.stdout, "stdout"),
        read_stream(process.stderr, "stderr"),
    )

    await process.wait()


async def start_all_systems(app):
    """Starting all OBU systems concurrently."""
    await asyncio.gather(
        start_obu_system(["python", "keyless_obu/keyless.py"], "Keyless", app),
        start_obu_system(["python", "toll_obu/toll.py"], "Toll", app),
        start_obu_system(["python", "infot_obu/infot.py"], "Infotainment", app),
        start_obu_system(["python", "hmi_obu/hmi.py"], "HMI", app),
    )


def run_asyncio_loop(loop):
    """Running the asyncio loop in a separate thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_ui():
    """Starting Tkinter UI and the asyncio loop."""
    root = tk.Tk()
    app = OBUApp(root)

    # new asyncio event loop
    loop = asyncio.new_event_loop()

    # Running the asyncio loop in a separate thread
    threading.Thread(target=run_asyncio_loop, args=(loop,), daemon=True).start()

    # Schedule the asyncio tasks in the new loop
    loop.call_soon_threadsafe(asyncio.create_task, start_all_systems(app))

    # Start the Tkinter mainloop
    root.mainloop()


if __name__ == "__main__":
    start_ui()
