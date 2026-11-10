# myMIA — Plans

## Roadmap

```
 v1.0  notebook ─► v1.1 more areas ─► v2.0 lifeTracker sub-agent ─► v3.0 standalone app
 (today)           dental/vision/      medicalAgent profile +        CLI/web, same
                   mental scenarios    shared medical history        engine
```

## v1.0 — done
- `myMIA.ipynb`: YEAR in → recommendation out
- Year info = `annualProfile.json`; start from `templates/annualProfile.template.json`

## Each November (the ritual)
- Download UHC claims CSV(s) → merge into `<YEAR-1>_FYClaims_<id>.csv`
- Copy last year's `annualProfile.json` → new year; update plans from the UHC PDFs
- New providers → add to `Providers.json` (cls + med)
- Run `myMIA.ipynb`

## Next
- Read plan PDFs automatically (no hand-keyed copays)
- Dental / vision / mental / fitness scenarios
- Medical-history risk signals feed scenario weights (future conditions)

## Into lifeTracker
- myMIA = sub-agent of `medicalAgent`; shares its profile (`medicalAgentProfile.json`)
- Engine stays pure Python (`claims`, `engine`) → same code behind notebook, CLI, or agent tool
- Personal data stays in the user's Health folder; repo holds code + template only

## Offering It
- **Notebook:** open `myMIA.ipynb`, set `YEAR`
- **App:** thin wrapper calling `load_annual → price_all → rank`
