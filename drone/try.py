from djitellopy import tello
from time import sleep

drone = tello.Tello()
drone.connect()
print(drone.get_battery())  # optional

def doSomething():
    drone.takeoff()
    sleep(1)
    drone.rotate_clockwise(90)
    sleep(1)
    drone.land()
    sleep(1)

condition = 1 > 0

if (condition):  # optional
    doSomething()