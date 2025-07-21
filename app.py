from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import time
import threading
import random
import logging
import math
import json
import os


# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Frame configuration
FRAME_DELAY = 1 / 60  # 60 FPS

# Device configuration
DEVICES_FILE = "devices.json"
if os.path.exists(DEVICES_FILE):
    with open(DEVICES_FILE, "r") as f:
        DEVICES = json.load(f)
else:
    DEVICES = {}

# Map device names to LED index lists
LED_GROUPS = {name: list(range(dev["num_pixels"])) for name, dev in DEVICES.items()}

# Shared LED state
current_colors = {group: [0, 0, 0] for group in LED_GROUPS}
current_effects = {}  # e.g. current_effects[group] = "pulsate"
led_overrides = {group: {} for group in LED_GROUPS}  # per-group LED overrides

# ----- Favorites Storage -----
FAVORITES_FILE = "favorites.json"
if os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, "r") as f:
        favorites = json.load(f)
else:
    favorites = [
        [255, 0, 0],
        [255, 127, 0],
        [255, 255, 0],
        [0, 255, 0],
        [0, 255, 255],
        [0, 0, 255],
        [139, 0, 255],
        [255, 0, 255],
        [255, 192, 203],
        [255, 255, 255]
    ]
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f)

# ----- Utility Functions -----
def hsv_to_rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    c = v * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = v - c
    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return [int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)]

def send_artnet(ip, universe, data):
    packet = bytearray()
    packet.extend(b'Art-Net\x00')
    packet.extend((0x5000).to_bytes(2, 'little'))
    packet.extend((14).to_bytes(2, 'big'))
    packet.extend(b'\x00')  # sequence
    packet.extend(b'\x00')  # physical
    packet.extend(int(universe).to_bytes(2, 'little'))
    packet.extend(len(data).to_bytes(2, 'big'))
    packet.extend(bytes(data))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(packet, (ip, 6454))
    finally:
        sock.close()


def create_led_buffer(group):
    buffer = []
    num_leds = len(LED_GROUPS[group])
    overrides = led_overrides.get(group, {})
    for i in range(num_leds):
        if i in overrides:
            color = overrides[i]
        else:
            color = current_colors[group]
        buffer.extend(color)
    return buffer


def update_leds():
    for group, device in DEVICES.items():
        data = create_led_buffer(group)
        send_artnet(device["ip"], device["universe"], data)

def fade_to_color(group, target_color, duration=2, allowed_effects=None):
    if allowed_effects is None:
        allowed_effects = ["fade"]
    steps = int(duration * 60)
    start_color = current_colors[group][:]
    for step in range(steps):
        if current_effects.get(group) not in allowed_effects:
            logging.info(f"Fade for {group} interrupted.")
            return
        intermediate = [int(start_color[i] + (target_color[i] - start_color[i]) * (step / steps)) for i in range(3)]
        current_colors[group] = intermediate
        update_leds()
        time.sleep(FRAME_DELAY)
    current_colors[group] = target_color
    update_leds()

# ----- Effect Functions -----
def color_cycle_effect(group, speed, vibrancy):
    colors = [
        [255, 0, 0],
        [0, 255, 0],
        [0, 0, 255],
        [255, 255, 0],
        [0, 255, 255],
        [255, 0, 255],
    ]
    index = 0
    while current_effects.get(group) == "color_cycle":
        target = colors[index]
        factor = vibrancy / 255.0
        L = int(0.299 * target[0] + 0.587 * target[1] + 0.114 * target[2])
        new_color = [int((L + (target[i]-L)*factor)*factor) for i in range(3)]
        fade_to_color(group, new_color, duration=speed, allowed_effects=["color_cycle"])
        index = (index + 1) % len(colors)

def pulsating_effect(group, speed, min_brightness=0, max_brightness=255):
    base = current_colors[group][:]
    while current_effects.get(group) == "pulsate":
        for b in range(min_brightness, max_brightness+1, 5):
            if current_effects.get(group) != "pulsate":
                return
            adj = [int(c * (b / 255)) for c in base]
            current_colors[group] = adj
            update_leds()
            time.sleep(speed / 100)
        for b in range(max_brightness, min_brightness-1, -5):
            if current_effects.get(group) != "pulsate":
                return
            adj = [int(c * (b / 255)) for c in base]
            current_colors[group] = adj
            update_leds()
            time.sleep(speed / 100)

def starry_night_effect(group, speed):
    dim = [10, 10, 30]
    current_colors[group] = dim
    update_leds()
    leds = LED_GROUPS[group]
    while current_effects.get(group) == "starry_night":
        count = max(1, len(leds) // 10)
        twinkle = random.sample(leds, count)
        for led in twinkle:
            led_overrides[group][led] = [255, 255, 255]
        update_leds()
        time.sleep(speed / 2)
        for led in twinkle:
            led_overrides[group].pop(led, None)
        update_leds()
        time.sleep(speed)

def candle_effect(group, speed, intensity=1.0, base_color=None):
    # Original candle effect for comparison
    if base_color is None:
        base_color = [255, 147, 41]
    while current_effects.get(group) == "candle":
        t = time.time()
        wave = 1.0 + 0.2 * math.sin(2 * math.pi * t / speed)
        flicker = random.uniform(0.95, 1.05)
        factor = intensity * wave * flicker
        factor = max(0.7, min(factor, 1.5))
        target = [
            min(255, int(base_color[0] * factor)),
            min(255, int(base_color[1] * (0.95 + 0.05 * factor))),
            min(255, int(base_color[2] * factor))
        ]
        fade_to_color(group, target, duration=0.1, allowed_effects=["candle"])
        time.sleep(speed)

def candle_gradient_effect(group, speed, intensity, gradient_amplitude, gradient_speed, base_color=None):
    """
    Candle Gradient Effect:
      - Global flicker factor from a slow sine wave plus random noise.
      - Local gradient factor that varies with LED position, using a sine function whose phase shifts over time.
      - The gradient may reverse direction randomly every few seconds.
    Parameters:
      intensity: overall brightness scaling (e.g., 0.7 to 2.0)
      gradient_amplitude: how pronounced the spatial gradient is (e.g., 0.0 to 1.0)
      gradient_speed: how fast the gradient phase shifts
      base_color: default warm yellow–orange ([255,147,41])
    """
    if base_color is None:
        base_color = [255, 147, 41]
    leds = LED_GROUPS[group]
    n = len(leds)
    direction = 1
    last_flip = time.time()
    flip_interval = 5.0  # Check every 5 seconds for possible reversal
    while current_effects.get(group) == "candle_gradient":
        t = time.time()
        if t - last_flip > flip_interval:
            if random.random() < 0.5:
                direction *= -1
            last_flip = t
        # Global flicker factor (sine wave with random noise)
        global_factor = intensity * (1.0 + 0.2 * math.sin(2 * math.pi * t / speed) + random.uniform(-0.15, 0.15))
        phase = t * gradient_speed * direction
        for idx, led in enumerate(leds):
            pos = idx / (n - 1) if n > 1 else 0
            # Local gradient: a sine wave that creates a spatial variation
            local_factor = 1.0 + gradient_amplitude * math.sin(2 * math.pi * (pos + phase)) + random.uniform(-0.1, 0.1)
            final_factor = global_factor * local_factor
            final_factor = max(0.7, min(final_factor, 1.8))
            target = [min(255, int(base_color[i] * final_factor)) for i in range(3)]
            led_overrides[group][led] = target
        update_leds()
        time.sleep(0.05)

def strobe_effect(group, speed):
    while current_effects.get(group) == "strobe":
        current_colors[group] = [255, 255, 255]
        update_leds()
        time.sleep(speed / 2)
        current_colors[group] = [0, 0, 0]
        update_leds()
        time.sleep(speed / 2)

def gradient_wave_effect(group, speed):
    base = current_colors[group][:]
    leds = LED_GROUPS[group]
    n = len(leds)
    low, high = 0.2, 1.0
    while current_effects.get(group) == "gradient_wave":
        t = time.time()
        phase = 0.5 * (1 + math.sin(2 * math.pi * t / speed))
        for idx, led in enumerate(leds):
            pos = idx / (n - 1) if n > 1 else 0
            brightness = high - (high - low) * pos if phase < 0.5 else low + (high - low) * pos
            grad_color = [min(255, int(c * brightness)) for c in base]
            led_overrides[group][led] = grad_color
        update_leds()
        time.sleep(0.05)
    for led in leds:
        led_overrides[group].pop(led, None)
    update_leds()

def snake_effect(group, speed):
    leds = LED_GROUPS[group]
    n = len(leds)
    snake_length = 10
    while current_effects.get(group) == "snake":
        for pos in range(n + snake_length):
            if current_effects.get(group) != "snake":
                return
            for idx, led in enumerate(leds):
                dist = pos - idx
                if 0 <= dist < snake_length:
                    factor = 1 - (dist / snake_length)
                    hue = (pos * 10) % 360
                    snake_color = hsv_to_rgb(hue, 1.0, factor)
                    led_overrides[group][led] = snake_color
                else:
                    led_overrides[group].pop(led, None)
            update_leds()
            time.sleep(speed / 20)
        for led in leds:
            led_overrides[group].pop(led, None)
        update_leds()

def favorite_cycle_effect(group, speed):
    global favorites
    if not favorites:
        return
    index = 0
    while current_effects.get(group) == "favorite_cycle":
        target = favorites[index % len(favorites)]
        fade_to_color(group, target, duration=speed, allowed_effects=["favorite_cycle"])
        index += 1

def favorite_jump_effect(group, speed):
    global favorites
    if not favorites:
        return
    group_order = list(LED_GROUPS.keys())
    try:
        offset = group_order.index(group)
    except ValueError:
        offset = 0
    index = offset
    while current_effects.get(group) == "favorite_jump":
        current_colors[group] = favorites[index % len(favorites)]
        update_leds()
        index += 1
        time.sleep(speed)

# ----- Endpoints -----
@app.route('/set_color', methods=['POST'])
def set_color_endpoint():
    data = request.json
    groups_req = data.get("groups", [])
    color = data.get("color", [255, 255, 255])

    for group in groups_req:
        if group in LED_GROUPS:
            current_effects[group] = "fade"
            logging.info(f"Setter farge {color} for {group}")
            threading.Thread(target=fade_to_color, args=(group, color), daemon=True).start()

    return jsonify({"status": "color set", "groups": groups_req, "color": color})


@app.route('/start_effect', methods=['POST'])
def start_effect_endpoint():
    data = request.json
    groups_req = data.get("groups", [])
    effect = data.get("effect", "pulsate")
    speed = float(data.get("speed", 0.2))
    for group in groups_req:
        if group in LED_GROUPS:
            current_effects[group] = effect
            logging.info(f"Starting effect '{effect}' for {group} at speed {speed}")
            if effect == "color_cycle":
                vibrancy = int(data.get("vibrancy", 255))
                threading.Thread(target=color_cycle_effect, args=(group, speed, vibrancy), daemon=True).start()
            elif effect == "pulsate":
                pulsate_min = int(data.get("pulsate_min", 0))
                pulsate_max = int(data.get("pulsate_max", 255))
                threading.Thread(target=pulsating_effect, args=(group, speed, pulsate_min, pulsate_max), daemon=True).start()
            elif effect == "starry_night":
                threading.Thread(target=starry_night_effect, args=(group, speed), daemon=True).start()
            elif effect == "candle":
                intensity = float(data.get("intensity", 1.0))
                base_color = data.get("candle_base_color", [255, 147, 41])
                threading.Thread(target=candle_effect, args=(group, speed, intensity, base_color), daemon=True).start()
            elif effect == "candle_v2":
                intensity = float(data.get("intensity", 1.0))
                base_color = data.get("candle_base_color", [255, 147, 41])
                threading.Thread(target=candle_effect, args=(group, speed, intensity, base_color), daemon=True).start()
            elif effect == "candle_gradient":
                intensity = float(data.get("intensity", 1.0))
                base_color = data.get("candle_base_color", [255, 147, 41])
                gradient_amplitude = float(data.get("gradient_amplitude", 0.5))
                gradient_speed = float(data.get("gradient_speed", 0.5))
                threading.Thread(target=candle_gradient_effect, args=(group, speed, intensity, gradient_amplitude, gradient_speed, base_color), daemon=True).start()
            elif effect == "strobe":
                threading.Thread(target=strobe_effect, args=(group, speed), daemon=True).start()
            elif effect == "gradient_wave":
                threading.Thread(target=gradient_wave_effect, args=(group, speed), daemon=True).start()
            elif effect == "snake":
                threading.Thread(target=snake_effect, args=(group, speed), daemon=True).start()
            elif effect == "favorite_cycle":
                threading.Thread(target=favorite_cycle_effect, args=(group, speed), daemon=True).start()
            elif effect == "favorite_jump":
                threading.Thread(target=favorite_jump_effect, args=(group, speed), daemon=True).start()
    return jsonify({"status": "effect started", "effect": effect, "groups": groups_req})

@app.route('/off', methods=['POST'])
def turn_off_endpoint():
    data = request.json
    groups_req = data.get("groups", [])
    for group in groups_req:
        current_effects.pop(group, None)
        logging.info(f"Turning off {group}")
        threading.Thread(target=fade_to_color, args=(group, [0, 0, 0]), daemon=True).start()
    return jsonify({"status": "turned off", "groups": groups_req})

@app.route('/off_all', methods=['POST'])
def turn_off_all_endpoint():
    current_effects.clear()
    for g in led_overrides:
        led_overrides[g].clear()
    for group in LED_GROUPS:
        current_colors[group] = [0, 0, 0]
    update_leds()
    logging.info("All lights turned off")
    return jsonify({"status": "all lights turned off"})

@app.route('/update_group_range', methods=['POST'])
def update_group_range_endpoint():
    data = request.json
    group = data.get("group")
    start = data.get("start")
    end = data.get("end")
    if group not in LED_GROUPS:
        return jsonify({"status": "error", "message": f"Group {group} not found"}), 404
    try:
        start = int(start)
        end = int(end)
        max_leds = DEVICES[group]["num_pixels"]
        if start < 0 or end >= max_leds or start > end:
            return jsonify({"status": "error", "message": "Invalid range values"}), 400
        LED_GROUPS[group] = list(range(start, end + 1))
        logging.info(f"Updated {group} active range to {start} - {end}")
        return jsonify({"status": "updated", "group": group, "range": [start, end]})
    except Exception as e:
        logging.error(f"Error updating group range: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/favorites', methods=['GET'])
def get_favorites():
    return jsonify(favorites)

@app.route('/favorites', methods=['POST'])
def update_favorites():
    global favorites
    data = request.json
    if not isinstance(data, list):
        return jsonify({"status": "error", "message": "Payload must be a list"}), 400
    favorites = data
    try:
        with open(FAVORITES_FILE, "w") as f:
            json.dump(favorites, f)
        return jsonify({"status": "updated", "favorites": favorites})
    except Exception as e:
        logging.error(f"Error saving favorites: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(DEVICES)


@app.route('/devices', methods=['POST'])
def update_devices():
    global DEVICES, LED_GROUPS, current_colors, led_overrides
    data = request.json
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Payload must be a dict"}), 400
    DEVICES = data
    try:
        with open(DEVICES_FILE, "w") as f:
            json.dump(DEVICES, f)
    except Exception as e:
        logging.error(f"Error saving devices: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    LED_GROUPS = {name: list(range(dev["num_pixels"])) for name, dev in DEVICES.items()}
    current_colors = {group: [0, 0, 0] for group in LED_GROUPS}
    led_overrides = {group: {} for group in LED_GROUPS}
    return jsonify({"status": "updated", "devices": DEVICES})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

