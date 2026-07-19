# PlantDiseaseAI bilingual research paper

This folder contains the synchronized Chinese and English Week 8 research report.

- Chinese draft: `paper/zh/main.tex`
- English draft: `paper/en/main.tex`
- Shared locked claims: `paper/shared/week8_verified_claims.tex`
- Bilingual benchmark, ablation, analysis, VLM, and reproduction tables: `paper/tables/`
- PDF outputs: `paper/out/`

The two papers use the same 13-section structure and the same 17 locked values. They
cover the verified Week 1--8 classification, analysis, demo, VLM-smoke, and local
release-candidate evidence, plus the later React/FastAPI target-leaf, plant-identity,
OpenCV morphology, and Corn abstention architecture. That serving update adds no new
frozen benchmark metric. Claims remain limited to seed 42 on the official PlantVillage
split unless explicitly stated. The known 227 overlapping leaf IDs, controlled
backgrounds, heuristic region evidence, incomplete human review, and absent field
validation remain binding limitations. Panjoel is the sole author; Codex is disclosed
only as a tool.

The architecture figure is generated from
`scripts/generate_hierarchical_architecture.py` and checked in as both SVG and a
3200x1800 PNG under `docs/media/`. The 114-class identity catalog is routing support,
not validated 114-species field accuracy; the Corn safety output is suspected abiotic
or nutrient stress, not confirmed nitrogen deficiency.

Build commands:

```bash
mkdir -p paper/out
cd paper/zh
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_zh -output-directory=../out main.tex
cd ../out && bibtex plantdisease_ai_zh
cd ../zh
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_zh -output-directory=../out main.tex
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_zh -output-directory=../out main.tex
cd ../en
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_en -output-directory=../out main.tex
cd ../out && bibtex plantdisease_ai_en
cd ../en
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_en -output-directory=../out main.tex
xelatex -interaction=nonstopmode -halt-on-error -jobname=plantdisease_ai_en -output-directory=../out main.tex
```

Audit parity before building:

```bash
uv run python scripts/audit_week8_paper.py --zh paper/zh/main.tex \
  --en paper/en/main.tex --claims paper/shared/week8_verified_claims.tex \
  --output reports/release/week8_paper_audit.json
```
