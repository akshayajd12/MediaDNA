import os
import io
import uuid
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.evidence import Evidence
from app.models.media_analysis import MediaAnalysis
from app.models.media_fingerprint import MediaFingerprint
from app.models.media_relationship import MediaRelationship
from app.models.propagation import PropagationNode, PropagationEdge
from app.models.timeline import TimelineEvent
from app.models.audit_log import AuditLog
from app.models.note import InvestigatorNote
from app.services.evidence_service import store_uploaded_evidence
from app.services.mediadna_service import generate_mediadna_fingerprint
from app.services.ai_detection_service import analyze_media_authenticity
from app.utils.image_processing import perform_ela, analyze_visual_features

def create_synthetic_image(text: str, bg_color=(30, 41, 59), fg_color=(241, 245, 249), size=(1280, 720), subtext=None, overlay_rect=False) -> bytes:
    """Generate a clean synthetic media frame byte buffer with distinct visual characteristics."""
    img = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw grid pattern for visual feature anchor points
    for i in range(0, size[0], 100):
        draw.line([(i, 0), (i, size[1])], fill=(51, 65, 85), width=1)
    for j in range(0, size[1], 100):
        draw.line([(0, j), (size[0], j)], fill=(51, 65, 85), width=1)

    # Draw simulated speaker / face box
    draw.rectangle([440, 180, 840, 540], outline=(14, 165, 233), width=4)
    draw.text((460, 200), "[FACE REGION - SUBJECT A]", fill=(14, 165, 233))

    if overlay_rect:
        # Draw fake manipulated region box
        draw.rectangle([460, 240, 820, 520], fill=(239, 68, 68, 128))
        draw.text((480, 260), "DEEPFAKE ALTERATION", fill=(255, 255, 255))

    # Main text banner
    draw.rectangle([0, size[1] - 120, size[0], size[1]], fill=(15, 23, 42))
    draw.text((40, size[1] - 90), text, fill=fg_color)
    if subtext:
        draw.text((40, size[1] - 50), subtext, fill=(239, 68, 68))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()

def load_hackathon_demo_dataset(db: Session) -> Case:
    """Generate and pre-populate complete synthetic investigation MD-DEMO-001 with 5-generation Media Family Tree."""
    
    # Check if demo case already exists
    existing_case = db.query(Case).filter(Case.case_number == "MD-DEMO-001").first()
    if existing_case:
        return existing_case

    # Create Case MD-DEMO-001
    demo_case = Case(
        id="case-md-demo-001",
        case_number="MD-DEMO-001",
        title="Deepfake Viral Disinformation Campaign - Press Conference Investigation",
        description="Investigation into altered press conference media circulating across public social platforms. Tracing lineage from official press release to viral manipulated copy.",
        status="ACTIVE",
        priority="CRITICAL"
    )
    db.add(demo_case)
    db.commit()

    base_time = datetime(2026, 8, 20, 10, 0, 0, tzinfo=timezone.utc)

    # Generation 1: Node A (Original Press Release)
    bytes_a = create_synthetic_image("CHANDIGARH POLICE OFFICIAL PRESS RELEASE - 2026", subtext="CONFIRMED GENUINE MEDIA")
    ev_a = store_uploaded_evidence(
        db, demo_case.id, bytes_a, "Original_Press_Conference.jpg", "image/jpeg",
        source_platform="PUBLIC_GOVT_PORTAL", source_url="https://chandigarhpolice.gov.in/press/2026/001.jpg", is_demo=True
    )
    ev_a.acquisition_timestamp = base_time

    # Generation 2: Node B (Cropped Social Media Version)
    bytes_b = create_synthetic_image("CHANDIGARH POLICE OFFICIAL PRESS RELEASE", size=(960, 720))
    ev_b = store_uploaded_evidence(
        db, demo_case.id, bytes_b, "Social_Media_Crop_Version.jpg", "image/jpeg",
        source_platform="TWITTER", source_url="https://x.com/news_handle/status/1001", is_demo=True
    )
    ev_b.acquisition_timestamp = base_time + timedelta(hours=4)

    # Generation 3: Node C (Fake Caption Text Overlay Added)
    bytes_c = create_synthetic_image("CHANDIGARH POLICE PRESS RELEASE", subtext="BREAKING: UNVERIFIED CURFEW ANNOUNCEMENT!", size=(960, 720))
    ev_c = store_uploaded_evidence(
        db, demo_case.id, bytes_c, "Fake_Caption_Overlay.jpg", "image/jpeg",
        source_platform="TELEGRAM_CHANNEL", source_url="https://t.me/local_alerts/4092", is_demo=True
    )
    ev_c.acquisition_timestamp = base_time + timedelta(hours=12)

    # Generation 4: Node D (Deepfake Face Swap Alteration)
    bytes_d = create_synthetic_image("CHANDIGARH POLICE PRESS RELEASE", subtext="BREAKING: UNVERIFIED CURFEW ANNOUNCEMENT!", size=(960, 720), overlay_rect=True)
    ev_d = store_uploaded_evidence(
        db, demo_case.id, bytes_d, "Deepfake_Face_Modified.jpg", "image/jpeg",
        source_platform="TELEGRAM_CHANNEL", source_url="https://t.me/viral_news_ind/881", is_demo=True
    )
    ev_d.acquisition_timestamp = base_time + timedelta(hours=24)

    # Generation 5: Node E (Viral High Compression Version)
    bytes_e = create_synthetic_image("CHANDIGARH POLICE PRESS RELEASE", subtext="BREAKING: UNVERIFIED CURFEW ANNOUNCEMENT!", size=(640, 480), overlay_rect=True)
    ev_e = store_uploaded_evidence(
        db, demo_case.id, bytes_e, "Viral_Compressed_Copy.jpg", "image/jpeg",
        source_platform="WHATSAPP_FORWARD", source_url="Public Investigator Evidence Upload", is_demo=True
    )
    ev_e.acquisition_timestamp = base_time + timedelta(hours=36)

    evidence_items = [ev_a, ev_b, ev_c, ev_d, ev_e]

    # Generate Analysis & MediaDNA for all 5 evidence items
    for idx, ev in enumerate(evidence_items):
        ela = perform_ela(ev.derived_file_path)
        vf = analyze_visual_features(ev.derived_file_path)
        
        # Override scores for high-fidelity demo representation
        prob = 0.05 if idx == 0 else 0.18 if idx == 1 else 0.45 if idx == 2 else 0.91 if idx == 3 else 0.94
        assessment = "AUTHENTIC / UNLIKELY MANIPULATED" if idx <= 1 else "SUSPICIOUS / LIKELY MANIPULATED"
        
        analysis = MediaAnalysis(
            evidence_id=ev.id,
            manipulation_probability=prob,
            assessment=assessment,
            confidence_score=0.94,
            ai_generated_score=0.92 if idx >= 3 else 0.1,
            face_manipulation_score=0.95 if idx >= 3 else 0.05,
            visual_inconsistency_score=0.88 if idx >= 2 else 0.1,
            indicators_json=[
                {
                    "type": "FACE_REGION_ANOMALY" if idx >= 3 else "TEXT_OVERLAY" if idx == 2 else "CROP_DETECTED",
                    "severity": "HIGH" if idx >= 3 else "MEDIUM",
                    "title": "Deepfake Face Boundary Inconsistency" if idx >= 3 else "Text Overlay Added" if idx == 2 else "Spatial Crop",
                    "description": "Localized face region exhibits blending artifacts and frequency distribution mismatch." if idx >= 3 else "Unnatural text overlay bounding box detected in lower third."
                }
            ]
        )
        db.add(analysis)

        fp_dict = generate_mediadna_fingerprint(ev)
        fp = MediaFingerprint(
            evidence_id=ev.id,
            perceptual_hash=fp_dict["perceptual_hash"],
            visual_embedding_json=fp_dict["visual_dna"],
            face_dna_json=fp_dict["face_dna"],
            audio_dna_json=fp_dict["audio_dna"],
            structural_dna_json=fp_dict["structural_dna"],
            text_dna_json=fp_dict["text_dna"],
            forensic_dna_json=fp_dict["forensic_dna"]
        )
        db.add(fp)

    db.commit()

    # Create Media Relationships (A->B, B->C, C->D, D->E)
    relationships = [
        {
            "src": ev_a.id, "tgt": ev_b.id, "type": "CROPPED_VERSION", "conf": 0.94,
            "evidence": ["96% visual feature match", "Same face identity embedding", "Resolution crop from 1280x720 to 960x720"],
            "transforms": ["CROP", "RESIZE"]
        },
        {
            "src": ev_b.id, "tgt": ev_c.id, "type": "TEXT_ADDED", "conf": 0.93,
            "evidence": ["94% background visual match", "Same subject framing", "New text caption detected: 'BREAKING: UNVERIFIED CURFEW'"],
            "transforms": ["TEXT_OVERLAY"]
        },
        {
            "src": ev_c.id, "tgt": ev_d.id, "type": "FACE_MODIFIED", "conf": 0.92,
            "evidence": ["91% spatial alignment", "Face embedding anomaly score 0.95", "Deepfake boundary blending artifact detected"],
            "transforms": ["FACE_SWAP"]
        },
        {
            "src": ev_d.id, "tgt": ev_e.id, "type": "REENCODED_VERSION", "conf": 0.89,
            "evidence": ["Identical scene content", "High re-compression quantization loss", "Resolution downscaled to 640x480"],
            "transforms": ["RECOMPRESSION", "DOWNSIZING"]
        }
    ]

    for rel in relationships:
        r_model = MediaRelationship(
            case_id=demo_case.id,
            source_evidence_id=rel["src"],
            target_evidence_id=rel["tgt"],
            relationship_type=rel["type"],
            confidence_score=rel["conf"],
            visual_similarity=0.92,
            face_similarity=0.95 if rel["type"] != "FACE_MODIFIED" else 0.45,
            supporting_evidence_json=rel["evidence"],
            detected_transformations_json=rel["transforms"]
        )
        db.add(r_model)

    # Create Propagation Nodes & Edges
    p_nodes = [
        PropagationNode(id="pnode-1", case_id=demo_case.id, node_label="Official Govt Portal", node_type="PLATFORM", platform="GOVT_WEB", evidence_id=ev_a.id, reach_count=15000),
        PropagationNode(id="pnode-2", case_id=demo_case.id, node_label="Press Officer Post", node_type="POST", platform="TWITTER", author_account="@ChdPoliceOfficial", evidence_id=ev_a.id, reach_count=45000),
        PropagationNode(id="pnode-3", case_id=demo_case.id, node_label="News Channel Repost", node_type="POST", platform="TWITTER", author_account="@StateNewsLive", evidence_id=ev_b.id, reach_count=120000),
        PropagationNode(id="pnode-4", case_id=demo_case.id, node_label="Telegram Alert Channel", node_type="POST", platform="TELEGRAM", author_account="t.me/city_alerts_fast", evidence_id=ev_c.id, reach_count=85000),
        PropagationNode(id="pnode-5", case_id=demo_case.id, node_label="Viral Disinfo Channel", node_type="POST", platform="TELEGRAM", author_account="t.me/unfiltered_opinion", evidence_id=ev_d.id, reach_count=230000),
        PropagationNode(id="pnode-6", case_id=demo_case.id, node_label="WhatsApp Mass Forward", node_type="POST", platform="WHATSAPP", author_account="Encrypted Public Evidence Submission", evidence_id=ev_e.id, reach_count=500000)
    ]
    for p in p_nodes:
        db.add(p)

    p_edges = [
        PropagationEdge(case_id=demo_case.id, source_node_id="pnode-1", target_node_id="pnode-2", action_type="POSTED"),
        PropagationEdge(case_id=demo_case.id, source_node_id="pnode-2", target_node_id="pnode-3", action_type="DERIVED_FROM"),
        PropagationEdge(case_id=demo_case.id, source_node_id="pnode-3", target_node_id="pnode-4", action_type="REPOSTED"),
        PropagationEdge(case_id=demo_case.id, source_node_id="pnode-4", target_node_id="pnode-5", action_type="DERIVED_FROM"),
        PropagationEdge(case_id=demo_case.id, source_node_id="pnode-5", target_node_id="pnode-6", action_type="SHARED")
    ]
    for pe in p_edges:
        db.add(pe)

    # Create Timeline Events
    timeline_events = [
        TimelineEvent(
            case_id=demo_case.id, evidence_id=ev_a.id, event_timestamp=base_time,
            event_type="EARLIEST_OCCURRENCE", title="Earliest Traceable Occurrence Discovered",
            description="Original unedited press conference image acquired from Official Police Web Portal.",
            change_type="ORIGINAL", confidence_score="CONFIRMED_HIGH", evidence_source="Public Govt Archive"
        ),
        TimelineEvent(
            case_id=demo_case.id, evidence_id=ev_b.id, event_timestamp=base_time + timedelta(hours=4),
            event_type="MODIFICATION_DETECTED", title="Aspect Ratio Crop Detected",
            description="Media reframed for 4:3 social media post layout.",
            change_type="CROP", confidence_score="HIGH", evidence_source="Public Twitter Post"
        ),
        TimelineEvent(
            case_id=demo_case.id, evidence_id=ev_c.id, event_timestamp=base_time + timedelta(hours=12),
            event_type="MODIFICATION_DETECTED", title="Sensational Fake Caption Overlay Added",
            description="Fake curfew announcement subtitle rendered over lower third.",
            change_type="TEXT_OVERLAY", confidence_score="HIGH", evidence_source="Telegram Public Channel"
        ),
        TimelineEvent(
            case_id=demo_case.id, evidence_id=ev_d.id, event_timestamp=base_time + timedelta(hours=24),
            event_type="MODIFICATION_DETECTED", title="Deepfake Face Swap Modification",
            description="Neural face swap filter applied over speaker's face region with high spatial ELA energy.",
            change_type="FACE_SWAP", confidence_score="HIGH", evidence_source="Telegram Disinfo Group"
        ),
        TimelineEvent(
            case_id=demo_case.id, evidence_id=ev_e.id, event_timestamp=base_time + timedelta(hours=36),
            event_type="VIRAL_SPREAD", title="Viral Mass Resharing Across Messaging Networks",
            description="High-compression derived copy circulating virally.",
            change_type="COMPRESSION", confidence_score="HIGH", evidence_source="Investigator Public Evidence Upload"
        )
    ]
    for te in timeline_events:
        db.add(te)

    # Create Investigator Note
    note = InvestigatorNote(
        case_id=demo_case.id,
        author_name="Inspector R. Sharma (Cyber Crime Cell)",
        note_type="Investigator conclusion",
        content="Media genealogy analysis confirms Node A (Original Press Release) as the earliest traceable occurrence. Node D & Node E contain synthetic face manipulations and fake subtitle overlays introduced on Telegram prior to viral WhatsApp circulation."
    )
    db.add(note)

    db.commit()
    db.refresh(demo_case)
    return demo_case
