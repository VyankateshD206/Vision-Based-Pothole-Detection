import os
import cv2
from pathlib import Path
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = PROJECT_ROOT / "merged_dataset"
REPORT_FILE = PROJECT_ROOT / "scripts" / "verification_report.txt"

def verify_and_clean():
    print("Starting Dataset Verification...")
    issues = []
    removed_count = 0
    total_checked = 0
    
    for split in ["train", "valid", "test"]:
        img_dir = MERGED_DIR / split / "images"
        lbl_dir = MERGED_DIR / split / "labels"
        
        if not img_dir.exists(): continue
        
        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
        for img_path in tqdm(images, desc=f"Verifying {split}"):
            total_checked += 1
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            
            reasons = []
            
            # 1. Image has corresponding .txt
            if not lbl_path.exists():
                reasons.append("Missing label file")
                
            # 2. Check label contents
            if lbl_path.exists():
                try:
                    with open(lbl_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    if not lines:
                        reasons.append("Empty label file")
                    else:
                        for line_idx, line in enumerate(lines):
                            parts = line.strip().split()
                            if not parts:
                                continue
                            if parts[0] != "0":
                                reasons.append(f"Label class is not 0 on line {line_idx+1}")
                            
                            coords = parts[1:]
                            if len(coords) < 6:
                                reasons.append(f"Not enough coordinates (min 6) on line {line_idx+1}")
                                
                            try:
                                floats = [float(c) for c in coords]
                                for val in floats:
                                    if val < 0.0 or val > 1.0:
                                        reasons.append(f"Coordinate out of range [0.0, 1.0] on line {line_idx+1}: {val}")
                            except ValueError:
                                reasons.append(f"Non-float coordinate on line {line_idx+1}")
                except Exception as e:
                    reasons.append(f"Could not read label file: {e}")
                    
            # 3. Check Image readable & minimum dimensions
            img = cv2.imread(str(img_path))
            if img is None:
                reasons.append("Image is corrupted or unreadable by cv2")
            else:
                h, w = img.shape[:2]
                if w < 100 or h < 100:
                    reasons.append(f"Image dimensions ({w}x{h}) smaller than 100x100")
                    
            if reasons:
                issues.append(f"{img_path.name}: {', '.join(reasons)}")
                # Remove
                try: img_path.unlink(missing_ok=True)
                except OSError: pass
                try: lbl_path.unlink(missing_ok=True)
                except OSError: pass
                removed_count += 1
                
    # Output Report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
         f.write(f"--- Verification Report ---\n")
         f.write(f"Total checked: {total_checked}\n")
         f.write(f"Total removed: {removed_count}\n\n")
         f.write("Issues Details:\n")
         f.write("\n".join(issues))
         
    print(f"\nVerification Complete.")
    print(f"Total checked: {total_checked}")
    print(f"Total removed: {removed_count}")
    print(f"See {REPORT_FILE.name} for details.")

if __name__ == "__main__":
    verify_and_clean()
