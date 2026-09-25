from app.services.similarity_service import compute_multisignal_similarity

def classify_media_relationship(fp_source: dict, fp_target: dict) -> dict:
    """Determine probable Media DNA genealogy relationship class, supporting evidence, and detected transformations."""
    sims = compute_multisignal_similarity(fp_source, fp_target)
    overall_sim = sims["overall_similarity"]
    visual_sim = sims["visual_similarity"]
    face_sim = sims["face_similarity"]
    audio_sim = sims["audio_similarity"]
    text_sim = sims["text_similarity"]
    struct_sim = sims["structural_similarity"]

    s_struct = fp_source.get("structural_dna", {})
    t_struct = fp_target.get("structural_dna", {})

    w_src, h_src = s_struct.get("width", 1920), s_struct.get("height", 1080)
    w_tgt, h_tgt = t_struct.get("width", 1920), t_struct.get("height", 1080)

    s_text = fp_source.get("text_dna", {}).get("ocr_text_found", "")
    t_text = fp_target.get("text_dna", {}).get("ocr_text_found", "")

    s_wm = fp_source.get("text_dna", {}).get("detected_watermarks", [])
    t_wm = fp_target.get("text_dna", {}).get("detected_watermarks", [])

    s_audio = fp_source.get("audio_dna", {}).get("audio_fingerprint_hash", "")
    t_audio = fp_target.get("audio_dna", {}).get("audio_fingerprint_hash", "")

    supporting_evidence = []
    detected_transformations = []

    # Evidence assembly
    supporting_evidence.append(f"{int(visual_sim * 100)}% visual similarity across perceptual & feature vectors")
    if face_sim > 0.85:
        supporting_evidence.append(f"{int(face_sim * 100)}% face embedding alignment (matching subject identities)")
    if audio_sim > 0.85 and s_audio != "NONE":
        supporting_evidence.append("Identical audio spectral fingerprint match")
    elif audio_sim < 0.4 and s_audio != "NONE" and t_audio != "NONE":
        supporting_evidence.append("Audio stream mismatch (audio replacement detected)")
        detected_transformations.append("AUDIO_REPLACED")

    # Crop & Resize checks
    aspect_src = (w_src / h_src) if h_src else 1.7778
    aspect_tgt = (w_tgt / h_tgt) if h_tgt else 1.7778
    if abs(aspect_src - aspect_tgt) > 0.08:
        detected_transformations.append("CROP_DETECTED")
        supporting_evidence.append(f"Aspect ratio shift from {aspect_src:.2f} to {aspect_tgt:.2f} (Crop)")
    elif (w_src != w_tgt or h_src != h_tgt) and visual_sim > 0.88:
        detected_transformations.append("RESIZE_DETECTED")
        supporting_evidence.append(f"Resolution change from {w_src}x{h_src} to {w_tgt}x{h_tgt}")

    # Text & Watermark checks
    if set(t_wm) - set(s_wm):
        detected_transformations.append("WATERMARK_ADDED")
        supporting_evidence.append(f"New watermark detected: {', '.join(set(t_wm) - set(s_wm))}")
    if t_text and not s_text:
        detected_transformations.append("TEXT_ADDED")
        supporting_evidence.append(f"New visible text overlay detected: '{t_text[:40]}...'")
    elif t_text and s_text and text_sim < 0.6:
        detected_transformations.append("CAPTION_MODIFIED")
        supporting_evidence.append("Text overlay modified or re-captioned")

    # Classification logic (supporting all required classes)
    if overall_sim < 0.35:
        rel_type = "UNRELATED"
        confidence = 0.95
    elif overall_sim >= 0.97 and not detected_transformations:
        rel_type = "SAME_MEDIA"
        confidence = 0.98
    elif overall_sim >= 0.93 and not detected_transformations:
        rel_type = "COPIED_VERSION"
        confidence = 0.96
    elif "FACE_MODIFIED" in detected_transformations or (face_sim < 0.65 and visual_sim > 0.80):
        rel_type = "FACE_MODIFIED"
        confidence = 0.92
        detected_transformations.append("FACE_SWAP_OR_ALTERATION")
    elif "AUDIO_REPLACED" in detected_transformations:
        rel_type = "AUDIO_REPLACED"
        confidence = 0.94
    elif "WATERMARK_ADDED" in detected_transformations:
        rel_type = "WATERMARK_ADDED"
        confidence = 0.93
    elif "TEXT_ADDED" in detected_transformations or "CAPTION_MODIFIED" in detected_transformations:
        rel_type = "TEXT_ADDED"
        confidence = 0.93
    elif "CROP_DETECTED" in detected_transformations:
        rel_type = "CROPPED_VERSION"
        confidence = 0.91
    elif "RESIZE_DETECTED" in detected_transformations:
        rel_type = "RESIZED_VERSION"
        confidence = 0.90
    elif visual_sim >= 0.85:
        rel_type = "REENCODED_VERSION"
        confidence = 0.88
        detected_transformations.append("RECOMPRESSION")
    elif visual_sim >= 0.65:
        rel_type = "PARTIAL_DERIVATIVE"
        confidence = 0.82
    else:
        rel_type = "HEAVILY_EDITED_DERIVATIVE"
        confidence = 0.78

    return {
        "relationship_type": rel_type,
        "confidence_score": confidence,
        "similarity_metrics": sims,
        "supporting_evidence": supporting_evidence,
        "detected_transformations": list(set(detected_transformations))
    }
