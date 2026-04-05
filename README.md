# Vision-Based-Pothole-Detection

This project estimates pothole severity from road images by combining:

- YOLOv8 instance segmentation (pothole mask)
- Depth-Anything-V2 depth estimation (depth map)
- Rule-based severity classification (Shallow, Moderate, Deep, or No pothole)
- ML-based severity classification (Logistic Regression, Random Forest, SVM, Naive Bayes)

Dataset source: https://www.kaggle.com/datasets/farzadnekouei/pothole-image-segmentation-dataset

## Project Structure

```text
Vision-Based-Pothole-Detection/
├── main.py                  # Original pipeline (rule-based only)
├── inference.py             # Unified pipeline (rule-based + ML models)
├── segmentation.py          # YOLOv8 pothole mask extraction
├── features.py              # Depth feature extraction
├── classifier.py            # Rule-based severity thresholds
├── ml_classifier.py         # ML training: features, KMeans labels, model training
├── report.tex               # LaTeX project report
├── depth/
│   └── generate_depth.py    # Batch depth map generation
├── data1/
│   ├── train/images/        # 720 training images
│   ├── train/labels/        # YOLO segmentation labels
│   ├── valid/images/        # 60 validation images
│   └── valid/labels/
├── depth_maps_1/
│   ├── train/               # Precomputed .npy depth maps (train)
│   └── valid/               # Precomputed .npy depth maps (valid)
├── ml_models/
│   ├── feature_scaler.pkl   # StandardScaler (fit on training data)
│   ├── logistic_regression.pkl
│   ├── random_forest.pkl
│   ├── svm.pkl
│   └── naive_bayes.pkl
├── ml_results/
│   ├── accuracy_comparison.png
│   ├── bootstrap_distributions.png
│   ├── kmeans_severity_distribution.png
│   ├── train_features.csv
│   └── valid_features.csv
├── yolo-segmentation/
│   └── model/best.pt
├── Depth-Anything-V2/
│   └── checkpoints/depth_anything_v2_vits.pth
└── output/                  # Saved inference visualizations
```

## Pipeline Files

| File | Purpose |
|------|---------|
| `segmentation.py` | Loads YOLOv8 segmentation weights and returns the largest pothole mask |
| `features.py` | Extracts normalised depth-based features inside the pothole mask |
| `classifier.py` | Applies rule-based thresholds on depth and area to assign severity |
| `main.py` | Runs the original pipeline (rule-based classification only) |
| `inference.py` | **Unified inference pipeline** — runs both rule-based and ML classifiers |
| `ml_classifier.py` | Feature extraction, KMeans pseudo-labelling, ML model training and evaluation |
| `depth/generate_depth.py` | Batch-generates and stores `.npy` depth maps for dataset folders |

## 1) Setup

Run from project root:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install numpy torch torchvision opencv-python matplotlib ultralytics dill tqdm scikit-learn pandas seaborn joblib
```

## 2) Get Depth-Anything-V2 from GitHub

Clone Depth-Anything-V2 from GitHub:

```powershell
git clone https://github.com/DepthAnything/Depth-Anything-V2.git
```

The scripts support either of these locations:

- `Vision-Based-Pothole-Detection/Depth-Anything-V2`
- `../Depth-Anything-V2` (sibling folder of this project)

## 3) Get dataset from Kaggle

Download the dataset from:

- https://www.kaggle.com/datasets/farzadnekouei/pothole-image-segmentation-dataset

Place it in this project as `data1/` so images are available at:

- `data1/train/images`
- `data1/valid/images`

## 4) Required model files

Make sure these files exist:

- `Depth-Anything-V2/checkpoints/depth_anything_v2_vits.pth`
- `yolo-segmentation/model/best.pt`

## 5) Generate depth maps for `data1` (one-time)

Generate precomputed depth maps for all training and validation images:

```powershell
python depth/generate_depth.py
```

This saves `.npy` depth maps to `depth_maps_1/train/` and `depth_maps_1/valid/`.

> **Note**: `generate_depth.py` is currently configured for `data1`. If using a different data directory, update `DATA_PATHS` and `OUTPUT_PATH` in the script.

## 6) Train ML severity classifiers

Once depth maps are generated, train all four ML models:

```powershell
python ml_classifier.py
```

This will:
1. Extract 11-dimensional features (geometric + depth) from each pothole in the dataset
2. Generate severity pseudo-labels via KMeans clustering (k=3)
3. Train Logistic Regression, Random Forest, SVM, and Naive Bayes classifiers
4. Evaluate on the validation set with bootstrapped confidence intervals
5. Save models to `ml_models/` and results/plots to `ml_results/`

## 7) Run inference (rule-based + ML)

Run the unified inference pipeline on a single image:

```powershell
python inference.py data1/train/images/pic-1-_jpg.rf.49882cdb272111f43a6656b1494a4918.jpg --output_dir output --no_show
```

This outputs:
- Console: severity predictions from both the rule-based classifier and all four ML models
- Saved visualization with 3 panels: original + labels, mask overlay, depth heatmap

To display the plot interactively, remove `--no_show`.

## 8) Run original pipeline (rule-based only)

```powershell
python main.py data1/train/images/pic-1-_jpg.rf.49882cdb272111f43a6656b1494a4918.jpg --output_dir output --no_show
```

## How the ML classifier works

### Feature Extraction
For each pothole detected via YOLO segmentation, 11 features are extracted:
- **Geometric**: height, width, box_area, pothole_area, nonpothole_area
- **Depth**: mean_depth, max_depth, min_depth, depth_std, depth_range, p90_depth

### Pseudo-Label Generation
Since no ground-truth severity labels exist, KMeans clustering (k=3) is applied on `max_depth` and `pothole_area` to generate three severity levels:
- **Shallow** (Level 0) — small area, lower depth
- **Moderate** (Level 1) — medium area/depth
- **Deep** (Level 2) — large area, higher depth

### Model Evaluation
- Accuracy and macro F1-score on the validation set
- Bootstrap resampling (n=1000) for 95% confidence intervals on accuracy

### Known Limitations
- Pseudo-labels are derived from the same features used for training, so high accuracy is expected but does not indicate true generalisation
- Per-image depth normalisation reduces depth discriminability across images
