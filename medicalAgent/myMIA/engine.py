import pandas as pd

from .claims import annualize_factor, load_claims

TIERS = ("1", "2", "3", "4")


def _classes(plan, df):
    missing = sorted(set(df[df.medClass != "pharma"].medClass) - set(plan["copays"]))
    if missing:
        raise KeyError(f"plan copays missing provider classes: {missing}")


def _drug_tier(ann, name):
    hits = [k for k in ann["drugs"] if name.upper().startswith(k.upper())]
    if not hits:
        raise KeyError(f"drug not in annual profile 'drugs': {name!r}")
    t = str(ann["drugs"][hits[0]]["tier"])
    if t not in TIERS:
        raise ValueError(f"unsupported drug tier {t} for {name!r} (tiers 1-4 only)")
    return t


def _visits(df):
    m = df[(df.medClass != "pharma") & (df.status != "DENIED")]
    return m.groupby(["Date", "provider", "medClass", "medDetail"], as_index=False).agg(cost=("cost", "sum")).sort_values("Date")


def _medical(plan, visits, w, events):
    ded = plan["deductible"]
    total = 0.0
    for r in visits.itertuples():
        full = r.cost * w
        copay = min(plan["copays"][r.medClass], r.cost)
        if ded > 0 and full > 0:
            take = min(full, ded)
            ded -= take
            total += take + copay * w * (1 - take / full)
        else:
            total += copay * w
    for ev, n in events.items():
        if ev not in plan["events"]:
            raise KeyError(f"plan has no event copay for {ev!r}")
        total += plan["events"][ev] * n
    return min(total, plan["oopMax"])


def _pharma(plan, ann, rx, f, exclude):
    rxp = plan["rx"]
    ded = rxp["deductible"]
    total = 0.0
    other = 0.0
    for r in rx.itertuples():
        if pd.isna(r.drug):
            other += r.myshare * f
            continue
        if any(r.drug.upper().startswith(x.upper()) for x in exclude):
            continue
        t = _drug_tier(ann, r.drug)
        cost = r.cost if pd.notna(r.cost) else r.billed
        copay = min(rxp["tiers"][t], cost)
        full = cost * f
        if t in ("3", "4") and ded > 0:
            take = min(full, ded)
            ded -= take
            total += take + copay * f * (1 - take / full)
        else:
            total += copay * f
    return min(total, rxp["catastrophic"]) + other


def price_all(ann, df=None):
    df = load_claims(ann) if df is None else df
    f = annualize_factor(df, ann)
    visits = _visits(df)
    rx = df[(df.medClass == "pharma") & (df.status != "DENIED")]
    rows = []
    for pn, plan in ann["plans"].items():
        _classes(plan, df)
        prem = (plan["premiumMonthly"] - plan.get("partBCreditMonthly", 0)) * 12
        for sn, sc in ann["scenarios"].items():
            v = visits[~visits.medDetail.isin(sc.get("excludeMedDetail", []))]
            med = _medical(plan, v, f * sc["usage"], sc.get("events", {}))
            rxo = _pharma(plan, ann, rx, f, sc.get("excludeDrugs", []))
            rows.append(dict(plan=pn, scenario=sn, premium=prem, medical=med, pharma=rxo, total=prem + med + rxo))
    out = pd.DataFrame(rows)
    out.attrs["annualizeFactor"] = f
    return out


def rank(ann, priced):
    w = {k: s["weight"] for k, s in ann["scenarios"].items()}
    t = priced.pivot(index="scenario", columns="plan", values="total").loc[list(w)]
    t.loc["EXPECTED"] = t.mul(pd.Series(w), axis=0).sum()
    t.loc["WORST"] = t.drop("EXPECTED").max()
    return t


def outlook(ann, priced, years=None):
    p = ann["projection"]
    years = years or p["years"]
    w = {k: s["weight"] for k, s in ann["scenarios"].items()}
    rows = []
    for pn in ann["plans"]:
        d = priced[priced.plan == pn].set_index("scenario")
        cum = {"expected": 0.0, "illness": 0.0}
        for y in range(1, years + 1):
            g = (1 + p["medInflation"]) ** y * (1 + p["usageGrowth"]) ** y
            pg = (1 + p["premiumGrowth"]) ** y
            for key, mix in (("expected", w), ("illness", {"illness": 1.0})):
                cum[key] += sum(mix[s] * (d.loc[s, "premium"] * pg + (d.loc[s, "medical"] + d.loc[s, "pharma"]) * g) for s in mix)
            rows.append(dict(plan=pn, year=y, expected=cum["expected"], illness=cum["illness"]))
    return pd.DataFrame(rows)


def plan_table(ann):
    keys = ["premiumMonthly", "partBCreditMonthly", "deductible", "oopMax"]
    t = pd.DataFrame({pn: {k: p.get(k, 0) for k in keys} for pn, p in ann["plans"].items()})
    c = pd.DataFrame({pn: p["copays"] for pn, p in ann["plans"].items()}).add_prefix("")
    c.index = "copay:" + c.index
    r = pd.DataFrame({pn: {**{"rxDed": p["rx"]["deductible"]}, **{f"rxTier{k}": v for k, v in p["rx"]["tiers"].items()}} for pn, p in ann["plans"].items()})
    return pd.concat([t, c, r])
