"""
Unified Pothole Severity Inference Pipeline
============================================
Takes an image path, runs YOLO segmentation + DepthAnythingV2 depth estimation,
then classifies severity using:
  1. Rule-based manual thresholds  (existing classifier.py)
  2. Saved ML models              (from ml_classifier.py training)

Usage:
    python inference.py <image_path> [--output_dir OUTPUT] [--no_show]
"""

import argparse
import os
import sys
from typing import Dict, List, Optional, Tuple

import cv2
import joblib
import matplotlib.pyplot as plt
import numpy as np

# ── project imports ──────────────────────────────────────────────────────────
from classifier import classify_severity          # rule-based
from features import extract_depth_features       # depth feature dict
from segmentation import get_pothole_mask         # YOLO segmentation

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "ml_models")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

# Feature column order – MUST match ml_classifier.py training exactly
FEATURE_COLS = [
    "height", "width", "box_area", "pothole_area", "nonpothole_area",
    "mean_depth", "max_depth", "min_depth", "depth_std", "depth_range",
    "p90_depth",
]

SEVERITY_MAP = {0: "Shallow", 1: "Moderate", 2: "Deep"}

# ML model file names (stem only, stored as .pkl)
ML_MODEL_NAMES = [
    "logistic_regression",
    "random_forest",
    "svm",
    "naive_bayes",
]


# ── Depth model (lazy-loaded singleton) ──────────────────────────────────────
_DEPTH_MODEL = None


def _resolve_depth_anything_root() -> str:
    candidates = [
        os.path.join(SCRIPT_DIR, "Depth-Anything-V2"),
        os.path.abspath(os.path.join(SCRIPT_DIR, "..", "Depth-Anything-V2")),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    raise FileNotFoundError(
        "Could not find Depth-Anything-V2. Looked in: " + ", ".join(candidates)
    )


def _load_depth_model():
    global _DEPTH_MODEL
    if _DEPTH_MODEL is not None:
        return _DEPTH_MODEL

    import torch

    depth_root = _resolve_depth_anything_root()
    if depth_root not in sys.path:
        sys.path.append(depth_root)

    from depth_anything_v2.dpt import DepthAnythingV2

    ckpt = os.path.join(depth_root, "checkpoints", "depth_anything_v2_vits.pth")
    if not os.path.isfile(ckpt):
        raise FileNotFoundError(f"Depth checkpoint not found: {ckpt}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DepthAnythingV2(
        encoder="vits", features=64, out_channels=[48, 96, 192, 384]
    )
    model.load_state_dict(torch.load(ckpt, map_location=device))
    model.to(device).eval()
    _DEPTH_MODEL = model
    return _DEPTH_MODEL


def get_depth_map(image: np.ndarray) -> np.ndarray:
    """Infer an HxW float32 depth map (raw values) from a BGR image."""
    model = _load_depth_model()
    depth = model.infer_image(image).astype(np.float32)
    if depth.shape != image.shape[:2]:
        depth = cv2.resize(
            depth, (image.shape[1], image.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )
    return depth


# ── ML helpers ───────────────────────────────────────────────────────────────
def load_ml_artifacts() -> Tuple[object, Dict[str, object]]:
    """Load scaler + all trained ML models from disk."""
    scaler_path = os.path.join(MODELS_DIR, "feature_scaler.pkl")
    if not os.path.isfile(scaler_path):
        raise FileNotFoundError(
            f"Feature scaler not found at {scaler_path}. "
            "Run ml_classifier.py first to train models."
        )
    scaler = joblib.load(scaler_path)

    models: Dict[str, object] = {}
    for name in ML_MODEL_NAMES:
        path = os.path.join(MODELS_DIR, f"{name}.pkl")
        if os.path.isfile(path):
            models[name] = joblib.load(path)
        else:
            print(f"  ⚠  Model file not found, skipping: {path}")
    return scaler, models


def extract_ml_features(
    mask: np.ndarray, depth_map: np.ndarray
) -> Optional[np.ndarray]:
    """
    Given a binary pothole mask and a depth map, extract the 11-dim feature
    vector expected by the ML models (same order as FEATURE_COLS).
    """
    h, w = mask.shape[:2]

    pothole_area = int(np.sum(mask))
    if pothole_area == 0:
        return None

    # Bounding-box geometry
    ys, xs = np.where(mask == 1)
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    p_width = max(1, x_max - x_min)
    p_height = max(1, y_max - y_min)
    box_area = p_width * p_height
    nonpothole_area = max(0, box_area - pothole_area)

    # Depth statistics (depth_map is raw; normalize to [0,1] first)
    d = depth_map.astype(np.float32)
    d_min_all, d_max_all = float(d.min()), float(d.max())
    if d_max_all > d_min_all:
        d = (d - d_min_all) / (d_max_all - d_min_all)
    else:
        d = np.zeros_like(d)

    depth_values = d[mask == 1]
    if len(depth_values) == 0:
        return None

    max_depth = float(np.max(depth_values))
    min_depth = float(np.min(depth_values))
    mean_depth = float(np.mean(depth_values))
    depth_std = float(np.std(depth_values))
    depth_range = max_depth - min_depth
    p90_depth = float(np.percentile(depth_values, 90))

    # Return in FEATURE_COLS order
    return np.array([
        p_height, p_width, box_area, pothole_area, nonpothole_area,
        mean_depth, max_depth, min_depth, depth_std, depth_range, p90_depth,
    ]).reshape(1, -1)


# ── main pipeline ────────────────────────────────────────────────────────────
def run_inference(
    image_path: str,
    output_dir: Optional[str] = None,
    show: bool = True,
) -> None:
    """
    Full inference pipeline:
      segmentation ➜ depth ➜ features ➜ rule-based + ML predictions.
    """
    print(f"\n{'='*60}")
    print(f"  Pothole Severity Inference Pipeline")
    print(f"  Image: {image_path}")
    print(f"{'='*60}\n")

    # ── 1. Segmentation ─────────────────────────────────────────────────────
    print("[1/4] Running YOLO segmentation...")
    mask, original_image = get_pothole_mask(image_path)

    # ── 2. Depth estimation ──────────────────────────────────────────────────
    print("[2/4] Estimating depth map (DepthAnythingV2)...")
    depth_map = get_depth_map(original_image)
    if mask.shape != depth_map.shape:
        depth_map = cv2.resize(
            depth_map, (mask.shape[1], mask.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )

    # ── 3. Feature extraction ────────────────────────────────────────────────
    print("[3/4] Extracting features...")
    depth_features = extract_depth_features(mask, depth_map)
    ml_feature_vec = extract_ml_features(mask, depth_map)

    # ── 4. Classification ────────────────────────────────────────────────────
    print("[4/4] Classifying severity...\n")

    # ─── 4a. Rule-based ──────────────────────────────────────────────────────
    rule_severity = classify_severity(depth_features)
    print(f"  ┌─ Rule-Based Classifier (Manual Thresholds)")
    print(f"  │   Severity:  {rule_severity}")
    if depth_features:
        print(f"  │   max_depth: {depth_features['max_depth']:.4f}")
        print(f"  │   area:      {depth_features['area']}")
    print(f"  └{'─'*50}\n")

    # ─── 4b. ML models ───────────────────────────────────────────────────────
    if ml_feature_vec is not None:
        scaler, ml_models = load_ml_artifacts()
        X_scaled = scaler.transform(ml_feature_vec)

        print(f"  ┌─ ML-Based Classifiers")
        ml_predictions = {}
        for name, model in ml_models.items():
            label = int(model.predict(X_scaled)[0])
            severity = SEVERITY_MAP.get(label, f"Unknown({label})")
            ml_predictions[name] = severity
            display_name = name.replace("_", " ").title()
            print(f"  │   {display_name:25s} →  {severity}")
        print(f"  └{'─'*50}\n")
    else:
        ml_predictions = {}
        print("  ⚠  No pothole detected — ML models skipped.\n")

    # ── Visualization ────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Panel 1: Original + severity labels
    overlay = original_image.copy()
    y_offset = 40
    cv2.putText(
        overlay, f"Rule-Based: {rule_severity}",
        (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA,
    )
    for name, sev in ml_predictions.items():
        y_offset += 30
        display_name = name.replace("_", " ").title()
        cv2.putText(
            overlay, f"{display_name}: {sev}",
            (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            (255, 200, 0), 2, cv2.LINE_AA,
        )
    axes[0].imshow(cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB))
    axes[0].set_title("Original + Severity Predictions")
    axes[0].axis("off")

    # Panel 2: Mask overlaid on original image
    overlay_mask = original_image.copy()
    if np.any(mask):
        # Create a red-tinted overlay where mask == 1
        red_layer = np.zeros_like(original_image)
        red_layer[:, :, 2] = 255  # Red channel (BGR)
        blended = cv2.addWeighted(original_image, 0.4, red_layer, 0.6, 0)
        overlay_mask[mask == 1] = blended[mask == 1]
        # Draw bounding box around the pothole region
        ys, xs = np.where(mask == 1)
        x1, y1, x2, y2 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
        cv2.rectangle(overlay_mask, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(
            overlay_mask, "Pothole", (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA,
        )
    axes[1].imshow(cv2.cvtColor(overlay_mask, cv2.COLOR_BGR2RGB))
    axes[1].set_title("Pothole Mask Overlay")
    axes[1].axis("off")

    # Panel 3: Depth heatmap
    depth_norm = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX).astype(
        np.uint8
    )
    depth_heatmap = cv2.applyColorMap(depth_norm, cv2.COLORMAP_JET)
    axes[2].imshow(cv2.cvtColor(depth_heatmap, cv2.COLOR_BGR2RGB))
    axes[2].set_title("Depth Map")
    axes[2].axis("off")

    plt.tight_layout()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(output_dir, f"{stem}_inference.png")
        plt.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"  Saved visualization → {out_path}")

    if show:
        plt.show()
    else:
        plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pothole severity inference (rule-based + ML)"
    )
    parser.add_argument("image_path", help="Path to input image")
    parser.add_argument(
        "--output_dir", default=None,
        help="Directory to save the visualization (default: don't save)",
    )
    parser.add_argument(
        "--no_show", action="store_true",
        help="Suppress interactive plot window",
    )
    args = parser.parse_args()

    run_inference(args.image_path, output_dir=args.output_dir, show=not args.no_show)


if __name__ == "__main__":
    main()
