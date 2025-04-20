import numpy as np
import math
from djitellopy import Tello
from scipy.spatial.transform import Rotation as R
import time

class TelloExplorer:
    def __init__(self, resolution=0.5, init_size=50):
        """
        resolution: meters per grid cell
        init_size: initial map is init_size x init_size, centered at (0,0)
        """
        # --- Drone setup ---
        self.tello = Tello(host='192.168.10.1')
        self.tello.connect()
        
        # --- Map initialization ---
        self.resolution = resolution
        self.unknown = -1
        self.free    =  0
        self.occ     =  1

        # occupancy map and visited mask
        self.occ_map = np.full((init_size, init_size), self.unknown, dtype=int)
        self.visited = np.zeros_like(self.occ_map, dtype=bool)

        # origin index in the array corresponding to world (0,0)
        self.origin = (init_size // 2, init_size // 2)
        self.curr_idx = self.origin
        self.yaw = 0.0   # current heading in degrees

    def world_to_grid(self, x, y):
        gx = int(round(x / self.resolution)) + self.origin[0]
        gy = int(round(y / self.resolution)) + self.origin[1]
        return gx, gy

    def ensure_in_map(self, gx, gy):
        """
        If (gx,gy) falls outside occ_map, pad both occ_map and visited.
        Adjust origin and curr_idx accordingly.
        """
        h, w = self.occ_map.shape
        pad_top = max(0, -gx)
        pad_bottom = max(0, gx - (h - 1))
        pad_left = max(0, -gy)
        pad_right = max(0, gy - (w - 1))
        if any((pad_top, pad_bottom, pad_left, pad_right)):
            self.occ_map = np.pad(self.occ_map,
                                  ((pad_top, pad_bottom), (pad_left, pad_right)),
                                  constant_values=self.unknown)
            self.visited = np.pad(self.visited,
                                  ((pad_top, pad_bottom), (pad_left, pad_right)),
                                  constant_values=False)
            # shift origin and current index
            self.origin    = (self.origin[0] + pad_top,    self.origin[1] + pad_left)
            self.curr_idx  = (self.curr_idx[0] + pad_top,  self.curr_idx[1] + pad_left)

    def update_pose(self, x, y, z, quat):
        """
        - Converts pose → grid
        - Expands map if needed
        - Marks current cell free & visited
        - Updates self.yaw from quaternion
        """
        # 1) parse yaw from quaternion
        r = R.from_quat(quat)               # quat = [qx, qy, qz, qw]
        _, _, yaw_rad = r.as_euler('xyz')
        self.yaw = math.degrees(yaw_rad)

        # 2) grid index
        gx, gy = self.world_to_grid(x, y)
        self.ensure_in_map(gx, gy)
        self.curr_idx = (gx, gy)

        # 3) mark free & visited
        self.occ_map[gx, gy] = self.free
        self.visited[gx, gy] = True

    def get_frontier(self):
        """
        Return list of neighbor indices (4‐connected) of current cell
        that are still unknown (occ_map = -1).
        """
        front = []
        x0, y0 = self.curr_idx
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x0 + dx, y0 + dy
            # ensure in map before lookup
            self.ensure_in_map(nx, ny)
            if self.occ_map[nx, ny] == self.unknown:
                front.append((nx, ny))
        return front

    def rotate_to(self, target_yaw):
        """
        Rotate the drone to face target_yaw (deg).
        Positive yaw_diff → cw, negative → ccw.
        """
        diff = (target_yaw - self.yaw + 180) % 360 - 180
        if diff > 0:
            self.tello.rotate_clockwise(int(diff))
        elif diff < 0:
            self.tello.rotate_counter_clockwise(int(-diff))
        # give the drone a moment to settle
        time.sleep(0.5)
        self.yaw = target_yaw

    def move_one_cell(self, goal_idx):
        """
        1) Compute heading
        2) Rotate to face it
        3) Move forward one cell
        """
        x0, y0 = self.curr_idx
        x1, y1 = goal_idx
        dx, dy = x1 - x0, y1 - y0

        # world‐frame heading
        yaw_goal = math.degrees(math.atan2(dy, dx))
        self.rotate_to(yaw_goal)

        # forward distance in cm
        dist_m = math.hypot(dx, dy) * self.resolution
        self.tello.move_forward(int(dist_m * 100))

    def choose_next_goal(self):
        f = self.get_frontier()
        return f[0] if f else None

    def get_pose_input(self):
        """
        Replace this stub with your actual pose source.
        Should return (x, y, z, (qx, qy, qz, qw)).
        """
        return None

    def run(self):
        self.tello.takeoff()
        while True:
            pose = self.get_pose_input()
            if pose is None:
                print("No more pose updates, landing.")
                break

            self.update_pose(*pose)

            goal = self.choose_next_goal()
            if goal is None:
                print("Exploration complete!")
                break

            self.move_one_cell(goal)

        self.tello.land()

if __name__ == '__main__':
    explorer = TelloExplorer(resolution=0.5, init_size=50)
    explorer.run()