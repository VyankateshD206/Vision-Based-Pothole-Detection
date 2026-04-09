import os
import hashlib
import csv
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = PROJECT_ROOT / "merged_dataset"
STATS_DIR = MERGED_DIR / "dataset_stats"
REPORT_CSV = STATS_DIR / "dataset_report.csv"

def get_hash(file_path):
    h = hashlib.md5()
    with open(file_path, 'rb') as f:
         for chunk in iter(lambda: f.read(4096), b""):
             h.update(chunk)
    return h.hexdigest()

def get_priority(filename):
    if filename.startswith("kaggle_"): return 0
    if filename.startswith("p600_"): return 1
    if filename.startswith("rdd_"): return 2
    if filename.startswith("gps_"): return 3
    return 4

def update_csv_status(removed_files):
    if not REPORT_CSV.exists():
         return
         
    with open(REPORT_CSV, 'r', newline='', encoding='utf-8') as f:
         reader = list(csv.reader(f))
         
    header = reader[0]
    try:
        status_idx = header.index("status")
        name_idx = header.index("filename")
    except ValueError:
        return # CSV format mismatch
        
    for row in reader[1:]:
        if row[name_idx] in removed_files:
             row[status_idx] = "removed_duplicate"
             
    with open(REPORT_CSV, 'w', newline='', encoding='utf-8') as f:
         writer = csv.writer(f)
         writer.writerows(reader)

def deduplicate():
    print("Finding all images in merged_dataset...")
    all_images = []
    for split in ["train", "valid", "test"]:
        img_dir = MERGED_DIR / split / "images"
        if img_dir.exists():
             all_images.extend(list(img_dir.glob("*.jpg")))
             all_images.extend(list(img_dir.glob("*.png")))
             
    total_before = len(all_images)
    print(f"Total images before: {total_before}")
    
    hashes = defaultdict(list)
    for img_path in tqdm(all_images, desc="Computing MD5 hashes"):
        hashes[get_hash(img_path)].append(img_path)
        
    removed_count = 0
    removed_filenames = set()
    
    for h, paths in tqdm(hashes.items(), desc="Removing duplicates"):
        if len(paths) > 1:
             paths.sort(key=lambda p: get_priority(p.name))
             keep_path = paths[0]
             for rm_path in paths[1:]:
                 split = rm_path.parent.parent.name # train/valid/test
                 lbl_name = f"{rm_path.stem}.txt"
                 lbl_path = MERGED_DIR / split / "labels" / lbl_name
                 
                 # Remove image
                 try:
                     rm_path.unlink()
                 except OSError: pass
                 
                 # Remove label
                 if lbl_path.exists():
                     try:
                         lbl_path.unlink()
                     except OSError: pass
                     
                 removed_count += 1
                 removed_filenames.add(rm_path.name)
                 
    total_after = total_before - removed_count
    
    print("\n--- Deduplication Summary ---")
    print(f"Total images before: {total_before}")
    print(f"Duplicates removed: {removed_count}")
    print(f"Total images after: {total_after}")
    
    print("\nUpdating dataset report...")
    update_csv_status(removed_filenames)
    print("Deduplication Complete.")

if __name__ == "__main__":
    deduplicate()
