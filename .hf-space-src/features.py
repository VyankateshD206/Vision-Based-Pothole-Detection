from typing import Any, Dict, Optional
import cv2
import numpy as np
import scipy.stats


def extract_depth_features(
    mask: np.ndarray, depth_map: np.ndarray
) -> Optional[Dict[str, Any]]:
    """
    Extract depth statistics from pixels where mask == 1.

    Args:
        mask: Binary mask array with foreground as 1.
        depth_map: Depth map array with same shape as mask.

    Returns:
        Dictionary containing:
        mean_depth, max_depth, min_depth, depth_std, depth_range,
        area, and p90_depth.
        Returns None when no pothole pixels are present in mask.
    """
    mask_array = np.asarray(mask)
    depth_array = np.asarray(depth_map, dtype=np.float32)

    if mask_array.shape != depth_array.shape:
        raise ValueError("mask and depth_map must have the same shape")

    # Normalize depth map to [0, 1] before computing features.
    depth_min_all = float(np.min(depth_array))
    depth_max_all = float(np.max(depth_array))
    if depth_max_all > depth_min_all:
        depth_array = (depth_array - depth_min_all) / (depth_max_all - depth_min_all)
    else:
        depth_array = np.zeros_like(depth_array, dtype=np.float32)

    depth_values = depth_array[mask_array == 1]
    area = int(depth_values.size)

    if area == 0:
        return None

    max_depth = float(np.max(depth_values))
    min_depth = float(np.min(depth_values))
    
    # Calculate local depth contrast (difference between hole and surrounding road context)
    kernel = np.ones((15, 15), np.uint8)
    dilated = cv2.dilate(mask_array.astype(np.uint8), kernel, iterations=2)
    boundary_ring = dilated - mask_array.astype(np.uint8)
    depth_boundary = depth_array[boundary_ring > 0]
    
    mean_val = float(np.mean(depth_values))
    if len(depth_boundary) > 0 and len(depth_values) > 0:
        local_depth_contrast = float(abs(mean_val - np.mean(depth_boundary)))
    else:
        local_depth_contrast = 0.0

    return {
        "mean_depth": mean_val,
        "max_depth": max_depth,
        "min_depth": min_depth,
        "depth_std": float(np.std(depth_values)),
        "depth_range": float(max_depth - min_depth),
        "area": area,
        "p90_depth": float(np.percentile(depth_values, 90)),
        "local_depth_contrast": local_depth_contrast
    }

def extract_features(mask: np.ndarray, depth_map: np.ndarray) -> Optional[Dict[str, Any]]:
    h, w = mask.shape[:2]
    pothole_area = int(np.sum(mask))
    if pothole_area == 0:
        return None
        
    ys, xs = np.where(mask > 0)
    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    p_width = max(1, x_max - x_min)
    p_height = max(1, y_max - y_min)
    box_area = p_width * p_height
    nonpothole_area = max(0, box_area - pothole_area)
    
    d = depth_map.astype(np.float32)
    d_min_all = float(np.min(d))
    d_max_all = float(np.max(d))
    if d_max_all > d_min_all:
        d = (d - d_min_all) / (d_max_all - d_min_all)
    else:
        d = np.zeros_like(d)
        
    depth_values = d[mask > 0]
    if len(depth_values) == 0:
        return None
        
    max_depth = float(np.max(depth_values))
    min_depth = float(np.min(depth_values))
    mean_depth = float(np.mean(depth_values))
    depth_std = float(np.std(depth_values))
    depth_range = max_depth - min_depth
    p90_depth = float(np.percentile(depth_values, 90))
    
    # Calculate local depth contrast (difference between hole and surrounding road context)
    kernel = np.ones((15, 15), np.uint8)
    dilated = cv2.dilate(mask.astype(np.uint8), kernel, iterations=2)
    boundary_ring = dilated - mask.astype(np.uint8)
    depth_boundary = d[boundary_ring > 0]
    
    if len(depth_boundary) > 0 and len(depth_values) > 0:
        # Since disparity means closer=higher, we take absolute difference or look at the drop.
        # For a hole, depth disparity usually changes abruptly compared to the immediate flat ring.
        local_depth_contrast = float(abs(mean_depth - depth_boundary.mean()))
    else:
        local_depth_contrast = 0.0
    
    return {
        'height': p_height,
        'width': p_width,
        'box_area': box_area,
        'pothole_area': pothole_area,
        'nonpothole_area': nonpothole_area,
        'mean_depth': mean_depth,
        'max_depth': max_depth,
        'min_depth': min_depth,
        'depth_std': depth_std,
        'depth_range': depth_range,
        'p90_depth': p90_depth,
        'local_depth_contrast': local_depth_contrast
    }

def polygon_surface_area(mask, pixel_size_cm=0.5):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    n = len(contour)
    area_px = 0
    for i in range(n):
        j = (i + 1) % n
        xi, yi = contour[i][0]
        xj, yj = contour[j][0]
        area_px += xi * yj
        area_px -= xj * yi
    area_px = abs(area_px) / 2.0
    area_cm2 = area_px * (pixel_size_cm ** 2)
    return {
        'surface_area_px2': area_px,
        'surface_area_cm2': area_cm2,
        'pixel_size_cm_assumption': pixel_size_cm
    }

def extract_features_extended(mask, depth_map):
    orig_features = extract_features(mask, depth_map)
    if orig_features is None:
        return None
        
    height = orig_features['height']
    width = orig_features['width']
    pothole_area = orig_features['pothole_area']
    
    aspect_ratio = width / (height + 1e-8)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        solidity = pothole_area / (hull_area + 1e-8)
        
        perimeter = cv2.arcLength(largest_contour, True)
        compactness = (4 * np.pi * pothole_area) / (perimeter**2 + 1e-8)
    else:
        solidity = 0.0
        compactness = 0.0
        
    # Re-normalize depth for consistent feature extraction as done in extract_features
    d = depth_map.astype(np.float32)
    d_min_all = float(np.min(d))
    d_max_all = float(np.max(d))
    if d_max_all > d_min_all:
        d = (d - d_min_all) / (d_max_all - d_min_all)
    else:
        d = np.zeros_like(d)
        
    depth_values_inside_mask = d[mask > 0]
    
    depth_skewness = scipy.stats.skew(depth_values_inside_mask)
    if np.isnan(depth_skewness):
        depth_skewness = 0.0
    depth_kurtosis = scipy.stats.kurtosis(depth_values_inside_mask)
    if np.isnan(depth_kurtosis):
        depth_kurtosis = 0.0
        
    kernel = np.ones((5,5), np.uint8)
    dilated = cv2.dilate(mask.astype(np.uint8), kernel, iterations=2)
    boundary_ring = dilated - mask.astype(np.uint8)
    depth_boundary = d[boundary_ring > 0]
    
    if len(depth_boundary) > 0 and len(depth_values_inside_mask) > 0:
        boundary_gradient = orig_features['mean_depth'] - depth_boundary.mean()
    else:
        boundary_gradient = 0.0
        
    ext_features = orig_features.copy()
    
    ys, xs = np.where(mask > 0)
    cy, cx = ys.mean(), xs.mean()
    distances = np.sqrt((ys - cy)**2 + (xs - cx)**2)
    weights = distances / (distances.sum() + 1e-8)
    weighted_mean_depth = (depth_values_inside_mask * weights).sum()
    
    poly_area = polygon_surface_area(mask)
    if poly_area is not None:
        surface_area_px2 = poly_area['surface_area_px2']
        surface_area_cm2 = poly_area['surface_area_cm2']
    else:
        surface_area_px2 = float(pothole_area)
        surface_area_cm2 = 0.0

    ext_features.update({
        'aspect_ratio': float(aspect_ratio),
        'solidity': float(solidity),
        'compactness': float(compactness),
        'depth_skewness': float(depth_skewness),
        'depth_kurtosis': float(depth_kurtosis),
        'boundary_gradient': float(boundary_gradient),
        'weighted_mean_depth': float(weighted_mean_depth),
        'surface_area_px2': float(surface_area_px2),
        'surface_area_cm2': float(surface_area_cm2)
    })
    
    return ext_features
        
    orig_features.update({
        'aspect_ratio': aspect_ratio,
        'solidity': solidity,
        'compactness': compactness,
        'depth_skewness': depth_skewness,
        'depth_kurtosis': depth_kurtosis,
        'boundary_gradient': boundary_gradient,
        'weighted_mean_depth': weighted_mean_depth,
        'surface_area_px2': surface_area_px2,
        'surface_area_cm2': surface_area_cm2
    })
    
    return orig_features
