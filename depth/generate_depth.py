import os
import cv2
import numpy as np
import torch
from tqdm import tqdm

# Add DepthAnythingV2 to path
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

# Support both layouts:
# 1) Vision-Based-Pothole-Detection/Depth-Anything-V2
# 2) ../Depth-Anything-V2 (sibling of project root)
DEPTH_ANYTHING_CANDIDATES = [
    os.path.join(PROJECT_ROOT, "Depth-Anything-V2"),
    os.path.abspath(os.path.join(PROJECT_ROOT, "..", "Depth-Anything-V2")),
]

DEPTH_ANYTHING_ROOT = next(
    (p for p in DEPTH_ANYTHING_CANDIDATES if os.path.isdir(p)), None
)
if DEPTH_ANYTHING_ROOT is None:
    raise FileNotFoundError(
        "Could not find Depth-Anything-V2. Expected one of: "
        + ", ".join(DEPTH_ANYTHING_CANDIDATES)
    )

sys.path.append(DEPTH_ANYTHING_ROOT)

from depth_anything_v2.dpt import DepthAnythingV2

# -------------------------
# CONFIG
# -------------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

MODEL_PATH = os.path.join(
    DEPTH_ANYTHING_ROOT, "checkpoints", "depth_anything_v2_vits.pth"
)

DATA_PATHS = {
    "train": os.path.join(PROJECT_ROOT, "merged_dataset", "train", "images"),
    "valid": os.path.join(PROJECT_ROOT, "merged_dataset", "valid", "images"),
    "test": os.path.join(PROJECT_ROOT, "merged_dataset", "test", "images"),
}

OUTPUT_PATH = os.path.join(PROJECT_ROOT, "depth_maps_merged")

# -------------------------
# LOAD MODEL
# -------------------------
model = DepthAnythingV2(encoder="vits", features=64, out_channels=[48, 96, 192, 384])
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.to(DEVICE).eval()


# -------------------------
# FUNCTION: process one image
# -------------------------
def get_depth(image):
    depth = model.infer_image(image)
    return depth


# -------------------------
# MAIN LOOP
# -------------------------
for split in DATA_PATHS:
    input_dir = DATA_PATHS[split]
    output_dir = os.path.join(OUTPUT_PATH, split)

    os.makedirs(output_dir, exist_ok=True)

    images = os.listdir(input_dir)

    print(f"\nProcessing {split}...")

    for img_name in tqdm(images):
        img_path = os.path.join(input_dir, img_name)

        # Read image
        image = cv2.imread(img_path)
        if image is None:
            continue

        # Get depth
        depth = get_depth(image)

        # Normalize depth (IMPORTANT)
        depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)

        # Save as .npy
        save_name = os.path.splitext(img_name)[0] + ".npy"
        save_path = os.path.join(output_dir, save_name)

        np.save(save_path, depth)

print("\nDepth maps generated successfully!")
