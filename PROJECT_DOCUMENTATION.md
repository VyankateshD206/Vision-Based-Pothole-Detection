# Pothole Intelligence Studio - Complete Project Documentation

## 1. Project Overview

This repository implements an end-to-end pothole analysis system that combines:

1. Pothole segmentation from RGB images.
2. Monocular depth estimation.
3. Rule-based and machine-learning severity classification.
4. Batch road-segment analysis and PDF reporting.
5. A FastAPI backend for inference and model insights.
6. A React web UI with separate Detection and Model Insights workspaces.
7. Dataset engineering scripts for merging multiple pothole datasets.

At runtime, the system can detect **multiple potholes per image**, compute per-pothole features, predict severity from multiple classifiers, compute consensus severity, and return visual + structured outputs.

---

## 2. High-Level Architecture

### 2.1 Main Layers

1. Data layer
- Source datasets: custom/Kaggle segmentation dataset, RDD2022, Pothole-600, GPS-tagged dataset.
- Processing scripts normalize format into one merged YOLO-segmentation-ready dataset.

2. Perception layer
- Segmentation: YOLOv8 segmentation model (`best.pt` by default).
- Depth: Depth-Anything-V2 (`depth_anything_v2_vits.pth`).

3. Feature layer
- Core geometric + depth features.
- Extended shape/statistical features for advanced models.

4. Decision layer
- Rule-based severity classification.
- ML model ensemble and per-model prediction.
- Majority-vote consensus.

5. Service/UI layer
- FastAPI inference endpoints.
- FastAPI model-insights endpoints serving metrics and graphs from `ml_results`.
- React app with dedicated sections:
  - Detection
  - Model Insights

6. Reporting layer
- Batch folder analysis + CSV/JSON/PDF reports.

---

## 3. Repository Structure and Responsibilities

### 3.1 Core Python files

- `main.py`
  - Original single-image pipeline (rule-based focus).
  - Loads mask + depth + features + severity and visualizes output.

- `inference.py`
  - Unified inference pipeline used by backend logic.
  - Multi-pothole support, per-pothole features, per-model predictions, consensus output, visualization + schematic JSON.

- `segmentation.py`
  - Loads YOLO model once.
  - Exposes:
    - `get_pothole_mask(...)` (largest mask)
    - `get_largest_mask(...)`
    - `get_all_masks(...)` (all masks sorted by area)
    - `get_mask_contour(...)`

- `features.py`
  - Extracts pothole depth and geometry features.
  - Exposes:
    - `extract_depth_features(...)`
    - `extract_features(...)`
    - `extract_features_extended(...)`
    - `polygon_surface_area(...)`

- `classifier.py`
  - Rule-based severity classifier based on local depth contrast and roughness.
  - Outputs: `No Pothole`, `Shallow`, `Moderate`, `Deep`.

- `ml_classifier.py`
  - Training/evaluation pipeline for ML severity classification.
  - Supports base and extended feature modes, pseudo-label and real-label workflows.
  - Produces model artifacts and analytics in `ml_results`.

- `api.py`
  - FastAPI server.
  - Endpoints:
    - `POST /analyze`
    - `GET /insights/summary`
    - `GET /insights/files/{file_name}`

- `road_segment_analysis.py`
  - Batch analysis over a folder of road images.
  - Produces per-pothole records + summary + PDF report.

- `test_pipeline.py`
  - Verification script for key modules, artifacts, and imports.

### 3.2 Data and artifact directories

- `data1/`
  - Original dataset layout (`train/valid` images + labels).

- `merged_dataset/`
  - Unified dataset assembled from multiple sources.
  - Contains split folders, `dataset.yaml`, stereo/depth support folders, severity labels.

- `depth_maps_merged/`
  - Depth maps generated for merged dataset.

- `depth_maps_global/`
  - Globally normalized depth maps across all splits.

- `depth_maps_1/`
  - Precomputed depth maps for the original dataset pipeline.

- `ml_models/` and `ml_models/extended/`
  - Saved scalers and trained classifiers.

- `ml_results/`
  - Evaluation outputs (plots, reports, CSVs) consumed by Model Insights.

- `output/`
  - Inference visual outputs and schematics.

- `yolo-segmentation/model/`
  - YOLO segmentation model files (default + retrained variants).

- `Depth-Anything-V2/`
  - External depth model code + checkpoints.

### 3.3 Scripts directory (`scripts/`)

- `convert_rdd2022.py`
  - Imports and converts RDD2022 XML annotations into YOLO polygon labels.
  - Merges into train/valid/test under `merged_dataset`.

- `convert_pothole600.py`
  - Converts Pothole-600 masks/disparity and severity metadata.
  - Adds labels, stereo-derived files, severity labels CSV entries.

- `extract_gps.py`
  - Extracts EXIF GPS coordinates from source images.
  - Sends annotated images to merged splits; unannotated images to `gps/unannotated_images`.

- `deduplicate.py`
  - Hash-based duplicate removal from merged dataset.

- `verify_dataset.py`
  - Structural and annotation validity checks; removes invalid samples.

- `dataset_summary.py`
  - Generates dataset summary text and `dataset.yaml` metadata.

- `retrain_yolo.py`
  - Retrains YOLOv8 segmentation using merged dataset config.

---

## 4. End-to-End Workflows

## 4.1 Dataset Engineering Workflow

Goal: produce one consistent segmentation-ready dataset from multiple sources.

Typical sequence:

1. Start with base data (`data1`) and copy into merged layout.
2. Add RDD2022 potholes (D40 class) converted to YOLO polygons.
3. Add Pothole-600 image/mask/severity/stereo contributions.
4. Add GPS-tagged dataset contributions.
5. Deduplicate by image hash.
6. Verify image-label quality constraints.
7. Generate split/source statistics and final dataset YAML.

Expected outputs:

- `merged_dataset/train|valid|test/images`
- `merged_dataset/train|valid|test/labels`
- `merged_dataset/dataset.yaml`
- `merged_dataset/dataset_stats/final_summary.txt`
- `merged_dataset/severity_labels/pothole600_annotations.csv`
- `gps/image_coordinates.csv`

## 4.2 Depth Workflow

### Step A: Generate depth maps

- Script: `depth/generate_depth.py`
- Current config points to merged dataset splits.
- Produces `.npy` depth files in `depth_maps_merged/{split}`.

### Step B: Global normalization

- Script: `depth/global_normalize.py`
- Pass 1: scans all merged depth maps to find global min/max.
- Saves min/max to `depth_global_stats.npy`.
- Pass 2: normalizes each depth map to [0,1] using global stats.
- Writes to `depth_maps_global/{split}`.

## 4.3 Single-Image Inference Workflow

Implemented in `inference.py` and reused by API logic.

Pipeline:

1. Load image.
2. Segment all potholes (`get_all_masks`).
3. Run depth estimation (Depth-Anything-V2).
4. For each pothole:
- Extract depth/geometric features.
- Compute rule-based severity.
- Build ML feature vector (11 or 20 feature mode by scaler expectation).
- Predict severity from available ML models.
- Compute consensus via majority vote.
5. Select worst severity at image level.
6. Generate visual panel image and schematic JSON.

CLI:

```bash
python inference.py <image_path> --output_dir output --no_show
```

Outputs:

- Visualization image (`*_inference.png`)
- Schematic JSON (`*_schematic.json`)
- Console predictions per model and consensus

## 4.4 Training + Evaluation Workflow

Implemented in `ml_classifier.py`.

### Core behavior

1. Extracts features from dataset splits.
2. Creates pseudo-labels via clustering (`Shallow`, `Moderate`, `Deep`) unless real labels enabled.
3. Optionally mixes in real labels from Pothole-600 severity CSV.
4. Trains classifiers on scaled features.
5. Saves scaler + model artifacts.
6. Runs bootstrap confidence estimation.
7. Runs enhanced evaluations.

### Models trained

- Logistic Regression
- Random Forest
- SVM
- Naive Bayes
- XGBoost
- LightGBM
- KNN
- MLP
- Soft-voting ensemble

### Extended evaluations generated

- Accuracy comparisons
- Bootstrapped distributions
- Confusion matrices per model
- Classification reports per model
- Calibration curves
- SHAP summary/bar plots
- Learning curves
- Feature-correlation heatmap
- t-SNE/UMAP feature-space plots
- Ablation study CSV

### Main output directories

- Models: `ml_models` (and/or `ml_models/extended` depending on script state)
- Results: `ml_results`

## 4.5 YOLO Retraining Workflow

Script: `scripts/retrain_yolo.py`

- Base model: `yolov8n-seg.pt`
- Data config: `merged_dataset/dataset.yaml`
- Trains segmentation model and copies best weights to:
  - `yolo-segmentation/model/best_merged.pt`
- Copies training results figure to:
  - `ml_results/yolo_training_results.png`

## 4.6 Batch Road-Segment Workflow

Script: `road_segment_analysis.py`

Given a folder of road images:

1. Detects potholes per image.
2. Computes depth + features + model predictions.
3. Computes consensus and confidence per pothole.
4. Aggregates severity and repair-priority metrics.
5. Estimates rough volume and rough repair cost.
6. Exports:
- `segment_results.csv`
- `segment_summary.json`
- `road_segment_report.pdf`

Command:

```bash
python road_segment_analysis.py <images_folder> --output_dir output
```

---

## 5. FastAPI Service

File: `api.py`

### 5.1 Endpoint: `POST /analyze`

Input:

- Multipart upload field: `file`

Behavior:

- Saves temporary image.
- Detects all masks.
- Computes per-pothole features and classifier outputs.
- Builds mask overlay, depth heatmap, schematic image.
- Returns image-level consensus and per-pothole details.

Response includes:

- `success`
- `potholeCount`
- `consensusSeverity`
- `consensusSubtext`
- `consensusCount`, `totalClassifiers`
- `features` (representative/worst pothole bundle)
- `classifications` (representative/worst pothole classifiers)
- `potholes` (full per-pothole array)
- `images.original`, `images.maskOverlay`, `images.depthHeatmap`, `images.schematic` (base64)
- `bbox` (representative pothole)

### 5.2 Endpoint: `GET /insights/summary`

Behavior:

- Reads model metrics from `classification_report_*.txt`.
- Reads ablation study from `ablation_study.csv`.
- Loads feature rows from `valid_features.csv` or `train_features.csv`.
- Scans all PNG graphs in `ml_results` and categorizes them.

Response includes:

- `topModel`
- `metrics`
- `ablation`
- `featureColumns`
- `featureRows`
- `graphs` (with URL under `/insights/files/...`)
- `totalGraphs`

### 5.3 Endpoint: `GET /insights/files/{file_name}`

Behavior:

- Securely serves artifacts under `ml_results`.
- Allowed extensions: `.png`, `.txt`, `.csv`.

---

## 6. Web UI Application

Directory: `web-ui/`

Tech stack:

- React + Vite
- Tailwind CSS v4
- Recharts
- lucide-react icons

Run commands:

```bash
cd web-ui
npm install
npm run dev
```

Build:

```bash
npm run build
```

### 6.1 App sections

Implemented in `web-ui/src/App.jsx`.

1. Detection section
- Upload image
- Trigger `/analyze`
- Show original/mask/depth/schematic images
- Show consensus severity badge
- Show classifier breakdown and extracted feature metrics
- Show per-pothole schematic data cards

2. Model Insights section
- Loads `/insights/summary`
- Interactive dashboard component (`InsightsHub.jsx`)
- Manual refresh action

### 6.2 Insights features (`InsightsHub.jsx`)

- Model metric explorer (Accuracy/Macro-F1 toggle)
- Ablation study chart
- Interactive feature scatter plot with:
  - X/Y feature selectors
  - Severity filter
- Graph gallery for all `ml_results` plots with:
  - Category filtering
  - Search
  - Fullscreen modal with previous/next navigation

---

## 7. Model-Result Artifacts in `ml_results`

Current repository includes (examples):

- Accuracy and aggregate:
  - `accuracy_comparison.png`
  - `accuracy_comparison_all_models.png`
  - `bootstrap_distributions.png`
  - `ablation_study.csv`

- Reports:
  - `classification_report_*.txt`

- Confusion matrices:
  - `confusion_matrix_*.png`

- Explainability:
  - `shap_*.png`
  - `shap_bar_*.png`

- Learning/structure diagnostics:
  - `learning_curve_*.png`
  - `feature_correlation.png`
  - `tsne_features.png`
  - `umap_features.png`
  - `calibration_curves.png`

- Feature data:
  - `train_features.csv`
  - `valid_features.csv`

These files are now directly consumed by the Model Insights UI through API endpoints.

---

## 8. Verification and Testing

### 8.1 Pipeline verification

- Script: `test_pipeline.py`
- Verifies segmentation functions, feature extractors, classifier behavior, model loading, dataset structure, and road-segment import integrity.

### 8.2 Dataset verification

- Script: `scripts/verify_dataset.py`
- Removes invalid image/label pairs based on structural checks.
- Writes `scripts/verification_report.txt`.

Current report in repo indicates:

- `Total checked: 4791`
- `Total removed: 0`

---

## 9. Typical Operational Commands

## 9.1 Backend API

```bash
cd Vision-Based-Pothole-Detection
.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

## 9.2 Frontend

```bash
cd Vision-Based-Pothole-Detection\web-ui
npm run dev
```

## 9.3 Training

```bash
cd Vision-Based-Pothole-Detection
.venv\Scripts\python.exe ml_classifier.py
```

## 9.4 Inference

```bash
python inference.py <image_path> --output_dir output --no_show
```

## 9.5 Batch road analysis

```bash
python road_segment_analysis.py <images_folder> --output_dir output
```

---

## 10. Configuration Flags and Modes

In `ml_classifier.py`:

- `USE_MERGED_DATASET`
- `USE_EXTENDED_FEATURES`
- `USE_REAL_LABELS`

Meaning:

- Toggle between original dataset-only workflow and merged dataset workflow.
- Toggle 11-feature vs extended 20-feature pipeline.
- Toggle pseudo-label-only training vs mixed real-label integration.

---

## 11. Known Caveats and Limitations

1. Pseudo-label inflation risk
- When pseudo-labels are derived from same feature space used for training, metrics can be optimistic.

2. Relative depth scale
- Depth maps are normalized and are not direct metric depth unless calibrated with camera parameters.

3. Estimated volume/cost
- Batch report volume/cost values are rough approximations and explicitly non-engineering estimates.

4. Path configuration sensitivity
- Several scripts assume specific local folder names and dataset placement.

5. Model artifact path caveat
- `ml_classifier.py` currently contains path reassignments that can cause artifacts to land in `ml_models` even when extended mode is intended.

6. Main pipeline script caveat
- `main.py` remains baseline-oriented; `inference.py` is the robust, multi-pothole, production-oriented inference path.

---

## 12. What the Project Is Doing Today (Summary)

In its current state, this project is not just a detector; it is a **full pothole intelligence stack**:

1. Builds and curates a multi-source pothole dataset.
2. Produces depth maps and globally normalized depth representations.
3. Trains multiple severity models and generates rich evaluation artifacts.
4. Performs per-image, per-pothole multi-model severity inference.
5. Serves real-time inference and analytics through an API.
6. Exposes a modern web dashboard with a separate interactive insights workspace.
7. Produces engineering-style road segment reports for prioritization.

This makes the repository suitable for research experimentation, model diagnostics, and practical demo-level deployment of pothole severity intelligence workflows.
