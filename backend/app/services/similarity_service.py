def hamming_distance(hex1: str, hex2: str) -> int:
    """Compute Hamming distance between two hex hashes."""
    try:
        val1 = int(hex1, 16)
        val2 = int(hex2, 16)
        return bin(val1 ^ val2).count('1')
    except Exception:
        return 64

def compute_multisignal_similarity(fp1: dict, fp2: dict) -> dict:
    """Compute explainable multi-signal similarity between two MediaDNA fingerprints."""
    
    # 1. Visual Similarity (Perceptual Hash + Visual Embedding)
    hash1 = fp1.get("perceptual_hash", "0000000000000000")
    hash2 = fp2.get("perceptual_hash", "0000000000000000")
    h_dist = hamming_distance(hash1, hash2)
    hash_sim = max(0.0, 1.0 - (h_dist / 32.0))

    vec1 = fp1.get("visual_dna", {}).get("visual_embedding", [])
    vec2 = fp2.get("visual_dna", {}).get("visual_embedding", [])
    if vec1 and vec2 and len(vec1) == len(vec2):
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math_sqrt(sum(a * a for a in vec1))
        norm2 = math_sqrt(sum(b * b for b in vec2))
        vec_sim = dot / (norm1 * norm2) if (norm1 * norm2) > 0 else 0.5
    else:
        vec_sim = 0.8

    visual_sim = round(0.6 * hash_sim + 0.4 * vec_sim, 4)

    # 2. Face Similarity
    f1 = fp1.get("face_dna", {}).get("face_count", 0)
    f2 = fp2.get("face_dna", {}).get("face_count", 0)
    face_sim = 0.98 if (f1 > 0 and f2 > 0 and f1 == f2) else 0.5 if (f1 > 0 or f2 > 0) else 0.85

    # 3. Audio Similarity
    a1 = fp1.get("audio_dna", {}).get("audio_fingerprint_hash", "")
    a2 = fp2.get("audio_dna", {}).get("audio_fingerprint_hash", "")
    audio_sim = 0.99 if (a1 and a2 and a1 == a2 and a1 != "NONE") else 0.3 if (a1 != a2 and a1 != "NONE" and a2 != "NONE") else 0.85

    # 4. Text / OCR Similarity
    t1 = fp1.get("text_dna", {}).get("ocr_text_found", "")
    t2 = fp2.get("text_dna", {}).get("ocr_text_found", "")
    if t1 and t2:
        words1 = set(t1.lower().split())
        words2 = set(t2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        text_sim = len(intersection) / len(union) if union else 0.0
    else:
        text_sim = 0.5

    # 5. Structural Similarity
    s1 = fp1.get("structural_dna", {})
    s2 = fp2.get("structural_dna", {})
    w1, h1 = s1.get("width", 1000), s1.get("height", 1000)
    w2, h2 = s2.get("width", 1000), s2.get("height", 1000)
    aspect_diff = abs((w1/h1) - (w2/h2)) if h1 and h2 else 0
    struct_sim = max(0.2, 1.0 - aspect_diff)

    # Overall Weighted Score
    overall_sim = round(
        0.40 * visual_sim +
        0.25 * face_sim +
        0.15 * audio_sim +
        0.10 * text_sim +
        0.10 * struct_sim, 4
    )

    return {
        "overall_similarity": overall_sim,
        "visual_similarity": visual_sim,
        "face_similarity": face_sim,
        "audio_similarity": audio_sim,
        "text_similarity": round(text_sim, 4),
        "structural_similarity": round(struct_sim, 4)
    }

def math_sqrt(val):
    import math
    return math.sqrt(val)
