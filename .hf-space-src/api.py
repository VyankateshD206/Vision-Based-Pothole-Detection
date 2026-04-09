import base64
import csv
import os
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# Import existing pipeline methods
from segmentation import get_all_masks
from inference import (
    get_depth_map,
    extract_ml_features,
    load_ml_artifacts,
    SEVERITY_MAP,
)
from features import extract_depth_features
from classifier import classify_severity

app = FastAPI(title="Pothole Detection API")
PROJECT_ROOT = Path(__file__).resolve().parent
ML_RESULTS_DIR = PROJECT_ROOT / "ml_results"


def _get_allowed_origins() -> List[str]:
    """Read allowed frontend origins from env; keep local defaults for development."""
    configured = os.getenv("FRONTEND_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if origins:
        return origins

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


ALLOWED_ORIGINS = _get_allowed_origins()

SEVERITY_WEIGHT = {
    "No Pothole": 0,
    "No pothole": 0,
    "Shallow": 1,
    "Moderate": 2,
    "Deep": 3,
}

SEVERITY_COLORS_BGR = {
    "No Pothole": (0, 255, 0),
    "Shallow": (0, 255, 255),
    "Moderate": (0, 165, 255),
    "Deep": (0, 0, 255),
}

GRAPH_CATEGORY_MAP = [
    ("accuracy_", "Accuracy"),
    ("ablation_", "Ablation"),
    ("calibration_", "Calibration"),
    ("bootstrap_", "Bootstrap"),
    ("confusion_matrix_", "Confusion Matrix"),
    ("feature_correlation", "Feature Relationships"),
    ("kmeans_", "Clustering"),
    ("learning_curve_", "Learning Curves"),
    ("shap_", "SHAP"),
    ("tsne_", "Embeddings"),
    ("umap_", "Embeddings"),
]

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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


def draw_labeled_bbox(
    image: np.ndarray,
    bbox: tuple,
    lines: list,
    box_color=(0, 0, 255),
) -> None:
    """Draw a bounding box and a readable multi-line label block."""
    x1, y1, x2, y2 = bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), box_color, 2)

    if not lines:
        return

    line_h = 20
    text_w = max(cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0][0] for text in lines)
    pad = 8
    box_w = text_w + 2 * pad
    box_h = line_h * len(lines) + 2 * pad

    x_text = max(5, min(x1, image.shape[1] - box_w - 5))
    y_text = y1 - box_h - 8
    if y_text < 5:
        y_text = min(image.shape[0] - box_h - 5, y2 + 8)

    overlay = image.copy()
    cv2.rectangle(overlay, (x_text, y_text), (x_text + box_w, y_text + box_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, image, 0.45, 0, image)

    for idx, text in enumerate(lines):
        y = y_text + pad + 14 + idx * line_h
        cv2.putText(
            image,
            text,
            (x_text + pad, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def normalize_severity(label: str) -> str:
    if label == "No pothole":
        return "No Pothole"
    return label


def severity_rank(label: str) -> int:
    return SEVERITY_WEIGHT.get(label, 0)


def majority_vote(verdicts: List[str]) -> Tuple[str, int, int]:
    if not verdicts:
        return "No Pothole", 0, 0

    counts = {v: verdicts.count(v) for v in set(verdicts)}
    ranked = sorted(
        counts.items(),
        key=lambda item: (item[1], severity_rank(item[0])),
        reverse=True,
    )
    winner = ranked[0][0]
    return winner, counts[winner], len(verdicts)


def mask_to_bbox(mask: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    ys, xs = np.where(mask > 0)
    if xs.size == 0 or ys.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def feature_bundle(depth_features: Optional[Dict[str, float]]) -> Dict[str, float]:
    if not depth_features:
        return {
            "pothole_area": 0,
            "max_depth": 0.0,
            "mean_depth": 0.0,
            "depth_std": 0.0,
            "depth_range": 0.0,
            "p90_depth": 0.0,
            "local_depth_contrast": 0.0,
        }

    return {
        "pothole_area": int(depth_features.get("area", 0)),
        "max_depth": float(depth_features.get("max_depth", 0.0)),
        "mean_depth": float(depth_features.get("mean_depth", 0.0)),
        "depth_std": float(depth_features.get("depth_std", 0.0)),
        "depth_range": float(depth_features.get("depth_range", 0.0)),
        "p90_depth": float(depth_features.get("p90_depth", 0.0)),
        "local_depth_contrast": float(depth_features.get("local_depth_contrast", 0.0)),
    }


def build_schematic_image(image_shape: Tuple[int, int, int], potholes: List[Dict[str, object]]) -> np.ndarray:
    h, w = image_shape[:2]
    schematic = np.zeros((h, w, 3), dtype=np.uint8)

    for pothole in potholes:
        bbox = pothole.get("bbox")
        if not bbox:
            continue

        severity = str(pothole.get("consensusSeverity", "No Pothole"))
        color = SEVERITY_COLORS_BGR.get(severity, (255, 255, 255))
        x1, y1, x2, y2 = int(bbox["x1"]), int(bbox["y1"]), int(bbox["x2"]), int(bbox["y2"])

        cv2.rectangle(schematic, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            schematic,
            f"P{pothole.get('id', 0)} {severity}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

    cv2.putText(
        schematic,
        "Schematic: Per-pothole bounding boxes and severity",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (220, 220, 220),
        2,
        cv2.LINE_AA,
    )
    return schematic


def _safe_results_file(file_name: str) -> Path:
    """Resolve a file under ml_results while preventing path traversal."""
    if not file_name or "/" in file_name or "\\" in file_name:
        raise HTTPException(status_code=400, detail="Invalid file name")

    target = (ML_RESULTS_DIR / file_name).resolve()
    results_root = ML_RESULTS_DIR.resolve()

    if not str(target).startswith(str(results_root)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return target


@app.get("/healthz")
async def healthz():
    return {"success": True, "status": "ok"}


def _parse_classification_report(report_path: Path) -> Optional[Dict[str, object]]:
    """Extract accuracy and macro F1 from sklearn text classification reports."""
    text = report_path.read_text(encoding="utf-8", errors="ignore")

    acc_match = re.search(r"accuracy\s+([0-9]*\.?[0-9]+)", text)
    macro_match = re.search(
        r"macro avg\s+([0-9]*\.?[0-9]+)\s+([0-9]*\.?[0-9]+)\s+([0-9]*\.?[0-9]+)",
        text,
    )

    if not acc_match:
        return None

    model_name = report_path.stem.replace("classification_report_", "")
    return {
        "model": model_name,
        "accuracy": float(acc_match.group(1)),
        "macroF1": float(macro_match.group(3)) if macro_match else None,
        "reportFile": report_path.name,
    }


def _load_ablation_rows() -> List[Dict[str, object]]:
    """Load ablation study rows if available."""
    ablation_path = ML_RESULTS_DIR / "ablation_study.csv"
    if not ablation_path.is_file():
        return []

    rows: List[Dict[str, object]] = []
    with ablation_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            rows.append(
                {
                    "subset": row.get("Feature Subset", "Unknown"),
                    "numFeatures": int(float(row.get("Num Features", 0))),
                    "valAccuracy": float(row.get("Val Accuracy", 0.0)),
                    "macroF1": float(row.get("Macro F1", 0.0)),
                }
            )
    return rows


def _load_feature_rows(max_rows: int = 1200) -> Dict[str, object]:
    """Load numeric feature rows for interactive scatter exploration."""
    candidate_paths = [
        ML_RESULTS_DIR / "valid_features.csv",
        ML_RESULTS_DIR / "train_features.csv",
    ]
    data_path = next((p for p in candidate_paths if p.is_file()), None)
    if data_path is None:
        return {"columns": [], "rows": []}

    rows: List[Dict[str, object]] = []
    feature_columns: List[str] = []

    with data_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames:
            feature_columns = [
                c for c in reader.fieldnames if c not in {"img_name", "severity_name", "pothole_idx"}
            ]

        for idx, row in enumerate(reader):
            if idx >= max_rows:
                break

            normalized: Dict[str, object] = {
                "imageName": row.get("img_name", ""),
                "severity": row.get("severity_name", "Unknown"),
            }

            for col in feature_columns:
                value = row.get(col, "")
                try:
                    normalized[col] = float(value)
                except (TypeError, ValueError):
                    normalized[col] = 0.0

            rows.append(normalized)

    return {
        "columns": feature_columns,
        "rows": rows,
    }


def _graph_category(file_name: str) -> str:
    lower = file_name.lower()
    for prefix, category in GRAPH_CATEGORY_MAP:
        if lower.startswith(prefix):
            return category
    return "Other"


def _build_graph_manifest() -> List[Dict[str, str]]:
    """Build graph manifest for all PNG outputs in ml_results."""
    if not ML_RESULTS_DIR.is_dir():
        return []

    graphs = []
    for png_path in sorted(ML_RESULTS_DIR.glob("*.png")):
        display_name = png_path.stem.replace("_", " ").title()
        graphs.append(
            {
                "file": png_path.name,
                "title": display_name,
                "category": _graph_category(png_path.name),
                "url": f"/insights/files/{png_path.name}",
            }
        )
    return graphs


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # 1. Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        contents = await file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # ── 1. Read image and segment all potholes ──
        original_image = cv2.imread(tmp_path)
        if original_image is None:
            raise FileNotFoundError("Unable to read uploaded image")

        masks = get_all_masks(tmp_path)

        # ── 2. Depth estimation ──
        depth_map = get_depth_map(original_image)
        if depth_map.shape != original_image.shape[:2]:
            depth_map = cv2.resize(
                depth_map,
                (original_image.shape[1], original_image.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )

        # ── 3. Load ML artifacts once ──
        scaler = None
        ml_models = {}
        try:
            scaler, ml_models = load_ml_artifacts()
        except FileNotFoundError:
            scaler, ml_models = None, {}

        expected_features = int(getattr(scaler, "n_features_in_", 11)) if scaler is not None else 11

        # ── 4. Per-pothole analysis ──
        potholes: List[Dict[str, object]] = []
        mask_records: List[Tuple[np.ndarray, Dict[str, object]]] = []

        for idx, mask in enumerate(masks, start=1):
            depth_features = extract_depth_features(mask, depth_map)
            if depth_features is None:
                continue

            rule_severity = normalize_severity(classify_severity(depth_features))
            ml_predictions: Dict[str, str] = {}

            ml_feature_vec = extract_ml_features(mask, depth_map, expected_features)
            if ml_feature_vec is not None and scaler is not None and ml_models:
                X_scaled = scaler.transform(ml_feature_vec)
                for name, model in ml_models.items():
                    label = int(model.predict(X_scaled)[0])
                    severity = normalize_severity(SEVERITY_MAP.get(label, f"Unknown({label})"))
                    display_name = name.replace("_", " ").title()
                    if name == "svm":
                        display_name = "SVM (RBF Kernel)"
                    ml_predictions[display_name] = severity

            classifications = {
                "Rule-Based": rule_severity,
                **ml_predictions,
            }

            consensus, consensus_count, total_classifiers = majority_vote(
                list(classifications.values())
            )

            bbox = mask_to_bbox(mask)
            bbox_obj = None
            if bbox is not None:
                bbox_obj = {
                    "x1": int(bbox[0]),
                    "y1": int(bbox[1]),
                    "x2": int(bbox[2]),
                    "y2": int(bbox[3]),
                }

            features = feature_bundle(depth_features)
            pothole = {
                "id": int(idx),
                "bbox": bbox_obj,
                "features": features,
                "classifications": classifications,
                "consensusSeverity": str(consensus),
                "consensusCount": int(consensus_count),
                "totalClassifiers": int(total_classifiers),
            }
            potholes.append(pothole)
            mask_records.append((mask, pothole))

        # Choose one representative pothole for backward-compatible fields.
        representative = None
        if potholes:
            representative = max(
                potholes,
                key=lambda p: (
                    severity_rank(str(p["consensusSeverity"])),
                    float(p["features"].get("pothole_area", 0)),
                ),
            )

        # ── 5. Build Visualization Images ──
        img_original = encode_image(original_image)

        overlay_mask = original_image.copy()
        for mask, pothole in mask_records:
            severity = str(pothole["consensusSeverity"])
            color = SEVERITY_COLORS_BGR.get(severity, (255, 255, 255))

            tint = np.zeros_like(original_image)
            tint[:, :, 0] = color[0]
            tint[:, :, 1] = color[1]
            tint[:, :, 2] = color[2]
            blended = cv2.addWeighted(original_image, 0.45, tint, 0.55, 0)
            overlay_mask[mask == 1] = blended[mask == 1]

            bbox_obj = pothole.get("bbox")
            if bbox_obj is not None:
                bbox = (
                    int(bbox_obj["x1"]),
                    int(bbox_obj["y1"]),
                    int(bbox_obj["x2"]),
                    int(bbox_obj["y2"]),
                )
                lines = [
                    f"P{pothole['id']}: {severity}",
                    f"Area: {pothole['features'].get('pothole_area', 0)}",
                    f"Drop: {pothole['features'].get('local_depth_contrast', 0.0):.3f}",
                ]
                draw_labeled_bbox(overlay_mask, bbox, lines, box_color=color)

        img_mask = encode_image(overlay_mask)

        depth_norm = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        depth_heatmap = cv2.applyColorMap(depth_norm, cv2.COLORMAP_INFERNO)
        img_depth = encode_image(depth_heatmap)

        schematic_img = build_schematic_image(original_image.shape, potholes)
        img_schematic = encode_image(schematic_img)

        if representative is None:
            consensus_text = "No Pothole"
            consensus_subtext = "Detected by 1 of 1 classifiers"
            features = feature_bundle(None)
            classifications = {"Rule-Based": "No Pothole"}
            consensus_count = 1
            total_classifiers = 1
            bbox = None
        else:
            consensus_text = str(representative["consensusSeverity"])
            pothole_count = len(potholes)
            consensus_subtext = f"Worst severity among {pothole_count} pothole(s)"
            features = representative["features"]
            classifications = representative["classifications"]
            consensus_count = int(representative["consensusCount"])
            total_classifiers = int(representative["totalClassifiers"])
            bbox = representative["bbox"]

        return JSONResponse(
            {
                "success": True,
                "potholeCount": len(potholes),
                "consensusSeverity": consensus_text,
                "consensusSubtext": consensus_subtext,
                "consensusCount": consensus_count,
                "totalClassifiers": total_classifiers,
                "features": features,
                "classifications": classifications,
                "potholes": potholes,
                "images": {
                    "original": img_original,
                    "maskOverlay": img_mask,
                    "depthHeatmap": img_depth,
                    "schematic": img_schematic,
                },
                "bbox": bbox,
            }
        )

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/insights/summary")
async def insights_summary():
    """Return structured model-performance data and graph manifest for the UI."""
    if not ML_RESULTS_DIR.is_dir():
        return JSONResponse(
            {
                "success": False,
                "error": "ml_results directory not found",
                "metrics": [],
                "ablation": [],
                "featureColumns": [],
                "featureRows": [],
                "graphs": [],
            },
            status_code=404,
        )

    metrics: List[Dict[str, object]] = []
    for report_path in sorted(ML_RESULTS_DIR.glob("classification_report_*.txt")):
        parsed = _parse_classification_report(report_path)
        if parsed is not None:
            metrics.append(parsed)

    metrics.sort(key=lambda row: row.get("accuracy", 0.0), reverse=True)
    top_model = metrics[0] if metrics else None

    ablation_rows = _load_ablation_rows()
    feature_data = _load_feature_rows(max_rows=1200)
    graphs = _build_graph_manifest()

    return JSONResponse(
        {
            "success": True,
            "topModel": top_model,
            "metrics": metrics,
            "ablation": ablation_rows,
            "featureColumns": feature_data["columns"],
            "featureRows": feature_data["rows"],
            "graphs": graphs,
            "totalGraphs": len(graphs),
        }
    )


@app.get("/insights/files/{file_name}")
async def insights_file(file_name: str):
    """Serve image/text/csv artifacts from ml_results for insights dashboard."""
    allowed_ext = {".png", ".txt", ".csv"}
    suffix = Path(file_name).suffix.lower()
    if suffix not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported file extension")

    target = _safe_results_file(file_name)
    return FileResponse(path=str(target), filename=target.name)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() in {"1", "true", "yes"}
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=reload_enabled)
