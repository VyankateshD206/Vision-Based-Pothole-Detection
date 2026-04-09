# pip install numpy tqdm
import numpy as np
from pathlib import Path
from tqdm import tqdm

def main():
    DEPTH_DIRS = [
        Path("depth_maps_merged/train"),
        Path("depth_maps_merged/valid"),
        Path("depth_maps_merged/test"),
    ]
    
    OUTPUT_DIRS = [
        Path("depth_maps_global/train"),
        Path("depth_maps_global/valid"),
        Path("depth_maps_global/test"),
    ]
    
    # Pass 1 — Find global range
    global_min = float('inf')
    global_max = float('-inf')
    
    all_files = []
    
    for d_dir in DEPTH_DIRS:
        if d_dir.exists() and d_dir.is_dir():
            files = list(d_dir.glob("*.npy"))
            all_files.extend(files)
            
    if not all_files:
        print("No depth maps found. Skipping normalization.")
        return
        
    print(f"Pass 1: Finding global range across {len(all_files)} files...")
    for f in tqdm(all_files, desc="Pass 1"):
        try:
            d = np.load(f)
            d_min = d.min()
            d_max = d.max()
            if d_min < global_min:
                global_min = d_min
            if d_max > global_max:
                global_max = d_max
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if global_min == float('inf') or global_max == float('-inf'):
        print("Could not compute valid global range.")
        return
        
    print(f"Global min: {global_min}")
    print(f"Global max: {global_max}")
    
    # Save stats
    np.save('depth_global_stats.npy', np.array([global_min, global_max]))
    
    # Pass 2 — Re-normalize and save
    print(f"\nPass 2: Re-normalizing and saving...")
    files_normalized = 0
    
    for i, d_dir in enumerate(DEPTH_DIRS):
        out_dir = OUTPUT_DIRS[i]
        out_dir.mkdir(parents=True, exist_ok=True)
        
        if d_dir.exists() and d_dir.is_dir():
            files = list(d_dir.glob("*.npy"))
            for f in tqdm(files, desc=f"Pass 2 ({d_dir.name})"):
                try:
                    d = np.load(f)
                    d_norm = (d - global_min) / (global_max - global_min + 1e-8)
                    
                    out_path = out_dir / f.name
                    np.save(out_path, d_norm)
                    files_normalized += 1
                except Exception as e:
                    print(f"Error processing {f}: {e}")
                    
    print(f"\nFiles normalized: {files_normalized}")
    print("Output available in depth_maps_global/")

if __name__ == "__main__":
    main()
