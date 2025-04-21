from djitellopy import Tello
import time

drone = Tello()
drone.connect()
time.sleep(2)
drone.takeoff()
time.sleep(2)
drone.land()