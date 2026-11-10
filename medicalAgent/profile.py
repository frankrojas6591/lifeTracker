import json
import logging
import os
from pathlib import Path

log = logging.getLogger("medicalAgent")

DEFAULT_PATH = Path.home() / "GDrive" / "Family" / "Health" / "medicalAgentProfile.json"
REQUIRED = ("personId", "insurer", "healthRoot", "medInsDir")


def profile_path():
    return Path(os.environ.get("MEDICAL_AGENT_PROFILE", DEFAULT_PATH)).expanduser()


def _default():
    health = Path.home() / "GDrive" / "Family" / "Health"
    return {
        "personId": "Frank",
        "insurer": "UHC_Medicare",
        "healthRoot": str(health),
        "medInsDir": str(health / "Medical" / "MedicalIns"),
        "hraDir": str(health / "Optum"),
    }


def load_profile():
    p = profile_path()
    if not p.exists():
        log.warning("medicalAgent profile missing - creating default at %s", p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(_default(), indent=2))
    prof = json.loads(p.read_text())
    missing = [k for k in REQUIRED if k not in prof]
    if missing:
        raise KeyError(f"{p} is missing required keys: {missing}")
    return prof
