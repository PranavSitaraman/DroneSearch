#!/usr/bin/env python3
"""
Two‑scene VGGT → depth‑map → GLB demo (no uploads, no Open3D).

`Run reconstruction`:
    • scene‑1: IMAGE_NAMES  → GLB + depth frame‑0
    • scene‑2: IMAGE2_NAMES → GLB + depth frame‑0
"""

import logging, time, tempfile
from typing import Tuple, List

import gradio as gr
import numpy as np
import torch

from visual_util import predictions_to_glb
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images
from vggt.utils.pose_enc import pose_encoding_to_extri_intri
from vggt.utils.geometry import unproject_depth_map_to_point_map

# ---------------------------------------------------------------------#
# 1.  Static input frames
# ---------------------------------------------------------------------#
IMAGE_NAMES = [
    "examples/kitchen/images/00.png",
    "examples/kitchen/images/01.png",
    "examples/kitchen/images/02.png",
    "examples/kitchen/images/03.png",
]

IMAGE2_NAMES = [
    "examples/kitchen/images/03.png",
    "examples/kitchen/images/04.png",
    "examples/kitchen/images/05.png",
    "examples/kitchen/images/06.png",
]

# ---------------------------------------------------------------------#
# 2.  Model initialisation
# ---------------------------------------------------------------------#
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = (
    torch.bfloat16
    if device == "cuda" and torch.cuda.get_device_capability()[0] >= 8
    else torch.float16
)

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("vggt‑dual‑demo")
LOG.info("Loading VGGT weights …")
model = VGGT.from_pretrained("facebook/VGGT-1B").to(device).eval()

# ---------------------------------------------------------------------#
# 3.  Helper – run one sequence → (glb_path, depth_png)
# ---------------------------------------------------------------------#
@torch.inference_mode()
def _process_sequence(
    img_paths: List[str],
    progress: gr.Progress,
    p0: float,
    p1: float,
    label: str,
) -> Tuple[str, np.ndarray]:
    """
    Reconstruct a single set of images.
    Map overall progress [p0,p1].
    """
    span = p1 - p0
    step = lambda frac, desc: progress(p0 + frac * span, desc=f"{label}: {desc}")

    step(0.0, "loading images")
    imgs = load_and_preprocess_images(img_paths).to(device)[None]  # [1,S,3,H,W]
    S = imgs.shape[1]             
    H = imgs.shape[-2]          
    W = imgs.shape[-1]          

    with torch.autocast(device_type="cuda", dtype=dtype) if device == "cuda" else torch.no_grad():
        step(0.15, "aggregator")
        tokens, ps_idx = model.aggregator(imgs)

        step(0.35, "camera head")
        pose_enc = model.camera_head(tokens)[-1]
        extrinsic, intrinsic = pose_encoding_to_extri_intri(pose_enc, (H, W))

        step(0.55, "depth head")
        depth_map, depth_conf = model.depth_head(tokens, imgs, ps_idx)

    # ---- numpy conversion -------------------------------------------------
    extrinsic = extrinsic.cpu().to(torch.float32).numpy().squeeze(0)
    intrinsic = intrinsic.cpu().to(torch.float32).numpy().squeeze(0)
    depth_map = depth_map.cpu().to(torch.float32).numpy().squeeze(0)
    depth_conf = depth_conf.cpu().to(torch.float32).numpy().squeeze(0)
    
    # Convert images to numpy for the predictions dict
    images_np = imgs.squeeze(0).cpu().permute(0, 2, 3, 1).to(torch.float32).numpy()  # [S,H,W,3]

    step(0.72, "un‑project depth")
    world_pts = unproject_depth_map_to_point_map(depth_map, extrinsic, intrinsic)

    preds = dict(
        depth=depth_map,
        depth_conf=depth_conf,
        pose_enc=pose_enc.cpu().to(torch.float32).numpy().squeeze(0),
        extrinsic=extrinsic,
        intrinsic=intrinsic,
        world_points_from_depth=world_pts,
        images=images_np,  # Add the images to the predictions dictionary
    )

    step(0.84, "to GLB")
    scene = predictions_to_glb(
        preds,
        conf_thres=50.0,
        filter_by_frames="All",
        mask_black_bg=False,
        mask_white_bg=False,
        show_cam=True,
        mask_sky=False,
        target_dir=".",  # not used for temp file
        prediction_mode="Depthmap and Camera Branch",
    )
    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as tmp:
        glb_path = tmp.name
    scene.export(glb_path)

    dm = depth_map[0, ..., 0]
    dm_norm = (dm - dm.min()) / (dm.max() - dm.min() + 1e-9)
    depth_png = (dm_norm * 255).astype(np.uint8)

    step(1.0, "done")
    return glb_path, depth_png

# ---------------------------------------------------------------------#
# 4.  Top‑level reconstruction (handles two sequences)
# ---------------------------------------------------------------------#
def run_both(progress: gr.Progress = gr.Progress(track_tqdm=False)):
    t0 = time.time()
    
    # Process first sequence
    glb1, depth1 = _process_sequence(IMAGE_NAMES, progress, 0.0, 0.5, "Set‑1")
    
    # Extract and print pose information for first sequence
    with torch.inference_mode():
        imgs1 = load_and_preprocess_images(IMAGE_NAMES).to(device)[None]
        tokens1, ps_idx1 = model.aggregator(imgs1)
        pose_enc1 = model.camera_head(tokens1)[-1]
        pose_info1 = pose_enc1.cpu().to(torch.float32).numpy().squeeze(0)
        print("=== Pose information for sequence 1 ===")
        for i, pose in enumerate(pose_info1):
            print(f"Frame {i}: Position XYZ: {pose[0:3]}, Quaternion XYZW: {pose[3:7]}, FOV: {pose[7:9]}")
    
    # Process second sequence
    glb2, depth2 = _process_sequence(IMAGE2_NAMES, progress, 0.5, 1.0, "Set‑2")
    
    # Extract and print pose information for second sequence
    with torch.inference_mode():
        imgs2 = load_and_preprocess_images(IMAGE2_NAMES).to(device)[None]
        tokens2, ps_idx2 = model.aggregator(imgs2)
        pose_enc2 = model.camera_head(tokens2)[-1]
        pose_info2 = pose_enc2.cpu().to(torch.float32).numpy().squeeze(0)
        print("=== Pose information for sequence 2 ===")
        for i, pose in enumerate(pose_info2):
            print(f"Frame {i}: Position XYZ: {pose[0:3]}, Quaternion XYZW: {pose[3:7]}, FOV: {pose[7:9]}")
    
    gr.Info(f"✓ Finished both in {time.time() - t0:.1f}s")
    return glb1, depth1, glb2, depth2

# ---------------------------------------------------------------------#
# 5.  Gradio UI
# ---------------------------------------------------------------------#
with gr.Blocks(title="VGGT – two sequences") as demo:
    gr.Markdown(
        """
### VGGT Depth‑Map Reconstruction × 2  
Reconstructs two fixed image sets (kitchen #0‑2 and #3‑5). Click **Run**.
"""
    )
    run_btn = gr.Button("Run reconstruction", variant="primary")

    with gr.Row():
        with gr.Column():
            viewer1 = gr.Model3D(label="Point cloud #1 (.glb)")
            depth1  = gr.Image(label="Depth #1 (frame‑0)")
        with gr.Column():
            viewer2 = gr.Model3D(label="Point cloud #2 (.glb)")
            depth2  = gr.Image(label="Depth #2 (frame‑0)")

    run_btn.click(run_both, outputs=[viewer1, depth1, viewer2, depth2])

# ---------------------------------------------------------------------#
if __name__ == "__main__":
    demo.launch(share=True, debug=True)
