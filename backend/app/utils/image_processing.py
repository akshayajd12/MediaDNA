import os
import io
import math
from PIL import Image, ImageChops, ImageEnhance, ImageStat
import numpy as np

def extract_exif_metadata(image_path: str) -> dict:
    """Extract EXIF metadata from image evidence."""
    metadata = {}
    try:
        with Image.open(image_path) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            metadata["mode"] = img.mode
            metadata["aspect_ratio"] = round(img.width / img.height, 4) if img.height else 1.0

            exif_data = img._getexif() if hasattr(img, '_getexif') and img._getexif() else None
            if exif_data:
                parsed_exif = {}
                for tag_id, value in exif_data.items():
                    # Handle raw strings / non-serializables cleanly
                    parsed_exif[str(tag_id)] = str(value)
                metadata["exif"] = parsed_exif
            else:
                metadata["exif"] = None
    except Exception as e:
        metadata["error"] = str(e)
    return metadata

def perform_ela(image_path: str, quality: int = 90) -> dict:
    """Perform Error Level Analysis (ELA) to highlight resaved/edited regions."""
    try:
        with Image.open(image_path) as orig_img:
            orig_img = orig_img.convert("RGB")
            buffer = io.BytesIO()
            orig_img.save(buffer, 'JPEG', quality=quality)
            buffer.seek(0)
            resaved_img = Image.open(buffer)

            ela_img = ImageChops.difference(orig_img, resaved_img)
            extrema = ela_img.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            scale = 255.0 / max_diff if max_diff != 0 else 1.0
            ela_img = ImageEnhance.Brightness(ela_img).enhance(scale)

            # Compute statistics on difference
            stat = ImageStat.Stat(ela_img)
            mean_ela_energy = sum(stat.mean) / len(stat.mean)
            variance_ela_energy = sum(stat.var) / len(stat.var)

            # High variance across regions indicates localized editing/manipulation
            suspicious_score = min(1.0, max(0.0, (variance_ela_energy - 100) / 2000.0))

            return {
                "ela_mean_energy": round(mean_ela_energy, 2),
                "ela_variance": round(variance_ela_energy, 2),
                "ela_suspicious_score": round(suspicious_score, 4),
                "has_compression_artifacts": mean_ela_energy > 15.0
            }
    except Exception as e:
        return {
            "ela_mean_energy": 0.0,
            "ela_variance": 0.0,
            "ela_suspicious_score": 0.0,
            "has_compression_artifacts": False,
            "error": str(e)
        }

def analyze_visual_features(image_path: str) -> dict:
    """Extract visual color histogram, noise variance, and frequency domain characteristics."""
    try:
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            arr = np.array(img_rgb, dtype=np.float32)

            # Color distribution stats
            r_mean, g_mean, b_mean = np.mean(arr, axis=(0,1))
            r_std, g_std, b_std = np.std(arr, axis=(0,1))

            # Laplacian noise variance approximation
            gray = np.mean(arr, axis=2)
            # High frequency noise analysis
            dy, dx = np.gradient(gray)
            noise_variance = float(np.var(dx) + np.var(dy))

            return {
                "color_mean": [float(r_mean), float(g_mean), float(b_mean)],
                "color_std": [float(r_std), float(g_std), float(b_std)],
                "noise_variance": round(noise_variance, 2),
                "is_blurred": noise_variance < 50.0
            }
    except Exception as e:
        return {
            "color_mean": [128.0, 128.0, 128.0],
            "color_std": [50.0, 50.0, 50.0],
            "noise_variance": 100.0,
            "is_blurred": False,
            "error": str(e)
        }
