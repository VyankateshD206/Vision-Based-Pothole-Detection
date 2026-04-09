import os
import glob
from pathlib import Path
from collections import defaultdict
import csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = PROJECT_ROOT / "merged_dataset"
STATS_DIR = MERGED_DIR / "dataset_stats"
REPORT_CSV = STATS_DIR / "dataset_report.csv"
FINAL_SUMMARY = STATS_DIR / "final_summary.txt"
YAML_FILE = MERGED_DIR / "dataset.yaml"

def polygon_area(coords):
    n = len(coords) // 2
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[2*i] * coords[2*j+1]
        area -= coords[2*j] * coords[2*i+1]
    return abs(area) / 2.0

def get_source_from_prefix(filename):
    if filename.startswith("kaggle_"): return "kaggle"
    if filename.startswith("rdd_japan_"): return "rdd_japan"
    if filename.startswith("rdd_india_"): return "rdd_india"
    if filename.startswith("rdd_usa_"): return "rdd_usa"
    if filename.startswith("rdd_norway_"): return "rdd_norway"
    if filename.startswith("rdd_czech_"): return "rdd_czech"
    if filename.startswith("rdd_china_"): return "rdd_china"
    if filename.startswith("p600_"): return "pothole600"
    if filename.startswith("gps_"): return "gps"
    return "unknown"

SOURCE_LABELS = {
    "kaggle": "Kaggle (existing)",
    "rdd_japan": "RDD2022 - Japan",
    "rdd_india": "RDD2022 - India",
    "rdd_usa": "RDD2022 - USA",
    "rdd_norway": "RDD2022 - Norway",
    "rdd_czech": "RDD2022 - Czech",
    "rdd_china": "RDD2022 - China",
    "pothole600": "Pothole-600",
    "gps": "GPS-Tagged"
}

def generate_summary():
    counts = {k: {"train": 0, "valid": 0, "test": 0, "total": 0} for k in SOURCE_LABELS}
    counts["unknown"] = {"train": 0, "valid": 0, "test": 0, "total": 0}
    
    pothole_dist = defaultdict(int)
    areas = {k: [] for k in counts}
    
    total_imgs = {"train": 0, "valid": 0, "test": 0}
    
    # Process files
    for split in ["train", "valid", "test"]:
        img_dir = MERGED_DIR / split / "images"
        lbl_dir = MERGED_DIR / split / "labels"
        if not img_dir.exists(): continue
        
        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
        for img_path in images:
            src = get_source_from_prefix(img_path.name)
            counts[src][split] += 1
            counts[src]["total"] += 1
            total_imgs[split] += 1
            
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            poly_count = 0
            if lbl_path.exists():
                with open(lbl_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 6:
                            poly_count += 1
                            try:
                                coords = [float(x) for x in parts[1:]]
                                area = polygon_area(coords)
                                areas[src].append(area)
                            except ValueError: pass
            
            pothole_dist[poly_count] += 1

    # Severity labels stats
    sev_file = MERGED_DIR / "severity_labels" / "pothole600_annotations.csv"
    sev_count = 0
    if sev_file.exists():
        with open(sev_file, "r") as f:
             sev_count = max(0, sum(1 for line in f) - 1)
             
    # Stereo maps count
    stereo_disp_dir = MERGED_DIR / "stereo" / "disparity"
    stereo_count = sum(1 for _ in stereo_disp_dir.rglob("*.npy")) if stereo_disp_dir.exists() else 0
    
    # GPS count
    gps_file = PROJECT_ROOT / "gps" / "image_coordinates.csv"
    gps_count = 0
    if gps_file.exists():
         with open(gps_file, "r") as f:
              gps_count = max(0, sum(1 for line in f) - 1)
              
    # Build YAML
    yaml_content = f"""path: merged_dataset
train: train/images
val: valid/images
test: test/images

nc: 1
names: ['pothole']

# Dataset statistics (auto-filled by script)
# train_images: {total_imgs['train']}
# valid_images: {total_imgs['valid']}
# test_images: {total_imgs['test']}
# sources: kaggle, rdd2022_japan, rdd2022_india, rdd2022_usa, rdd2022_norway, rdd2022_czech, rdd2022_china, pothole600, gps_tagged
"""
    with open(YAML_FILE, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    # Build Report
    report_lines = []
    
    report_lines.append("Dataset Pre-processing Final Summary\n" + "="*36 + "\n")
    
    report_lines.append(f"1. Total image count per split: Train={total_imgs['train']}, Valid={total_imgs['valid']}, Test={total_imgs['test']}")
    
    report_lines.append("\n2. Image count per source dataset:")
    for src_key, src_label in SOURCE_LABELS.items():
        if counts[src_key]['total'] > 0:
            report_lines.append(f"   - {src_label}: {counts[src_key]['total']}")
            
    report_lines.append("\n3. Distribution of pothole counts per image:")
    for ct in sorted(pothole_dist.keys()):
        report_lines.append(f"   - {ct} pothole(s): {pothole_dist[ct]} images")
        
    report_lines.append("\n4. Average bounding box/polygon area per source (relative 0-1):")
    for src_key, src_label in SOURCE_LABELS.items():
        if areas[src_key]:
            avg_area = sum(areas[src_key]) / len(areas[src_key])
            report_lines.append(f"   - {src_label}: {avg_area:.5f}")
            
    report_lines.append(f"\n5. Images with Pothole-600 severity labels: {sev_count}")
    report_lines.append(f"6. GPS-tagged images loaded: {gps_count}")
    report_lines.append(f"7. Pothole-600 stereo pairs stored: {stereo_count}")
    
    report_lines.append("\n" + "┌─────────────────────┬────────┬───────┬──────┬────────┐")
    report_lines.append("│ Source              │ Train  │ Valid │ Test │ Total  │")
    report_lines.append("├─────────────────────┼────────┼───────┼──────┼────────┤")
    for src_key, src_label in SOURCE_LABELS.items():
        r = counts[src_key]
        report_lines.append(f"│ {src_label:<19} │ {r['train']:>6} │ {r['valid']:>5} │ {r['test']:>4} │ {r['total']:>6} │")
    report_lines.append("├─────────────────────┼────────┼───────┼──────┼────────┤")
    tot_tot = sum(total_imgs.values())
    report_lines.append(f"│ TOTAL               │ {total_imgs['train']:>6} │ {total_imgs['valid']:>5} │ {total_imgs['test']:>4} │ {tot_tot:>6} │")
    report_lines.append("└─────────────────────┴────────┴───────┴──────┴────────┘")
    
    full_report = "\n".join(report_lines)
    
    STATS_DIR.mkdir(parents=True, exist_ok=True)
    with open(FINAL_SUMMARY, "w", encoding="utf-8") as f:
        f.write(full_report)
        
    print(full_report)
    print("\nSuccessfully wrote dataset.yaml and final_summary.txt")

if __name__ == "__main__":
    generate_summary()
