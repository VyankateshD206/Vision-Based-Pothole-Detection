import os
import shutil
import xml.etree.ElementTree as ET
import random
import requests
import zipfile
import csv
from pathlib import Path
from tqdm import tqdm

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA1_DIR = PROJECT_ROOT / "data1"
MERGED_DIR = PROJECT_ROOT / "merged_dataset"
STATS_DIR = MERGED_DIR / "dataset_stats"
REPORT_CSV = STATS_DIR / "dataset_report.csv"

# Make directories
for split in ["train", "valid", "test"]:
    (MERGED_DIR / split / "images").mkdir(parents=True, exist_ok=True)
    (MERGED_DIR / split / "labels").mkdir(parents=True, exist_ok=True)
STATS_DIR.mkdir(parents=True, exist_ok=True)


def init_csv():
    if not REPORT_CSV.exists():
        with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "source", "split", "has_label", "image_width", "image_height", "status", "latitude", "longitude"])

def append_to_csv(rows):
    with open(REPORT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def copy_kaggle_base():
    print("Copying base custom/Kaggle dataset from data1/ ...")
    csv_rows = []
    for split in ["train", "valid"]:
        img_dir = DATA1_DIR / split / "images"
        lbl_dir = DATA1_DIR / split / "labels"
        
        if not img_dir.exists():
            continue
            
        images = list(img_dir.glob("*.jpg"))
        for img_path in tqdm(images, desc=f"Copying Kaggle {split}"):
            new_name = f"kaggle_{img_path.name}"
            new_img_dest = MERGED_DIR / split / "images" / new_name
            shutil.copy2(img_path, new_img_dest)
            
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            has_label = False
            if lbl_path.exists():
                new_lbl_dest = MERGED_DIR / split / "labels" / f"kaggle_{lbl_path.name}"
                shutil.copy2(lbl_path, new_lbl_dest)
                has_label = True
                
            csv_rows.append([new_name, "kaggle", split, has_label, "", "", "ok", "", ""])
            
    append_to_csv(csv_rows)

RDD_COUNTRIES = {
    "Japan": "https://github.com/sekilab/RoadDamageDetector/releases/download/v2022.1/Japan.zip",
    "India": "https://github.com/sekilab/RoadDamageDetector/releases/download/v2022.1/India.zip",
    "USA": "https://github.com/sekilab/RoadDamageDetector/releases/download/v2022.1/United_States.zip",
    "Norway": "https://github.com/sekilab/RoadDamageDetector/releases/download/v2022.1/Norway.zip",
    "Czech": "https://github.com/sekilab/RoadDamageDetector/releases/download/v2022.1/Czech.zip",
    "China": "https://github.com/sekilab/RoadDamageDetector/releases/download/v2022.1/China_MotorBike.zip"
}

def download_file(url, dest):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(dest, "wb") as f, tqdm(
            desc=dest.name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
        return True
    except Exception as e:
        print(f"\nFailed to download {url}")
        print(f"Error: {e}")
        print("Please manually download it from https://github.com/sekilab/RoadDamageDetector/releases/tag/v2022.1")
        return False

def process_rdd():
    rdd_temp_dir = PROJECT_ROOT / "rdd_temp"
    rdd_temp_dir.mkdir(exist_ok=True)
    
    rdd_source_dir = PROJECT_ROOT / "RDD2022" / "RDD2022_all_countries"
    if not rdd_source_dir.exists():
        rdd_source_dir = PROJECT_ROOT / "RDD2022"
    
    found_zips = list(rdd_source_dir.glob("*.zip"))
    if not found_zips:
        print(f"No zip files found in {rdd_source_dir}. Please place RDD2022 zips there.")
        return
        
    for zip_path in found_zips:
        country = zip_path.stem
        extract_dir = rdd_temp_dir / country
        if not extract_dir.exists():
            print(f"Extracting {country}...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            except zipfile.BadZipFile:
                print(f"Error: {zip_path.name} is corrupted. Please re-download manually.")
                continue

        print(f"Processing annotations for {country}...")
        
        # Structure varies slightly upon extraction. Scan recursively for XMLs
        xml_files = list(extract_dir.rglob("*.xml"))
        
        valid_pairs = []
        for xml_path in tqdm(xml_files, desc=f"Filtering {country}"):
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                has_d40 = False
                pothole_boxes = []
                size_elem = root.find("size")
                if size_elem is None:
                    continue
                w_img = int(size_elem.find("width").text)
                h_img = int(size_elem.find("height").text)
                
                if w_img == 0 or h_img == 0:
                    continue
                    
                for obj in root.findall("object"):
                    name = obj.find("name").text
                    if name == "D40":
                        has_d40 = True
                        bndbox = obj.find("bndbox")
                        xmin = float(bndbox.find("xmin").text)
                        ymin = float(bndbox.find("ymin").text)
                        xmax = float(bndbox.find("xmax").text)
                        ymax = float(bndbox.find("ymax").text)
                        
                        x1 = xmin / w_img
                        y1 = ymin / h_img
                        x2 = xmax / w_img
                        y2 = ymin / h_img
                        x3 = xmax / w_img
                        y3 = ymax / h_img
                        x4 = xmin / w_img
                        y4 = ymax / h_img
                        
                        x1, y1 = max(0.0, min(1.0, x1)), max(0.0, min(1.0, y1))
                        x2, y2 = max(0.0, min(1.0, x2)), max(0.0, min(1.0, y2))
                        x3, y3 = max(0.0, min(1.0, x3)), max(0.0, min(1.0, y3))
                        x4, y4 = max(0.0, min(1.0, x4)), max(0.0, min(1.0, y4))
                        
                        pothole_boxes.append(f"0 {x1:.6f} {y1:.6f} {x2:.6f} {y2:.6f} {x3:.6f} {y3:.6f} {x4:.6f} {y4:.6f}")
                
                if has_d40: # Only if D40 is present
                    img_name = root.find("filename").text
                    # The image is usually in the same dir or in a sibling 'images' dir
                    img_path = xml_path.parent / img_name
                    if not img_path.exists():
                        # Try looking in 'images' if we are in 'annotations'
                        img_path = xml_path.parent.parent / "images" / img_name
                        if not img_path.exists():
                            # Try looking if we are in 'annotations/xmls'
                            img_path = xml_path.parent.parent.parent / "images" / img_name
                        
                    if img_path.exists():
                        valid_pairs.append({
                            "xml": xml_path,
                            "img": img_path,
                            "labels": pothole_boxes,
                            "w": w_img,
                            "h": h_img
                        })
            except Exception as e:
                pass # skip invalid files
                
        random.shuffle(valid_pairs)
        n = len(valid_pairs)
        train_idx = int(0.8 * n)
        val_idx = int(0.9 * n)
        
        csv_rows = []
        for i, pair in enumerate(tqdm(valid_pairs, desc=f"Writing {country} outputs")):
            if i < train_idx:
                split = "train"
            elif i < val_idx:
                split = "valid"
            else:
                split = "test"
                
            orig_name = pair["img"].name
            new_name = f"rdd_{country.lower()}_{orig_name}"
            new_img_dest = MERGED_DIR / split / "images" / new_name
            new_lbl_dest = MERGED_DIR / split / "labels" / f"{Path(new_name).stem}.txt"
            
            shutil.copy2(pair["img"], new_img_dest)
            
            with open(new_lbl_dest, "w", encoding="utf-8") as f:
                f.write("\n".join(pair["labels"]))
                
            # Fix potentially malformed bounding boxes if x1 == x2 or y1 == y2
            valid_polygon = False
            for coord_str in pair["labels"]:
                parts = coord_str.split()
                if len(parts) >= 9:
                    valid_polygon = True
                    break
            if not valid_polygon:
                continue
                
            csv_rows.append([new_name, f"rdd2022_{country.lower()}", split, True, pair["w"], pair["h"], "ok", "", ""])
            
        if csv_rows:
            append_to_csv(csv_rows)

if __name__ == "__main__":
    init_csv()
    copy_kaggle_base()
    process_rdd()
    print("Dataset 1 and 2 processing complete.")
