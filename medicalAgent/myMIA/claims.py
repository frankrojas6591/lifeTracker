import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger("myMIA")

RENAME = {
    "Claim Number": "cNum",
    "Date Visited": "Date",
    "Visited Provider": "provider",
    "Coverage type": "coverage",
    "Claim Status": "status",
    "Medication Name": "drug",
    "Total Billed": "billed",
    "Total Cost (Allowed Amount)": "allowed",
    "Plan Paid": "paid",
    "Your Share": "myshare",
}


def _num(v):
    if isinstance(v, str):
        return float(v.replace("$", "").replace(",", ""))
    return v


def load_claims(ann):
    d = Path(ann["_dir"])
    csv = d / ann["claimsCsv"]
    prov = d / ann["providersJson"]
    for f in (csv, prov):
        if not f.exists():
            raise FileNotFoundError(f"required input missing: {f}")

    df = pd.read_csv(csv)
    absent = [c for c in RENAME if c not in df.columns]
    if absent:
        raise KeyError(f"{csv} is missing columns: {absent}")
    df = df[list(RENAME)].rename(columns=RENAME)

    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if len(df) < before:
        log.warning("dropped %d duplicate claim rows (merged download files overlap)", before - len(df))

    for c in ("billed", "allowed", "paid", "myshare"):
        df[c] = df[c].map(_num)
    df["Date"] = pd.to_datetime(df["Date"])
    df["cost"] = df["allowed"].fillna(df["billed"])

    pDict = json.loads(prov.read_text())
    unknown = sorted(set(df.provider) - set(pDict))
    if unknown:
        raise KeyError(f"providers missing from {prov.name}: {unknown}")
    df["medClass"] = df.provider.map(lambda p: pDict[p]["cls"])
    df["medDetail"] = df.provider.map(lambda p: pDict[p]["med"])
    df.attrs["duplicatesDropped"] = before - len(df)
    return df.sort_values("Date").reset_index(drop=True)


def annualize_factor(df, ann):
    if ann.get("annualizeFactor"):
        return float(ann["annualizeFactor"])
    last = df.Date.max()
    days = (last - pd.Timestamp(year=last.year, month=1, day=1)).days + 1
    return 365.0 / days
