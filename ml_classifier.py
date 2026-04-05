import os
import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm
from ultralytics import YOLO
import argparse
from typing import List, Dict, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.utils import resample
import joblib

# Setup paths (Assuming this script is in the root directory like main.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA1_PATH = os.path.join(SCRIPT_DIR, "data1")
DEPTH1_PATH = os.path.join(SCRIPT_DIR, "depth_maps_1")
RESULTS_PATH = os.path.join(SCRIPT_DIR, "ml_results")
MODELS_PATH = os.path.join(SCRIPT_DIR, "ml_models")

os.makedirs(RESULTS_PATH, exist_ok=True)
os.makedirs(MODELS_PATH, exist_ok=True)


def parse_yolo_label(label_path: str, img_shape: Tuple[int, int]) -> List[np.ndarray]:
    """Parse YOLO segmentation label and return a list of integer polygon coordinates."""
    h, w = img_shape
    polygons = []
    if not os.path.exists(label_path):
        return polygons
    
    with open(label_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                # Class mapping assumed to be parts[0], followed by polygon points
                coords = np.array([float(x) for x in parts[1:]]).reshape(-1, 2)
                # Scale from normalized [0, 1] to image dimensions
                coords[:, 0] *= w
                coords[:, 1] *= h
                polygons.append(coords.astype(np.int32))
    return polygons


def extract_dataset_features(split: str) -> pd.DataFrame:
    """Extract features from images, labels, and depth maps in a given split."""
    images_dir = os.path.join(DATA1_PATH, split, "images")
    labels_dir = os.path.join(DATA1_PATH, split, "labels")
    depths_dir = os.path.join(DEPTH1_PATH, split)
    
    features_list = []
    
    if not os.path.exists(images_dir):
        print(f"Warning: {images_dir} does not exist. Skipping.")
        return pd.DataFrame()
        
    image_files = os.listdir(images_dir)
    print(f"Extracting features for {split} split...")
    
    for img_name in tqdm(image_files):
        img_basename = os.path.splitext(img_name)[0]
        img_path = os.path.join(images_dir, img_name)
        
        # Determine exact label and depth paths
        # Assuming YOLO segmentation label has .txt extension
        label_path = os.path.join(labels_dir, f"{img_basename}.txt")
        # Assuming depth maps have .npy extension as per generate_depth_data1.py
        depth_path = os.path.join(depths_dir, f"{img_basename}.npy")
        
        if not os.path.exists(depth_path):
            # Fallback for slight naming variations
            for filename in os.listdir(depths_dir):
                if filename.startswith(img_basename.split('.rf.')[0]):
                    depth_path = os.path.join(depths_dir, filename)
                    break

        if not os.path.exists(label_path) or not os.path.exists(depth_path):
            continue
            
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        h, w = img.shape[:2]
        polygons = parse_yolo_label(label_path, (h, w))
        
        try:
            depth_map = np.load(depth_path)
        except Exception as e:
            print(f"Error loading {depth_path}: {e}")
            continue
            
        # Ensure depth map shape matches image
        if depth_map.shape != (h, w):
            depth_map = cv2.resize(depth_map, (w, h), interpolation=cv2.INTER_LINEAR)
            
        # For each pothole in the image
        for i, poly in enumerate(polygons):
            # Create binary mask for this pothole
            mask = np.zeros((h, w), dtype=np.uint8)
            # YOLO labels can sometimes be invalid
            if poly.shape[0] < 3:
                continue
            cv2.fillPoly(mask, [poly], 1)
            
            # Extract basic geometry features
            # Bounding box
            x_min, y_min = np.min(poly, axis=0)
            x_max, y_max = np.max(poly, axis=0)
            p_width = max(1, x_max - x_min)
            p_height = max(1, y_max - y_min)
            box_area = p_width * p_height
            
            pothole_area = np.sum(mask)
            nonpothole_area = max(0, box_area - pothole_area) # Prevent negative values technically
            
            if pothole_area == 0:
                continue
                
            # Extract depth features
            depth_values = depth_map[mask == 1]
            if len(depth_values) == 0:
                continue
                
            max_depth = float(np.max(depth_values))
            min_depth = float(np.min(depth_values))
            mean_depth = float(np.mean(depth_values))
            
            # Store everything
            features_list.append({
                "img_name": img_name,
                "pothole_idx": i,
                "height": p_height,
                "width": p_width,
                "box_area": box_area,
                "pothole_area": pothole_area,
                "nonpothole_area": nonpothole_area,
                "mean_depth": mean_depth,
                "max_depth": max_depth,
                "min_depth": min_depth,
                "depth_std": float(np.std(depth_values)),
                "depth_range": float(max_depth - min_depth),
                "p90_depth": float(np.percentile(depth_values, 90)),
            })
            
    return pd.DataFrame(features_list)

def generate_pseudo_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Use KMeans to generate 3 pseudolabels indicating severity."""
    if df.empty:
        return df
        
    print("Generating severity pseudo-labels via KMeans...")
    # Features generally indicative of severity: max depth and area
    # Normalizing features before clustering to prevent bias towards large area values
    features_for_clustering = df[['max_depth', 'pothole_area']].copy()
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features_for_clustering)
    
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_features)
    
    # We want to order clusters such that Level 1 (Shallow) < Level 2 (Moderate) < Level 3 (Deep)
    # Calculate a proxy "severity score" for each cluster centroid (e.g., standard distance from origin)
    centroids = kmeans.cluster_centers_
    cluster_scores = [(cluster_id, np.linalg.norm(centroid)) for cluster_id, centroid in enumerate(centroids)]
    
    # Sort clusters by severity score
    sorted_clusters = sorted(cluster_scores, key=lambda x: x[1])
    
    # Create mapping: lowest score -> 0 (Shallow), middle -> 1 (Moderate), highest -> 2 (Deep)
    cluster_mapping = {cluster_id: rank for rank, (cluster_id, score) in enumerate(sorted_clusters)}
    
    # Apply mapping
    df['severity_label'] = [cluster_mapping[c] for c in clusters]
    df['severity_name'] = df['severity_label'].map({0: 'Shallow', 1: 'Moderate', 2: 'Deep'})
    
    # Plot feature distribution colored by assigned severity
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='pothole_area', y='max_depth', hue='severity_name', palette=['green', 'orange', 'red'])
    plt.title("KMeans Extracted Severity Levels (Max Depth vs Pothole Area)")
    plt.savefig(os.path.join(RESULTS_PATH, 'kmeans_severity_distribution.png'))
    plt.close()
    
    return df

def bootstrap_evaluation(model, X_val, y_val, n_iterations=1000):
    """Evaluate performance repeatedly via bootstrapping."""
    scores = []
    n_size = int(len(X_val))
    
    # Using integer indexing or resetting index to avoid KeyError
    X_val_np = X_val.values if isinstance(X_val, pd.DataFrame) else X_val
    y_val_np = y_val.values if isinstance(y_val, pd.Series) else y_val
    
    for _ in range(n_iterations):
        # Prepare bootstrap sample
        indices = resample(np.arange(n_size), replace=True, n_samples=n_size)
        X_sample = X_val_np[indices]
        y_sample = y_val_np[indices]
        
        # Evaluate
        predictions = model.predict(X_sample)
        score = accuracy_score(y_sample, predictions)
        scores.append(score)
        
    return scores

def main():
    parser = argparse.ArgumentParser(description="Train ML based pothole severity classifier")
    parser.add_argument("--save_data", action="store_true", default=True, help="Save extracted features to CSV")
    args = parser.parse_args()

    # 1. Feature Extraction
    train_df = extract_dataset_features("train")
    if train_df.empty:
        print("Cannot proceed. Training features extracted are empty. Are labels/depth_maps_1 synced?")
        return
        
    val_df = extract_dataset_features("valid")
    
    # 2. Pseudo Label Generation (Fit on train, apply to valid mapping logically)
    # We will fit KMeans on train data to define the cluster mapping standard.
    train_df = generate_pseudo_labels(train_df)
    
    # Apply identical transformation to val_df using a simple Nearest-Centroid or 
    # train another instance but consistency matters. So re-using same approach globally or:
    # the simplest robust way: apply the same clustering process to the full data then split it back,
    # OR map valid data to the closest center found during training.
    # For simplicity, cluster valid set independently if it's large enough and follows same distribution.
    # To maintain strict separation, we determine closest centroid from training data.
    if not val_df.empty:
        print("Generating pseudo labels for validation set mapping...")
        features_train_clu = train_df[['max_depth', 'pothole_area']].copy()
        features_val_clu = val_df[['max_depth', 'pothole_area']].copy()
        
        sc = StandardScaler()
        sc.fit(features_train_clu)
        
        km = KMeans(n_clusters=3, random_state=42, n_init=10)
        km.fit(sc.transform(features_train_clu))
        
        centroids = km.cluster_centers_
        cluster_scores = [(cluster_id, np.linalg.norm(cen)) for cluster_id, cen in enumerate(centroids)]
        sorted_clusters = sorted(cluster_scores, key=lambda x: x[1])
        cluster_mapping = {cluster_id: rank for rank, (cluster_id, score) in enumerate(sorted_clusters)}
        
        # Predict on valid
        val_clusters = km.predict(sc.transform(features_val_clu))
        val_df['severity_label'] = [cluster_mapping[c] for c in val_clusters]
        val_df['severity_name'] = val_df['severity_label'].map({0: 'Shallow', 1: 'Moderate', 2: 'Deep'})

    if args.save_data:
        train_df.to_csv(os.path.join(RESULTS_PATH, "train_features.csv"), index=False)
        if not val_df.empty:
            val_df.to_csv(os.path.join(RESULTS_PATH, "valid_features.csv"), index=False)
            
    # 3. Model Training
    print("\nPreparing models...")
    # Features matching reference diagram + additional depth info
    feature_cols = [
        'height', 'width', 'box_area', 'pothole_area', 'nonpothole_area', 
        'mean_depth', 'max_depth', 'min_depth', 'depth_std', 'depth_range', 'p90_depth'
    ]
    target_col = 'severity_label'
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    
    if not val_df.empty:
        X_val = val_df[feature_cols]
        y_val = val_df[target_col]
    else:
        # Fallback if no validation data
        from sklearn.model_selection import train_test_split
        print("No validation set found, splitting train set...")
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

    # Standardize features (crucial for SVM and Logistic Regression)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    joblib.dump(scaler, os.path.join(MODELS_PATH, "feature_scaler.pkl"))

    models = {
        "Logistic Regression": LogisticRegression(random_state=42, max_iter=1000),
        "Random Forest": RandomForestClassifier(random_state=42, n_estimators=100),
        "SVM": SVC(random_state=42, probability=True),
        "Naive Bayes": GaussianNB()
    }

    results = []
    trained_models = {}

    for name, mm in models.items():
        print(f"\nTraining {name}...")
        mm.fit(X_train_scaled, y_train)
        
        # Save model
        joblib.dump(mm, os.path.join(MODELS_PATH, f"{name.replace(' ', '_').lower()}.pkl"))
        trained_models[name] = mm
        
        # Predict & Evaluate metrics
        y_pred = mm.predict(X_val_scaled)
        acc = accuracy_score(y_val, y_pred)
        report = classification_report(y_val, y_pred, output_dict=True, zero_division=0)
        
        results.append({
            "Model": name,
            "Accuracy": acc,
            "Macro F1": report.get('macro avg', {}).get('f1-score', 0)
        })
        
        print(f"[{name}] Accuracy: {acc:.4f}")
        
    # 4. Evaluation and Bootstrapping for Best Model Selection
    print("\nStarting bootstrapping evaluation (n=1000 iterations)...")
    bootstrap_results = {}
    
    for name, mm in trained_models.items():
        # Retrieve scores robustly
        b_scores = bootstrap_evaluation(mm, X_val_scaled, y_val, 1000)
        bootstrap_results[name] = b_scores
        
        mean_acc = np.mean(b_scores)
        ci_lower = np.percentile(b_scores, 2.5)
        ci_upper = np.percentile(b_scores, 97.5)
        
        print(f"{name} Bootstrap 95% CI Accuracy: {mean_acc:.4f} ({ci_lower:.4f} - {ci_upper:.4f})")
        
        # Update results
        for r in results:
            if r["Model"] == name:
                r["Bootstrap Mean Acc"] = mean_acc

    # Plot performance comparison
    res_df = pd.DataFrame(results)
    print("\n--- Final Results ---")
    print(res_df.to_string(index=False))
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=res_df, x="Model", y="Accuracy")
    plt.title("Classifier Accuracy Comparison")
    plt.ylim(0, 1)
    plt.savefig(os.path.join(RESULTS_PATH, "accuracy_comparison.png"))
    plt.close()
    
    # Plot Bootstrapping distributions
    plt.figure(figsize=(10, 6))
    for name, scores in bootstrap_results.items():
        sns.kdeplot(scores, label=name)
    plt.title("Bootstrapped Accuracy Distribution")
    plt.xlabel("Accuracy")
    plt.legend()
    plt.savefig(os.path.join(RESULTS_PATH, "bootstrap_distributions.png"))
    plt.close()

if __name__ == "__main__":
    main()
