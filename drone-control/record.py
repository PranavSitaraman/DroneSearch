#!/usr/bin/env python3
import time
import os
import logging
import cv2
from djitellopy import Tello

def parse_key_values(s: str) -> dict:
    """
    Parse a semicolon-separated 'key:val;key:val;...' string into a dict of floats.
    """
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

def main():
    # ——— 1) Connect & stream ———
    tello = Tello()
    tello.LOGGER.setLevel(logging.DEBUG)
    tello.connect()
    print(f"✅ Connected (Battery: {tello.get_battery()}%)")
    tello.streamon()
    frame_reader = tello.get_frame_read()
    time.sleep(2)  # stream warm‑up

    # ——— 2) Prepare directories & timestamp log ———
    os.makedirs('images', exist_ok=True)
    os.makedirs('imu', exist_ok=True)
    ts_log = open('timestep.txt', 'w')

    print("Collecting data every 1 s. Ctrl+C to stop.")

    try:
        while True:
            ts = time.time()

            # ——— 3) Capture frame, convert BGR→RGB, save ———
            bgr = frame_reader.frame
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            img_path = os.path.join('images', f"{int(ts)}.png")
            cv2.imwrite(img_path, rgb)

            # ——— 4) Gather telemetry ———
            data = {}
            data['timestamp']      = ts
            data['battery']        = tello.get_battery()
            data['height_cm']      = tello.get_height()
            data['flight_time_s']  = tello.get_flight_time()
            data['speed_x']        = tello.get_speed_x()
            data['speed_y']        = tello.get_speed_y()
            data['speed_z']        = tello.get_speed_z()

            # Attitude: parse "pitch:-3;roll:0;yaw:122;"
            try:
                att_str = tello.send_read_command('attitude?')
                att = parse_key_values(att_str)
            except Exception:
                att = {}
            data['pitch'] = att.get('pitch')
            data['roll']  = att.get('roll')
            data['yaw']   = att.get('yaw')

            # Acceleration from onboard IMU
            data['acc_x'] = tello.get_acceleration_x()
            data['acc_y'] = tello.get_acceleration_y()
            data['acc_z'] = tello.get_acceleration_z()

            # Barometer: parse e.g. "-50.087814"
            try:
                baro = tello.send_read_command('baro?')
                data['barometer_cm'] = float(baro)
            except Exception:
                data['barometer_cm'] = None

            data['tof_cm']       = tello.get_distance_tof()
            data['temperature_C']= tello.get_temperature()

            # Wi‑Fi SNR: parse "wifi?-?" 
            try:
                wifi = tello.send_read_command('wifi?')
                data['wifi_snr'] = float(wifi)
            except Exception:
                data['wifi_snr'] = None

            # ——— 5) Write one IMU text file per timestamp ———
            imu_path = os.path.join('imu', f"{int(ts)}.txt")
            with open(imu_path, 'w') as f:
                for k, v in data.items():
                    f.write(f"{k}: {v}\n")

            # ——— 6) Log timestamp and wait ———
            ts_log.write(f"{ts}\n")
            ts_log.flush()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n✔ Stopped by user")
    finally:
        ts_log.close()
        tello.streamoff()
        tello.end()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()