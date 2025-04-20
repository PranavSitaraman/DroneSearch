#!/usr/bin/env python3
import time
import os
import logging
import threading
import cv2
import numpy as np
from djitellopy import Tello

# ——— Utility ———
def parse_key_values(s: str) -> dict:
    out = {}
    for part in s.strip().split(';'):
        if ':' not in part:
            continue
        k, v = part.split(':', 1)
        try:
            out[k] = float(v)
        except ValueError:
            out[k] = None
    return out

# ——— Logging Thread ———
def start_data_collection(tello, frame_reader):
    os.makedirs('images', exist_ok=True)
    os.makedirs('imu', exist_ok=True)
    ts_log = open('timestep.txt', 'w')

    def loop():
        while logging_active[0]:
            ts = time.time()
            bgr = frame_reader.frame
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            cv2.imwrite(os.path.join('images', f"{int(ts * 1000)}.png"), rgb)

            data = {
                'timestamp': ts,
                'battery': tello.get_battery(),
                'height_cm': tello.get_height(),
                'flight_time_s': tello.get_flight_time(),
                'speed_x': tello.get_speed_x(),
                'speed_y': tello.get_speed_y(),
                'speed_z': tello.get_speed_z(),
                'acc_x': tello.get_acceleration_x(),
                'acc_y': tello.get_acceleration_y(),
                'acc_z': tello.get_acceleration_z(),
                'tof_cm': tello.get_distance_tof(),
                'temperature_C': tello.get_temperature(),
            }

            try:
                att = parse_key_values(tello.send_read_command('attitude?'))
                data.update({k: att.get(k) for k in ['pitch', 'roll', 'yaw']})
            except: pass

            try:
                data['barometer_cm'] = float(tello.send_read_command('baro?'))
            except: data['barometer_cm'] = None

            try:
                data['wifi_snr'] = float(tello.send_read_command('wifi?'))
            except: data['wifi_snr'] = None

            with open(os.path.join('imu', f"{int(ts * 1000)}.txt"), 'w') as f:
                for k, v in data.items():
                    f.write(f"{k}: {v}\n")

            ts_log.write(f"{ts}\n")
            ts_log.flush()
            time.sleep(0.1)  # 10Hz

        ts_log.close()

    thread = threading.Thread(target=loop)
    thread.start()
    return thread

# ——— Main ———
def main():
    tello = Tello()
    tello.LOGGER.setLevel(logging.DEBUG)
    tello.connect()
    print(f"✅ Connected (Battery: {tello.get_battery()}%)")

    tello.streamon()
    frame_reader = tello.get_frame_read()
    time.sleep(2)

    print("📸 Starting data collection thread")
    thread = start_data_collection(tello, frame_reader)

    print("🛫 Taking off...")
    tello.takeoff()
    time.sleep(1)

    print("🔁 Moving forward while spinning (spiral path)")
    # Spiral: 10x (10 cm forward + 36° turn) = 100cm forward + 360°
    for _ in range(10):
        tello.move_forward(10)
        time.sleep(1)
        tello.rotate_clockwise(36)
        time.sleep(1)

    print("🛬 Landing")
    tello.land()

    logging_active[0] = False
    thread.join()
    tello.streamoff()
    tello.end()
    cv2.destroyAllWindows()

# Shared state flag for logging loop
logging_active = [True]

if __name__ == "__main__":
    main()