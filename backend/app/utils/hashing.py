import hashlib
from PIL import Image
import imagehash

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file to preserve evidence integrity."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def calculate_perceptual_hashes(image_path: str) -> dict:
    """Calculate multi-signal perceptual hashes (dhash, phash, ahash, colorhash)."""
    try:
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            d_hash = str(imagehash.dhash(img))
            p_hash = str(imagehash.phash(img))
            a_hash = str(imagehash.average_hash(img))
            c_hash = str(imagehash.colorhash(img))
            return {
                "dhash": d_hash,
                "phash": p_hash,
                "ahash": a_hash,
                "colorhash": c_hash,
                "primary": p_hash
            }
    except Exception as e:
        return {
            "dhash": "0000000000000000",
            "phash": "0000000000000000",
            "ahash": "0000000000000000",
            "colorhash": "0000000000000000",
            "primary": "0000000000000000",
            "error": str(e)
        }
