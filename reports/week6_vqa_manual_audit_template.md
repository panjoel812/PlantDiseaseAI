# Manual VQA Audit Template

- Status: `pending_human_review`
- Dataset: `outputs/plantvillage/week6_vlm/vqa_seed.jsonl`
- Analysis: `outputs/plantvillage/week6_vlm/vlm_result_analysis.json`
- Entries: 72
- Unique images: 24
- Risk-flagged entries: 7

## Instructions

- Review every entry before changing review_status to passed or failed.
- Only mark answer_traceable_to_source as true when the answer follows from the stored label or curated source.
- Do not use model predictions as ground truth.
- Record ambiguous wording, duplicate-question problems, or agricultural-safety concerns in human_notes.

## Review entries

| sample_id | type | question | expected_answer | model_hint | risk_markers | review_status |
| --- | --- | --- | --- | --- | --- | --- |
| vqa-train-hf-test-1099-plant | plant | Which plant is shown according to the PlantVillage label? | Corn (maize) |  |  | pending_human_review |
| vqa-train-hf-test-1099-condition | condition | What labeled condition does this PlantVillage image show? | Northern Leaf Blight |  |  | pending_human_review |
| vqa-train-hf-test-1099-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-1175-plant | plant | Which plant is shown according to the PlantVillage label? | Corn (maize) |  |  | pending_human_review |
| vqa-train-hf-test-1175-condition | condition | What labeled condition does this PlantVillage image show? | Northern Leaf Blight |  |  | pending_human_review |
| vqa-train-hf-test-1175-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-166-plant | plant | Which plant is shown according to the PlantVillage label? | Potato |  |  | pending_human_review |
| vqa-train-hf-test-166-condition | condition | What labeled condition does this PlantVillage image show? | Late blight |  |  | pending_human_review |
| vqa-train-hf-test-166-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-198-plant | plant | Which plant is shown according to the PlantVillage label? | Potato |  |  | pending_human_review |
| vqa-train-hf-test-198-condition | condition | What labeled condition does this PlantVillage image show? | Late blight |  |  | pending_human_review |
| vqa-train-hf-test-198-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-3453-plant | plant | Which plant is shown according to the PlantVillage label? | Soybean |  |  | pending_human_review |
| vqa-train-hf-test-3453-condition | condition | What labeled condition does this PlantVillage image show? | healthy |  |  | pending_human_review |
| vqa-train-hf-test-3453-health_status | health_status | Is the labeled plant condition healthy or diseased? | healthy |  |  | pending_human_review |
| vqa-train-hf-test-5109-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-5109-condition | condition | What labeled condition does this PlantVillage image show? | Target Spot |  |  | pending_human_review |
| vqa-train-hf-test-5109-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-5269-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-5269-condition | condition | What labeled condition does this PlantVillage image show? | Target Spot |  |  | pending_human_review |
| vqa-train-hf-test-5269-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-530-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-530-condition | condition | What labeled condition does this PlantVillage image show? | Early blight |  |  | pending_human_review |
| vqa-train-hf-test-530-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-6186-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-6186-condition | condition | What labeled condition does this PlantVillage image show? | Bacterial spot |  |  | pending_human_review |
| vqa-train-hf-test-6186-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-6270-plant | plant | Which plant is shown according to the PlantVillage label? | Apple |  |  | pending_human_review |
| vqa-train-hf-test-6270-condition | condition | What labeled condition does this PlantVillage image show? | Apple scab |  |  | pending_human_review |
| vqa-train-hf-test-6270-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-6272-plant | plant | Which plant is shown according to the PlantVillage label? | Apple |  |  | pending_human_review |
| vqa-train-hf-test-6272-condition | condition | What labeled condition does this PlantVillage image show? | Apple scab |  |  | pending_human_review |
| vqa-train-hf-test-6272-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-6611-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-6611-condition | condition | What labeled condition does this PlantVillage image show? | Septoria leaf spot |  |  | pending_human_review |
| vqa-train-hf-test-6611-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-6690-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-6690-condition | condition | What labeled condition does this PlantVillage image show? | Septoria leaf spot |  |  | pending_human_review |
| vqa-train-hf-test-6690-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-691-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato |  |  | pending_human_review |
| vqa-train-hf-test-691-condition | condition | What labeled condition does this PlantVillage image show? | Early blight |  |  | pending_human_review |
| vqa-train-hf-test-691-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-7821-plant | plant | Which plant is shown according to the PlantVillage label? | Squash |  |  | pending_human_review |
| vqa-train-hf-test-7821-condition | condition | What labeled condition does this PlantVillage image show? | Powdery mildew |  |  | pending_human_review |
| vqa-train-hf-test-7821-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-train-hf-test-8965-plant | plant | Which plant is shown according to the PlantVillage label? | Blueberry |  |  | pending_human_review |
| vqa-train-hf-test-8965-condition | condition | What labeled condition does this PlantVillage image show? | healthy |  |  | pending_human_review |
| vqa-train-hf-test-8965-health_status | health_status | Is the labeled plant condition healthy or diseased? | healthy |  |  | pending_human_review |
| vqa-validation-hf-test-9443-plant | plant | Which plant is shown according to the PlantVillage label? | Apple |  |  | pending_human_review |
| vqa-validation-hf-test-9443-condition | condition | What labeled condition does this PlantVillage image show? | Black rot |  |  | pending_human_review |
| vqa-validation-hf-test-9443-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-validation-hf-test-9448-plant | plant | Which plant is shown according to the PlantVillage label? | Apple |  |  | pending_human_review |
| vqa-validation-hf-test-9448-condition | condition | What labeled condition does this PlantVillage image show? | Black rot |  |  | pending_human_review |
| vqa-validation-hf-test-9448-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased |  |  | pending_human_review |
| vqa-validation-hf-test-953-plant | plant | Which plant is shown according to the PlantVillage label? | Apple |  |  | pending_human_review |
| vqa-validation-hf-test-953-condition | condition | What labeled condition does this PlantVillage image show? | healthy |  |  | pending_human_review |
| vqa-validation-hf-test-953-health_status | health_status | Is the labeled plant condition healthy or diseased? | healthy |  |  | pending_human_review |
| vqa-test-hf-test-957-plant | plant | Which plant is shown according to the PlantVillage label? | Apple | the plant shown in the image is peach prunus persica this is a common fruit tree and the leaf morphology |  | pending_human_review |
| vqa-test-hf-test-957-condition | condition | What labeled condition does this PlantVillage image show? | healthy | the image shows a leaf affected by leaf spot pseudomonas syringae a common bacterial disease in plants this condition is characterized by | bacterial, pseudomonas | pending_human_review |
| vqa-test-hf-test-957-health_status | health_status | Is the labeled plant condition healthy or diseased? | healthy | based on the image provided the plant condition appears to be healthy here s a breakdown of the visual evidence leaf color the leaf |  | pending_human_review |
| vqa-test-hf-test-9748-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato | according to the plantvillage label the plant shown is tomato |  | pending_human_review |
| vqa-test-hf-test-9748-condition | condition | What labeled condition does this PlantVillage image show? | Leaf Mold | the image shows tomato leaf curl this condition is typically caused by the tomato leaf curl virus tolcv often transmitted by | virus, tolcv | pending_human_review |
| vqa-test-hf-test-9748-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased | the plant condition shown in the image is diseased the leaf exhibits clear signs of a plant disease likely a fungal or viral infection characterized | fungal | pending_human_review |
| vqa-test-hf-test-9749-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato | according to the plantvillage label the plant shown is tomato |  | pending_human_review |
| vqa-test-hf-test-9749-condition | condition | What labeled condition does this PlantVillage image show? | Leaf Mold | the image shows a leaf with yellowing and browning spots which is characteristic of leaf spot a common fungal disease affecting many plants this condition | fungal | pending_human_review |
| vqa-test-hf-test-9749-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased | the plant condition shown in the image is diseased here s why the leaf exhibits yellowing chlorosis in patches |  | pending_human_review |
| vqa-test-hf-test-9750-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato | according to the plantvillage label the plant shown is tomato |  | pending_human_review |
| vqa-test-hf-test-9750-condition | condition | What labeled condition does this PlantVillage image show? | Leaf Mold | the image shows tomato leaf spot this condition is caused by the fungus colletotrichum lycopersici which leads to the | fungus, colletotrichum | pending_human_review |
| vqa-test-hf-test-9750-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased | the plant condition shown in the image is diseased the leaf exhibits several clear signs of disease or stress yellowing chlorosis |  | pending_human_review |
| vqa-test-hf-test-9852-plant | plant | Which plant is shown according to the PlantVillage label? | Tomato | according to the plantvillage label the plant shown is tomato |  | pending_human_review |
| vqa-test-hf-test-9852-condition | condition | What labeled condition does this PlantVillage image show? | Leaf Mold | the condition shown in this plantvillage image is tomato leaf spot this is a common fungal disease affecting tomato plants characterized by the yellowing | fungal, virus | pending_human_review |
| vqa-test-hf-test-9852-health_status | health_status | Is the labeled plant condition healthy or diseased? | diseased | the plant condition shown in the image is diseased the leaf exhibits clear signs of a plant disease likely a fungal or bacterial infection such as | fungal, bacterial | pending_human_review |

This file is a template for human review. It is not evidence that the VQA dataset has passed manual audit until each entry is filled and reviewed.
