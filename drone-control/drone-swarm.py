from djitellopy import Tello
import threading
import time

# Replace with actual IPs if in AP mode or using EDU swarm
# Find IP addresses using `netsh interface ip show address` on Windows
TELLO_IPS = [
    '192.168.10.2',  # Drone 1 (default)
    '192.168.10.3',  # Drone 2
    # Add more IPs as needed
]

def control_drone(ip):
    drone = Tello(host=ip)
    drone.connect()
    print(f"[{ip}] Battery: {drone.get_battery()}%")
    time.sleep(3)

    drone.streamon()
    frame_reader = drone.get_frame_read()
    time.sleep(2)
    drone.streamoff()

    print(f"[{ip}] Landed.")

def main():
    threads = []

    for ip in TELLO_IPS:
        t = threading.Thread(target=control_drone, args=(ip,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
