from djitellopy import Tello
import time

interface_names = [b"eth1", b"eth2"]
tello_ip = ["192.168.10.1", "192.168.10.3"]

for i in range(2):
    drone = Tello(host=tello_ip[i])
    drone.connect()
    time.sleep(2)
    drone.takeoff()
    time.sleep(2)
    drone.land()
    print("✅ Done.")