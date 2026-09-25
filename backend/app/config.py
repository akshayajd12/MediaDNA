import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = BASE_DIR / "evidence_store"
DERIVED_DIR = EVIDENCE_DIR / "derived"
ORIGINAL_DIR = EVIDENCE_DIR / "original"
REPORTS_DIR = BASE_DIR / "reports_store"

# Ensure directories exist
ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
DERIVED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/mediadna.db")
SECRET_KEY = os.getenv("SECRET_KEY", "mediadna-forensic-secret-key-chandigarh-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Forensic Disclaimers
FORENSIC_DISCLAIMERS = {
    "ai_analysis": "AI analysis is an investigative aid and does not constitute definitive forensic proof.",
    "origin_tracing": "Origin tracing identifies the earliest traceable occurrence within the available evidence, not necessarily the true original source.",
    "propagation_mapping": "Propagation mapping is limited to accessible public or investigator-provided evidence.",
    "attribution": "Attribution requires corroborating legal and digital evidence beyond similarity scoring."
}
