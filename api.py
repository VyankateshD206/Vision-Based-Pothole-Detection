import base64
import os
import tempfile
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import existing pipeline methods
from segmentation import get_pothole_mask
from inference import (
    get_depth_map,
    extract_ml_features,
    load_ml_artifacts,
    SEVERITY_MAP,
)
from features import extract_depth_features
from classifier import classify_severity

app = FastAPI(title="Pothole Detection API")

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def encode_image(image: np.ndarray) -> str:
    """Encode an OpenCV BGR image as a base64 JPEG string."""
    ret, buffer = cv2.imencode(".jpg", image)
    if not ret:
        return ""
    base64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_str}"


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # 1. Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # ── 1. Segmentation ──
        mask, original_image = get_pothole_mask(tmp_path)

        # ── 2. Depth estimation ──
        depth_map = get_depth_map(original_image)
        if mask.shape != depth_map.shape:
            depth_map = cv2.resize(
                depth_map,
                (mask.shape[1], mask.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )

        # ── 3. Feature extraction ──
        depth_features = extract_depth_features(mask, depth_map)
        ml_feature_vec = extract_ml_features(mask, depth_map)

        # ── 4. Classification ──
        rule_severity = classify_severity(depth_features)
        
        ml_predictions = {}
        if ml_feature_vec is not None:
            # We assume ML models and scaler are in ml_models/ and trained
            scaler, ml_models = load_ml_artifacts()
            X_scaled = scaler.transform(ml_feature_vec)
            for name, model in ml_models.items():
                label = int(model.predict(X_scaled)[0])
                severity = SEVERITY_MAP.get(label, f"Unknown({label})")
                display_name = name.replace("_", " ").title()
                if name == "svm":
                    display_name = "SVM (RBF Kernel)" # match UI
                ml_predictions[display_name] = severity

        # Add Rule-based pred
        classifications = {
            "Rule-Based": rule_severity,
            **ml_predictions
        }

        # ── 5. Build Visualization Images ──
        # Image 1: Original
        img_original = encode_image(original_image)

        # Image 2: Mask Overlay
        overlay_mask = original_image.copy()
        if np.any(mask):
            red_layer = np.zeros_like(original_image)
            red_layer[:, :, 2] = 255  # Red channel
            blended = cv2.addWeighted(original_image, 0.4, red_layer, 0.6, 0)
            overlay_mask[mask == 1] = blended[mask == 1]
            ys, xs = np.where(mask == 1)
            x1, y1, x2, y2 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
            cv2.rectangle(overlay_mask, (x1, y1), (x2, y2), (0, 0, 255), 2)
        img_mask = encode_image(overlay_mask)

        # Image 3: Depth Heatmap (Inferno)
        depth_norm = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        depth_heatmap = cv2.applyColorMap(depth_norm, cv2.COLORMAP_INFERNO)
        img_depth = encode_image(depth_heatmap)


        # Build response features
        if depth_features is None:
            features = {
                "pothole_area": 0,
                "max_depth": 0,
                "mean_depth": 0,
                "depth_std": 0,
                "depth_range": 0,
                "p90_depth": 0
            }
            pothole_count = 0
        else:
            # We must map from the features the Pipeline gives to what the UI expects
            # UI expects: pothole_area, max_depth, mean_depth, depth_std, depth_range, p90_depth
            pothole_count = 1
            features = {
                "pothole_area": depth_features.get('area', 0),
                "max_depth": depth_features.get('max_depth', 0.0),
                "mean_depth": depth_features.get('mean_depth', 0.0),
                "depth_std": depth_features.get('depth_std', 0.0),
                "depth_range": depth_features.get('depth_range', 0.0),
                "p90_depth": depth_features.get('p90_depth', 0.0)
            }


        # Decide final consensus severity
        if pothole_count == 0:
            consensus_text = "No Pothole"
        else:
            # majority vote
            verdicts = list(classifications.values())
            counts = {v: verdicts.count(v) for v in set(verdicts)}
            consensus = max(counts, key=counts.get)
            cnt = counts[consensus]
            tot = len(verdicts)
            consensus_text = consensus
            consensus_subtext = f"Detected by {cnt} of {tot} classifiers"
            
        return JSONResponse({
            "success": True,
            "potholeCount": pothole_count,
            "consensusSeverity": consensus_text,
            "consensusSubtext": "Detected by 1 of 1 classifiers" if pothole_count == 0 else consensus_subtext,
            "features": features,
            "classifications": classifications,
            "images": {
                "original": img_original,
                "maskOverlay": img_mask,
                "depthHeatmap": img_depth
            }
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
