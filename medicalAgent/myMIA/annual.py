import json
from pathlib import Path

from ..profile import load_profile

REQUIRED = ("year", "claimsCsv", "providersJson", "plans", "drugs", "scenarios", "projection")


def load_annual(year=None, path=None):
    prof = load_profile()
    if path is None:
        if year is None:
            raise ValueError("load_annual needs a year or an explicit path")
        path = Path(prof["medInsDir"]) / str(year) / "annualProfile.json"
    path = Path(path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"annual profile not found: {path} (copy myMIA/templates/annualProfile.template.json there and fill it in)")
    ann = json.loads(path.read_text())
    missing = [k for k in REQUIRED if k not in ann]
    if missing:
        raise KeyError(f"{path} is missing required keys: {missing}")
    wsum = sum(s["weight"] for s in ann["scenarios"].values())
    if abs(wsum - 1.0) > 1e-6:
        raise ValueError(f"scenario weights must sum to 1.0, got {wsum}")
    ann["_dir"] = path.parent
    ann["_path"] = path
    return prof, ann
