# Week 6 VLM Assistant Safety Prototype

## Status

This is a Week 6 resource-limited prototype. It demonstrates how the image
classifier can provide structured context to an educational assistant, but it is
not a professional agricultural diagnosis system and it is not evidence of VLM
LoRA/QLoRA fine-tuning.

## Implemented behavior

- Uses classifier context as the primary structured signal: top class,
  confidence, and existing demo warnings.
- Produces bounded educational summaries only when classifier confidence is high
  and the class is inside the verified PlantVillage leaf-label scope.
- Refuses pesticide, fungicide, spray, dose, dilution, concentration, or other
  high-risk management requests.
- Refuses low-confidence classifier context instead of converting uncertainty
  into a disease claim.
- Refuses unknown, non-leaf, or out-of-domain context.
- Returns explicit sources such as `classifier:Tomato___Late_blight` and
  `vqa:qwen3-vl-short-smoke` when a source-backed VQA answer is included.

## Fixed demo evidence

Generated command:

```bash
uv run python scripts/demo_vlm_assistant.py \
  --output outputs/plantvillage/week6_vlm/vlm_assistant_demo.json
```

Machine-readable output summary:

- Status: `completed`
- Scenario count: `4`
- Actions covered: `educational_summary`, `refuse_high_risk`,
  `refuse_low_confidence`, `refuse_out_of_scope`

Code and tests:

- Prototype: `src/plantdisease/vlm/assistant.py`
- Demo script: `scripts/demo_vlm_assistant.py`
- Tests: `tests/vlm/test_assistant.py`,
  `tests/vlm/test_assistant_demo.py`

## Manual VQA audit template

Generated command:

```bash
uv run python scripts/build_vqa_audit_template.py \
  --dataset outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --analysis outputs/plantvillage/week6_vlm/vlm_result_analysis.json \
  --output-json outputs/plantvillage/week6_vlm/vqa_manual_audit_template.json \
  --report reports/week6_vqa_manual_audit_template.md
```

Current audit-template summary:

- Status: `pending_human_review`
- Entries: `72`
- Unique images: `24`
- Question types: `plant=24`, `condition=24`, `health_status=24`
- Risk-flagged entries from automatic VLM analysis: `7`

This template is not a completed human audit. It is the structured input for
reviewing traceability, ambiguity, language quality, duplicate-question issues,
and safety concerns.

## Boundaries for README, reports, and resume

Accurate wording:

- “Implemented a safety-bounded agricultural assistant prototype that uses
  classifier context, refuses low-confidence/out-of-scope/high-risk requests,
  and records source provenance.”
- “Generated a 72-entry manual VQA audit template; human review remains
  pending.”
- “Qwen3-VL zero-shot smoke reached 10/15 exact-match with a short-answer
  prompt on 5 test images.”

Do not claim:

- completed LoRA/QLoRA fine-tuning;
- reliable field diagnosis;
- pesticide dosage or treatment recommendations;
- completed human VQA audit.
