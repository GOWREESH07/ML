from PIL import Image
import numpy as np
from typing import Tuple

def validate_mri_image(image: Image.Image) -> Tuple[bool, str]:
    """
    Validates whether the uploaded image resembles a valid grayscale MRI brain scan.
    Returns (is_valid, reason).
    """
    rgb_img = image.convert("RGB")
    arr = np.array(rgb_img, dtype=np.float32)
    
    # 1. Grayscale / channel correlation check
    # In clinical MRI slices, R, G, and B intensities are identical or nearly identical.
    channel_diff = (
        np.abs(arr[:, :, 0] - arr[:, :, 1]) +
        np.abs(arr[:, :, 1] - arr[:, :, 2]) +
        np.abs(arr[:, :, 2] - arr[:, :, 0])
    ) / 3.0
    mean_channel_diff = float(np.mean(channel_diff))
    if mean_channel_diff > 8.0:
        return (
            False,
            f"Image rejected: Detected significant color variance (channel diff {mean_channel_diff:.1f} > 8.0). "
            "MRI scans must be grayscale medical images, not color photographs or diagrams."
        )

    gray = np.mean(arr, axis=2)

    # 2. Dynamic range and contrast spread check
    min_val, max_val = float(np.min(gray)), float(np.max(gray))
    intensity_range = max_val - min_val
    if intensity_range < 35.0:
        return (
            False,
            f"Image rejected: Insufficient contrast spread (range {intensity_range:.1f} < 35.0). "
            "The image appears blank, flat, or severely degraded."
        )

    std_val = float(np.std(gray))
    if std_val < 15.0:
        return (
            False,
            f"Image rejected: Insufficient intensity deviation (std {std_val:.1f} < 15.0). "
            "Scan does not display typical brain tissue contrast."
        )

    # 3. Background distribution check (axial/coronal brain scans have dark background surrounding brain parenchyma)
    bg_ratio = float(np.mean(gray < 25.0))
    if bg_ratio > 0.95:
        return (
            False,
            "Image rejected: Image is over 95% dark background with negligible tissue content."
        )
    if bg_ratio < 0.05:
        # Check if the image is inverted or completely washed out
        bright_ratio = float(np.mean(gray > 240.0))
        if bright_ratio > 0.85:
            return (
                False,
                "Image rejected: Over 85% of pixels are saturated white; not a standard MRI slice."
            )

    return (True, "Valid MRI scan characteristics verified.")
