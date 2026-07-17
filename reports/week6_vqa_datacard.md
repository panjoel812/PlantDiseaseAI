# Week 6 VQA Seed Data Card

Generated on: 2026-07-13

## Purpose

This is a small, source-grounded VQA seed dataset for Week 6 pipeline validation. It is
not a full PlantVillageVQA release and is not evidence of VLM fine-tuning quality.

## Source Evidence

- Source file: `outputs/plantvillage/week4_explainability/frozen_samples.json`
- Builder: `scripts/build_vqa_dataset.py`
- Schema: `src/plantdisease/vlm/schema.py`
- Output JSONL: `outputs/plantvillage/week6_vlm/vqa_seed.jsonl`
- Output summary: `outputs/plantvillage/week6_vlm/vqa_seed_summary.json`

The source records are the 24 frozen Week 4 explainability samples. Answers are derived
only from `true_class_name`; no VLM output is used as ground truth.

## Schema

Each record uses `schema_version = 1` and includes:

- `sample_id`
- `image_id`
- `image_ref`
- `question`
- `answer`
- `question_type`
- `source`
- `split`
- `audit_status`
- `metadata`

Allowed splits are `train`, `validation`, and `test`. Entity leakage is checked by
`image_id`; all questions for one image must remain in one split.

## Generated Counts

```json
{
  "audit_status_counts": {
    "pending": 72
  },
  "entity_split_leakage": false,
  "image_count": 24,
  "question_type_counts": {
    "condition": 24,
    "health_status": 24,
    "plant": 24
  },
  "sample_count": 72,
  "schema_version": 1,
  "source_counts": {
    "plantvillage_label": 72
  },
  "split_counts": {
    "test": 15,
    "train": 48,
    "validation": 9
  }
}
```

## Split Policy

The builder sorts unique `image_id` values and assigns entire images to deterministic
train/validation/test buckets. It then creates three questions per image:

1. labeled plant;
2. labeled condition;
3. healthy vs diseased status.

The generated summary reports `entity_split_leakage: false`.

## Audit Status

All records currently have `audit_status: pending`. This means the schema and source
traceability are validated, but a human language-quality audit has not yet been completed.

## Limitations

- The seed contains only 24 images and 72 questions.
- It is built from Week 4 frozen samples, not the full PlantVillage train/validation/test
  split.
- It tests source-grounded VQA plumbing, not VLM generalization.
- It does not include treatment advice, pesticide instructions, or local regulatory
  recommendations.
- It should not be used to claim completed LoRA fine-tuning.
