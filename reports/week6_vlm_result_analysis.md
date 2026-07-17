# Week 6 VLM Result Analysis

## Dataset Audit

- Samples: 72
- Images: 24
- Automated quality status: `needs_human_audit`
- Repeated question templates: 3
- Empty answers: 0

## Result Analyses

### outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json

- Status: `completed`
- Model: `mlx-community/Qwen3-VL-4B-Instruct-4bit`
- Prompt style: `original`
- Questions: 15

| question_type | correct | total | exact_match |
| --- | ---: | ---: | ---: |
| condition | 0 | 5 | 0.0000 |
| health_status | 0 | 5 | 0.0000 |
| plant | 0 | 5 | 0.0000 |

Top confusions:

- condition: expected `Leaf Mold`, got `the condition shown in this plantvillage image is tomato leaf spot this is a common fungal disease affecting tomato plants characterized by the yellowing` (1x)
- condition: expected `Leaf Mold`, got `the image shows a leaf with yellowing and browning spots which is characteristic of leaf spot a common fungal disease affecting many plants this condition` (1x)
- condition: expected `Leaf Mold`, got `the image shows tomato leaf curl this condition is typically caused by the tomato leaf curl virus tolcv often transmitted by` (1x)
- condition: expected `Leaf Mold`, got `the image shows tomato leaf spot this condition is caused by the fungus colletotrichum lycopersici which leads to the` (1x)
- condition: expected `healthy`, got `the image shows a leaf affected by leaf spot pseudomonas syringae a common bacterial disease in plants this condition is characterized by` (1x)
- health_status: expected `diseased`, got `the plant condition shown in the image is diseased here s why the leaf exhibits yellowing chlorosis in patches` (1x)
- health_status: expected `diseased`, got `the plant condition shown in the image is diseased the leaf exhibits clear signs of a plant disease likely a fungal or bacterial infection such as` (1x)
- health_status: expected `diseased`, got `the plant condition shown in the image is diseased the leaf exhibits clear signs of a plant disease likely a fungal or viral infection characterized` (1x)
- health_status: expected `diseased`, got `the plant condition shown in the image is diseased the leaf exhibits several clear signs of disease or stress yellowing chlorosis` (1x)
- health_status: expected `healthy`, got `based on the image provided the plant condition appears to be healthy here s a breakdown of the visual evidence leaf color the leaf` (1x)
- plant: expected `Apple`, got `the plant shown in the image is peach prunus persica this is a common fruit tree and the leaf morphology` (1x)
- plant: expected `Tomato`, got `according to the plantvillage label the plant shown is tomato` (4x)

Potential hallucination / safety flags:

- vqa-test-hf-test-957-condition: markers `bacterial, pseudomonas` in answer `The image shows a leaf affected by **Leaf spot (Pseudomonas syringae)**, a common bacterial disease in plants. This condition is characterized by`
- vqa-test-hf-test-9748-condition: markers `virus, tolcv` in answer `The image shows **Tomato leaf curl**.

This condition is typically caused by the **Tomato leaf curl virus (ToLCV)**, often transmitted by`
- vqa-test-hf-test-9748-health_status: markers `fungal` in answer `The plant condition shown in the image is **diseased**.

The leaf exhibits clear signs of a plant disease, likely a fungal or viral infection, characterized`
- vqa-test-hf-test-9749-condition: markers `fungal` in answer `The image shows a leaf with yellowing and browning spots, which is characteristic of **Leaf Spot** — a common fungal disease affecting many plants. This condition`
- vqa-test-hf-test-9750-condition: markers `fungus, colletotrichum` in answer `The image shows **Tomato leaf spot**.

This condition is caused by the fungus *Colletotrichum lycopersici*, which leads to the`
- vqa-test-hf-test-9852-condition: markers `fungal` in answer `The condition shown in this PlantVillage image is **Tomato leaf spot**.

This is a common fungal disease affecting tomato plants, characterized by the yellowing`
- vqa-test-hf-test-9852-health_status: markers `fungal, bacterial` in answer `The plant condition shown in the image is **diseased**.

The leaf exhibits clear signs of a plant disease, likely a fungal or bacterial infection such as`

### outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json

- Status: `completed`
- Model: `mlx-community/Qwen3-VL-4B-Instruct-4bit`
- Prompt style: `short`
- Questions: 15

| question_type | correct | total | exact_match |
| --- | ---: | ---: | ---: |
| condition | 0 | 5 | 0.0000 |
| health_status | 5 | 5 | 1.0000 |
| plant | 5 | 5 | 1.0000 |

Top confusions:

- condition: expected `Leaf Mold`, got `leaf spot disease` (1x)
- condition: expected `Leaf Mold`, got `tomato leaf curl virus` (2x)
- condition: expected `Leaf Mold`, got `tomato leaf spot disease` (1x)
- condition: expected `healthy`, got `leaf spot disease` (1x)

Potential hallucination / safety flags:

- vqa-test-hf-test-9748-condition: markers `virus` in answer `Tomato leaf curl virus`
- vqa-test-hf-test-9852-condition: markers `virus` in answer `Tomato leaf curl virus`

## Interpretation

This analysis is for a small Week 6 smoke baseline. It separates exact-match errors, condition-label confusions, and risky explanatory terms from the verified classifier results. It is not evidence of LoRA training or field diagnosis reliability.
