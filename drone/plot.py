"""
Minimal 3‑D matplotlib visualizer for camera poses (position + quaternion).

• Each frame is drawn as:
    – a small colored dot (sequence‑specific color) at the XYZ position
    – three short axis arrows showing the local +X (red), +Y (green), +Z (blue)

• Two independent sequences are shown; feel free to add more.

Requires:
    numpy
    matplotlib
    scipy  (for quaternion → rotation‑matrix conversion)

Install extras if needed:
    pip install matplotlib scipy
"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401 (needed for 3‑D)
from scipy.spatial.transform import Rotation as R

# ---------------------------------------------------------------------
# ❶  Hard‑coded input ─ replace with your own loader as necessary
seq_A_xyz = np.array([
    [ 1.9322391e-05, -2.6811851e-05,  1.5158137e-05],
    [-0.5019823,     -0.00118865,     0.14657676 ],
    [-0.8087555,      0.03690614,     0.4450592  ],
])

seq_A_quat = np.array([               # (x, y, z, w) ordering
    [-1.9245799e-05, -7.3398023e-06, -2.6055341e-05,  1.0000055e+00],
    [ 0.03918747,     0.23449253,     0.06902833,     0.96866846   ],
    [ 0.10025221,     0.3627328,      0.13004833,     0.9172508    ],
])

seq_B_xyz = np.array([
    [-2.1763375e-05, -8.3483856e-06, -7.9573529e-06],
    [-0.68498796,    -0.5114615,      0.510086   ],
    [-0.4691723,     -0.356645,       0.24670483 ],
])

seq_B_quat = np.array([
    [-5.0753106e-06, -4.3749616e-05, -2.5560847e-05,  9.9999899e-01],
    [-0.13955887,     0.4832751,      0.3510147,      0.7899206   ],
    [-0.08210269,     0.3137512,      0.30112997,     0.8966248   ],
])

# Put sequences in a list for compact iteration
sequences = [
    dict(name="Seq A", xyz=seq_A_xyz, quat=seq_A_quat, color="tab:orange"),
    dict(name="Seq B", xyz=seq_B_xyz, quat=seq_B_quat, color="tab:purple"),
]

# ---------------------------------------------------------------------
# ❷  Figure / axes setup
fig = plt.figure(figsize=(7, 6))
ax: Axes3D = fig.add_subplot(111, projection="3d")
ax.set_box_aspect([1, 1, 1])  # equal aspect ratio

# ---------------------------------------------------------------------
# ❸  Helper to draw one camera pose
def draw_pose(origin: np.ndarray, rot: R, length: float = 0.05):
    """Draw a right‑handed coordinate frame at `origin` using `rot` (Rotation)."""
    axes = rot.apply(np.eye(3))  # world‑space directions of camera’s +X,+Y,+Z
    colors = ["r", "g", "b"]
    for vec, c in zip(axes, colors):
        ax.quiver(
            origin[0], origin[1], origin[2],     # tail
            vec[0], vec[1], vec[2],              # direction
            length=length, color=c, linewidth=1,
        )

# ---------------------------------------------------------------------
# ❹  Plot every sequence
for seq in sequences:
    xyz, quat, clr = seq["xyz"], seq["quat"], seq["color"]

    # Trajectory line + points
    ax.plot(xyz[:, 0], xyz[:, 1], xyz[:, 2],
            marker="o", markersize=4, color=clr,
            label=seq["name"])

    # Coordinate frames
    for p, q in zip(xyz, quat):
        draw_pose(p, R.from_quat(q))

# ---------------------------------------------------------------------
# ❺  Cosmetics
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Camera trajectories with orientation frames")
ax.legend()
plt.tight_layout()
plt.show()
