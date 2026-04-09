# Pothole Detection Pipeline — Run Order

## Setup
`pip install scipy xgboost lightgbm shap reportlab tqdm`

## Step 1 — Generate depth maps for all merged dataset images
`python depth/generate_depth.py`

## Step 2 — Globally normalize all depth maps
`python depth/global_normalize.py`

## Step 3 — Retrain YOLOv8 on merged dataset (optional — takes time)
`python scripts/retrain_yolo.py`

## Step 4 — Retrain all ML classifiers on merged dataset
`python ml_classifier.py`

## Step 5 — Hybrid CNN model (coming in next implementation phase)
*Reserved — do not run yet*

## Step 6 — Verify everything works
`python test_pipeline.py`

## Step 7 — Single image inference (original pipeline, unchanged)
`python inference.py <image_path> --output_dir output --no_show`

## Step 8 — Road segment analysis on a folder of images
`python road_segment_analysis.py <images_folder> --output_dir output`

## Flags
In `ml_classifier.py` set at top:
* `USE_MERGED_DATASET    = True/False`
* `USE_EXTENDED_FEATURES = True/False`
* `USE_REAL_LABELS       = True/False`

All `False` = original behavior exactly preserved.
