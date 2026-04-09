import os
import shutil
import csv
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from tqdm import tqdm

random.seed(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MERGED_DIR = PROJECT_ROOT / "merged_dataset"
STATS_DIR = MERGED_DIR / "dataset_stats"
REPORT_CSV = STATS_DIR / "dataset_report.csv"
GPS_DIR = PROJECT_ROOT / "gps"

UNANNOTATED_DIR = GPS_DIR / "unannotated_images"

GPS_DIR.mkdir(parents=True, exist_ok=True)
UNANNOTATED_DIR.mkdir(parents=True, exist_ok=True)

for split in ["train", "valid", "test"]:
    (MERGED_DIR / split / "images").mkdir(parents=True, exist_ok=True)
    (MERGED_DIR / split / "labels").mkdir(parents=True, exist_ok=True)


def append_to_csv(rows):
    with open(REPORT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def convert_dms(dms, ref):
    if not dms or len(dms) < 3: return None
    try:
        degrees = float(dms[0])
        minutes = float(dms[1])
        seconds = float(dms[2])
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ["S", "W"]:
            decimal = -decimal
        return decimal
    except Exception:
        return None

def extract_gps(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            return None, None
            
        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag)
            if tag_name == "GPSInfo":
                for gps_tag, gps_val in value.items():
                    gps_info[GPSTAGS.get(gps_tag)] = gps_val
                    
        lat = convert_dms(gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef"))
        lon = convert_dms(gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef"))
        return lat, lon
    except Exception:
         return None, None


def find_dataset_dir():
    # Look for Kaggle extracted folder
    # Possible names
    names = ["pothole-dataset", "archive", "chitrakumari25"]
    for d in PROJECT_ROOT.iterdir():
        if d.is_dir() and d.name == "data1": continue # ignore base
        if d.is_dir() and d.name == "merged_dataset": continue 
        if d.is_dir() and any(n in d.name.lower() for n in names):
            # Verify it contains images
            if list(d.rglob("*.jpg")):
                return d
    return None


def process_gps_dataset():
    dataset_dir = find_dataset_dir()
    if not dataset_dir:
        print("GPS Pothole Dataset not found.")
        print("Please manually download https://www.kaggle.com/datasets/chitrakumari25/pothole-dataset")
        print("Extract it to a folder like 'pothole-dataset' in the project root.")
        return
        
    print(f"Found GPS Dataset at: {dataset_dir.name}")
    images = list(dataset_dir.rglob("*.jpg"))
    print(f"Found {len(images)} images.")
    
    annotated = []
    unannotated = []
    gps_rows = []
    
    for img_path in tqdm(images, desc="Extracting GPS & Checking Annotations"):
        lat, lon = extract_gps(img_path)
        
        # Check annotations
        stem = img_path.stem
        w, h = 0, 0
        try:
             with Image.open(img_path) as im:
                 w, h = im.size
        except: pass
        
        # Check YOLO txt
        txt_path = img_path.with_suffix(".txt")
        polygons = []
        if txt_path.exists():
             with open(txt_path, "r") as f:
                 lines = f.readlines()
             for line in lines:
                 parts = line.strip().split()
                 if len(parts) >= 5: # standard yolo or polygon
                     # If it's a bounding box 0 x y w h, convert to polygon 
                     if len(parts) == 5:
                         c, x, y, bw, bh = map(float, parts)
                         x1 = max(0.0, min(1.0, x - bw/2))
                         y1 = max(0.0, min(1.0, y - bh/2))
                         x2 = max(0.0, min(1.0, x + bw/2))
                         y2 = max(0.0, min(1.0, y - bh/2))
                         x3 = max(0.0, min(1.0, x + bw/2))
                         y3 = max(0.0, min(1.0, y + bh/2))
                         x4 = max(0.0, min(1.0, x - bw/2))
                         y4 = max(0.0, min(1.0, y + bh/2))
                         polygons.append(f"0 {x1:.6f} {y1:.6f} {x2:.6f} {y2:.6f} {x3:.6f} {y3:.6f} {x4:.6f} {y4:.6f}")
                     else:
                         polygons.append("0 " + " ".join(parts[1:]))

        # Check Pascal VOC XML
        xml_path = img_path.with_suffix(".xml")
        if not txt_path.exists() and xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                if w == 0:
                    size_e = root.find("size")
                    if size_e:
                       w = int(size_e.find("width").text)
                       h = int(size_e.find("height").text)
                       
                if w > 0:
                    for obj in root.findall("object"):
                        bndbox = obj.find("bndbox")
                        if bndbox is not None:
                            xmin = float(bndbox.find("xmin").text) / w
                            ymin = float(bndbox.find("ymin").text) / h
                            xmax = float(bndbox.find("xmax").text) / w
                            ymax = float(bndbox.find("ymax").text) / h
                            
                            x1, y1 = max(0.0, min(1.0, xmin)), max(0.0, min(1.0, ymin))
                            x2, y2 = max(0.0, min(1.0, xmax)), max(0.0, min(1.0, ymin))
                            x3, y3 = max(0.0, min(1.0, xmax)), max(0.0, min(1.0, ymax))
                            x4, y4 = max(0.0, min(1.0, xmin)), max(0.0, min(1.0, ymax))
                            polygons.append(f"0 {x1:.6f} {y1:.6f} {x2:.6f} {y2:.6f} {x3:.6f} {y3:.6f} {x4:.6f} {y4:.6f}")
            except: pass
            
        info = {
             "img": img_path,
             "polygons": polygons,
             "lat": lat if lat else "",
             "lon": lon if lon else "",
             "w": w,
             "h": h
        }
        
        orig_name = img_path.name
        new_name = f"gps_{orig_name}"
        
        if lat and lon:
             gps_rows.append([new_name, lat, lon, "kaggle_chitrakumari25"])
             
        if polygons:
            annotated.append(info)
        else:
            unannotated.append(info)

    # Save Coordinates
    gps_csv = GPS_DIR / "image_coordinates.csv"
    with open(gps_csv, "w", newline="", encoding="utf-8") as f:
         writer = csv.writer(f)
         writer.writerow(["image_name", "latitude", "longitude", "source"])
         writer.writerows(gps_rows)
         
    # Handle Unannotated
    for info in tqdm(unannotated, desc="Copying Unannotated"):
        orig_name = info["img"].name
        new_name = f"gps_{orig_name}"
        dest = UNANNOTATED_DIR / new_name
        shutil.copy2(info["img"], dest)
        
    # Split Annotated
    random.shuffle(annotated)
    n = len(annotated)
    train_idx = int(0.8 * n)
    val_idx = int(0.9 * n)
    
    csv_rows = []
    for i, info in enumerate(tqdm(annotated, desc="Saving GPS Dataset")):
        if i < train_idx: split = "train"
        elif i < val_idx: split = "valid"
        else: split = "test"
        
        orig_name = info["img"].name
        new_name = f"gps_{orig_name}"
        new_stem = Path(new_name).stem
        
        shutil.copy2(info["img"], MERGED_DIR / split / "images" / new_name)
        with open(MERGED_DIR / split / "labels" / f"{new_stem}.txt", "w") as f:
             f.write("\n".join(info["polygons"]))
             
        csv_rows.append([new_name, "gps_tagged", split, True, info["w"], info["h"], "ok", info["lat"], info["lon"]])
        
    append_to_csv(csv_rows)
    print("GPS Dataset Processing Complete.")
    
if __name__ == "__main__":
    process_gps_dataset()
