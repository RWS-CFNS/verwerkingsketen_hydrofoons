import tkinter as tk
from tkinter import Canvas
import threading
import time
import math
import re
from collections import deque
from PIL import Image, ImageTk
import os
import argparse

# Get mode from command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["test", "demo", "field"], help="python ./analyze.py <test|demo|field> (<mode>)")
args = parser.parse_args()

script_dir = os.path.dirname(os.path.abspath(__file__))
folder = os.path.normpath(os.path.join(script_dir, "../recordings"))

LOG_FILE = os.path.join(folder, "results.txt")
MIC_RADIUS = 15 # Only visual circle
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
SPEED_OF_SOUND = 343  # m/s
TIME_SYNC_ERROR = 0.000_020_000  # seconds
PLACEMENT_ERROR = 0.005  # meters
DEFAULT_CM_PER_SQUARE = 10
GRID_PIXEL_SIZE = 100  # pixels between grid lines (width and height div by this size must be integer)

line_pattern = re.compile(r"Signal pair \((\d+), (\d+)\): Estimated distance from center: ([\-\d.]+) cm. SNR: ([\d.]+)")

distance_data = deque()
if args.mode == "test":
    distance_data = deque(maxlen=1)
elif args.mode == "demo":
    distance_data = deque(maxlen=3)



microphones = {}  # id -> (x, y)
lock = threading.Lock() # for safely looking at "distance_data"-queue

class MicBandVisualizer:
    def __init__(self, root):
        self.root = root
        self.canvas = Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="black")
        self.canvas.pack()

        # Controls
        control_frame = tk.Frame(root)
        control_frame.pack()
        tk.Label(control_frame, text="Centimeters per square:").pack(side=tk.LEFT)
        self.cm_entry = tk.Entry(control_frame, width=5)
        self.cm_entry.insert(0, str(DEFAULT_CM_PER_SQUARE))
        self.cm_entry.pack(side=tk.LEFT)
        tk.Button(control_frame, text="Apply", command=self.update_scale).pack(side=tk.LEFT)

        self.tk_image = None
        self.mic_widgets = {}
        self.mic_labels = {}

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.drag_data = {"item": None, "id": None, "x": 0, "y": 0}

        self.cm_per_square = DEFAULT_CM_PER_SQUARE 
        self.SCALE = GRID_PIXEL_SIZE / (self.cm_per_square / 100)

        self.update_loop()

    def update_scale(self):
        try:
            self.cm_per_square = float(self.cm_entry.get())
            self.SCALE = GRID_PIXEL_SIZE / (self.cm_per_square / 100)  # 100px = X cm
        except ValueError:
            pass

    def on_press(self, event):
        for mic_id, widget in self.mic_widgets.items():
            x1, y1, x2, y2 = self.canvas.coords(widget)
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.drag_data["item"] = widget
                self.drag_data["id"] = mic_id
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                break

    def on_drag(self, event):
        if self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            mic_id = self.drag_data["id"]
            self.canvas.move(self.mic_widgets[mic_id], dx, dy)
            self.canvas.move(self.mic_labels[mic_id], dx, dy)
            coords = self.canvas.coords(self.mic_widgets[mic_id])
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            microphones[mic_id] = (cx, cy)
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def update_loop(self):
        self.draw_frame()
        self.root.after(100, self.update_loop)

    def draw_frame(self):
        image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "black")
        pixels = image.load()

        # Draw fixed-pixel grid every GRID_PIXEL_SIZE pixels
        for x in range(0, CANVAS_WIDTH, GRID_PIXEL_SIZE):
            for y in range(CANVAS_HEIGHT):
                pixels[x, y] = (50, 50, 50)
        for y in range(0, CANVAS_HEIGHT, GRID_PIXEL_SIZE):
            for x in range(CANVAS_WIDTH):
                pixels[x, y] = (50, 50, 50)

        # Safely copy distance data
        with lock:
            data_copy = list(distance_data)

        # Draw bands
        for i, (pair, distance_cm, snr) in enumerate(data_copy):
            mic1, mic2 = pair
            if mic1 not in microphones or mic2 not in microphones:
                continue
            x1, y1 = microphones[mic1]
            x2, y2 = microphones[mic2]

            d_measured = (distance_cm * 2) / 100  # See for reason "*2" synchronize.py 
            dist_error1 = 2 * PLACEMENT_ERROR
            dist_error2 = -2 * PLACEMENT_ERROR

            delta_time = d_measured / SPEED_OF_SOUND
            time_error1 = SPEED_OF_SOUND * (delta_time + TIME_SYNC_ERROR)
            time_error2 = SPEED_OF_SOUND * (delta_time - TIME_SYNC_ERROR)

            max_error = max(time_error1 + dist_error1, time_error1 + dist_error2,
                            time_error2 + dist_error1, time_error2 + dist_error2)
            min_error = min(time_error1 + dist_error1, time_error1 + dist_error2,
                            time_error2 + dist_error1, time_error2 + dist_error2)

            fade = 1.0 if i == len(data_copy) - 1 else 0.75 if i == len(data_copy) - 2 else 0.5

            # Calculate the color for each pixel
            for y in range(CANVAS_HEIGHT):
                for x in range(CANVAS_WIDTH):
                    d1 = math.hypot(x - x1, y - y1) / self.SCALE
                    d2 = math.hypot(x - x2, y - y2) / self.SCALE
                    diff = d1 - d2
                    if min_error <= diff <= max_error:
                        r, g, b = pixels[x, y]
                        color = (int(255 * fade), int(127 * fade), int(255 * fade))
                        if snr < 16: # Low SNR, invert color
                            color = (int(255 - color[0]), int(255 - color[1]), int(255 - color[2]))
                        pixels[x, y] = (min(r + color[0], 255), min(g + color[1], 255), min(b + color[2], 255))

        # Overwrite the window with the new frame
        self.tk_image = ImageTk.PhotoImage(image)
        self.canvas.create_image((0, 0), image=self.tk_image, anchor=tk.NW)

        # Make sure the mics are drawn on top
        for mic_id in self.mic_widgets:
            self.canvas.tag_raise(self.mic_widgets[mic_id])
            self.canvas.tag_raise(self.mic_labels[mic_id])

    def add_microphone(self, mic_id):
        if mic_id in self.mic_widgets:
            return
        x, y = 100 + 50 * len(microphones), 100
        microphones[mic_id] = (x, y)
        circle = self.canvas.create_oval(x - MIC_RADIUS, y - MIC_RADIUS, x + MIC_RADIUS, y + MIC_RADIUS, fill="white")
        label = self.canvas.create_text(x, y, text=str(mic_id), fill="black")
        self.mic_widgets[mic_id] = circle
        self.mic_labels[mic_id] = label

# Update queue with last three lines, add mics when new ones found in line
def tail_file():
    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            match = line_pattern.search(line)
            if match:
                mic1 = int(match.group(1))
                mic2 = int(match.group(2))
                distance = float(match.group(3))
                snr = float(match.group(4))
                # Safely access the shared distance_data
                with lock:
                    distance_data.append(((mic1, mic2), distance, snr))
                app.root.after(0, app.add_microphone, mic1)
                app.root.after(0, app.add_microphone, mic2)

# Start tail thread and window thread
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Mic Band Visualizer with Physical Scaling")
    app = MicBandVisualizer(root)

    # Create a thread to read the log file, to separate GUI rendering and file reading
    thread = threading.Thread(target=tail_file, daemon=True)
    thread.start()

    root.mainloop()
