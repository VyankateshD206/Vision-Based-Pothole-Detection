from typing import Any, Dict, Optional


def classify_severity(features: Optional[Dict[str, Any]]) -> str:
    """
    Classify pothole severity using rule-based thresholds on local depth metrics.

    Rules:
    - Prioritize relative local drop (`local_depth_contrast`) instead of absolute `max_depth` (which just measures distance to camera).
    - if local_depth_contrast is high, the hole drops off sharply -> Deep
    - if local_depth_contrast is very low and texture (depth_std) is smooth, it's a puddle/shallow -> Shallow
    - else -> Moderate
    """
    if features is None:
        return "No pothole"

    area = float(features.get("area", features.get("pothole_area", 0.0)))
    if area <= 0:
        return "No pothole"

    # Get our new relative features, fall back to max_depth if old cache is used
    local_depth_contrast = features.get("local_depth_contrast", None)
    depth_std = float(features.get("depth_std", 0.0))
    max_depth = float(features.get("max_depth", 0.0))

    if local_depth_contrast is not None:
        local_depth_contrast = float(local_depth_contrast)
        # Using relative metrics!
        if local_depth_contrast < 0.05 and depth_std < 0.05:
            # Virtually no drop from surrounding road AND very smooth = Shallow
            return "Shallow"
        elif local_depth_contrast > 0.15 or depth_std > 0.15:
            # Sharp drop from the road OR very rough/bumpy texture -> Deep
            return "Deep"
        else:
            return "Moderate"
    else:
        # Fallback to old heuristic if local_depth_contrast not available
        if max_depth < 0.3 and area < 500:
            return "Shallow"
        if max_depth < 0.6:
            return "Moderate"
        return "Deep"

rule_based_classify = classify_severity
