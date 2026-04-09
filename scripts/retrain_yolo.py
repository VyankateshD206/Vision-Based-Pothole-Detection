import os
import shutil
from pathlib import Path
from ultralytics import YOLO

# Configuration
MODEL_BASE  = "yolov8n-seg.pt"
DATA_YAML   = "merged_dataset/dataset.yaml"
EPOCHS      = 50
IMG_SIZE    = 640
BATCH_SIZE  = 16
PATIENCE    = 10
RUN_NAME    = "pothole_merged_v1"

def main():
    print(f"Starting YOLOv8 segmentation retraining...")
    print(f"Base model: {MODEL_BASE}")
    print(f"Dataset: {DATA_YAML}")
    
    # Check dataset exists
    if not Path(DATA_YAML).exists():
        print(f"Dataset config NOT FOUND at {DATA_YAML}! Cannot train.")
        return

    model = YOLO(MODEL_BASE)
    
    # Train
    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        name=RUN_NAME,
        patience=PATIENCE,
        save=True,
        val=True,
        augment=True
    )
    
    # Locate paths
    train_dir = Path("runs/segment") / RUN_NAME
    best_weights = train_dir / "weights/best.pt"
    results_plot = train_dir / "results.png"
    
    target_weights = Path("yolo-segmentation/model/best_merged.pt")
    target_results = Path("ml_results/yolo_training_results.png")
    
    target_weights.parent.mkdir(parents=True, exist_ok=True)
    Path("ml_results").mkdir(parents=True, exist_ok=True)
    
    # Copy best weights
    if best_weights.exists():
        shutil.copy2(best_weights, target_weights)
        print(f"\nModel saved successfully: {target_weights}")
    else:
        print(f"Error: Could not find trained weights at {best_weights}")
        
    # Copy results plot
    if results_plot.exists():
        shutil.copy2(results_plot, target_results)
        print(f"Training plots saved to: {target_results}")
        
    print(f"\nFinal metrics:")
    if hasattr(results, 'box') and hasattr(results.box, 'map50'):
        print(f"  Box mAP50:     {results.box.map50:.4f}")
        print(f"  Box mAP50-95:  {results.box.map:.4f}")
    if hasattr(results, 'seg') and hasattr(results.seg, 'map50'):
        print(f"  Seg mAP50:     {results.seg.map50:.4f}")
        print(f"  Seg mAP50-95:  {results.seg.map:.4f}")
        
    print("\nTo use new model in inference: change model_path argument to yolo-segmentation/model/best_merged.pt")
    print("Original best.pt is unchanged.")

if __name__ == "__main__":
    main()
