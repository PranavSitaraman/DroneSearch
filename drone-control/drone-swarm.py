from djitellopy import Tello
import threading
import time

# Replace with actual IPs if in AP mode or using EDU swarm
TELLO_IPS = [
    '192.168.10.1',  # Drone 1 (default)
    '192.168.10.2',  # Drone 2
    # Add more IPs as needed
]

def control_drone(ip):
    drone = Tello(host=ip)
    drone.connect()
    print(f"[{ip}] Battery: {drone.get_battery()}%")

    drone.takeoff()
    time.sleep(3)

    drone.move_forward(50)
    time.sleep(2)

    drone.land()
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
