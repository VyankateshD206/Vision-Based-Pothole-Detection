import os
from typing import List, Tuple

import cv2
import numpy as np
from ultralytics import YOLO


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_CANDIDATES = [
    os.path.join(SCRIPT_DIR, "yolo-segmentation", "model", "best.pt"),
    os.path.join(SCRIPT_DIR, "model", "best.pt"),
]

MODEL_PATH = next((path for path in MODEL_CANDIDATES if os.path.isfile(path)), None)
if MODEL_PATH is None:
    raise FileNotFoundError(
        "Could not find pretrained weights 'best.pt'. Expected one of: "
        + ", ".join(MODEL_CANDIDATES)
    )

# Load YOLOv8 segmentation model once and reuse it for inference calls.
MODEL = YOLO(MODEL_PATH)


def _extract_binary_masks(
    image: np.ndarray,
    model: YOLO,
    conf_threshold: float = 0.25,
    min_area: int = 100,
) -> List[np.ndarray]:
    """Return all pothole masks sorted by descending area."""
    height, width = image.shape[:2]
    results = model.predict(source=image, imgsz=640, conf=conf_threshold, verbose=False)
    result = results[0]

    if result.masks is None or len(result.masks.data) == 0:
        return []

    masks = result.masks.data.detach().cpu().numpy()
    binary_masks = (masks > 0.5).astype(np.uint8)

    filtered_masks = []
    for m in binary_masks:
        if m.shape != (height, width):
            m = cv2.resize(m, (width, height), interpolation=cv2.INTER_NEAREST)
            m = (m > 0).astype(np.uint8)

        area = int(m.sum())
        if area >= min_area:
            filtered_masks.append((area, m))

    filtered_masks.sort(key=lambda x: x[0], reverse=True)
    return [mask for _, mask in filtered_masks]


def get_pothole_mask(image_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run YOLOv8 segmentation on an image and return the largest pothole mask.

    Args:
        image_path: Path to input image.

    Returns:
        A tuple of (binary_mask, original_image) where:
        - binary_mask is an HxW np.uint8 array containing values {0, 1}
        - original_image is the loaded image in OpenCV BGR format
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Unable to read image: {image_path}")

    height, width = image.shape[:2]
    all_masks = _extract_binary_masks(image=image, model=MODEL, conf_threshold=0.25)
    if not all_masks:
        return np.zeros((height, width), dtype=np.uint8), image

    largest_mask = all_masks[0]

    return largest_mask, image

def get_largest_mask(img_path):
    mask, _ = get_pothole_mask(img_path)
    return mask

def get_all_masks(
    image_path,
    model_path="yolo-segmentation/model/best.pt",
    conf_threshold=0.25,
    min_area=100,
):
    image = cv2.imread(str(image_path))
    if image is None:
        return []

    # Uses the same model loading approach as get_largest_mask()
    if os.path.exists(model_path):
        model = YOLO(model_path) if os.path.abspath(model_path) != os.path.abspath(MODEL_PATH) else MODEL
    else:
        model = MODEL
        
    return _extract_binary_masks(
        image=image,
        model=model,
        conf_threshold=conf_threshold,
        min_area=min_area,
    )

def get_mask_contour(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest_contour = max(contours, key=cv2.contourArea)
    return largest_contour
