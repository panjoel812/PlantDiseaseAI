# Week 4 Baseline vs Final Same-Sample Grad-CAM Comparison

生成时间：2026-07-13

## 范围

本报告比较 Week 4 冻结样本中最终模型出错的 12 个样本。每个样本使用相同原图，分别运行 Week 3 `00_resnet50_baseline` 和 `09_combo_candidate`，并以各自 top-1 预测类别生成 Grad-CAM overlay。

- Baseline checkpoint：`outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42/checkpoint.pt`
- Final checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- 对比图：`reports/figures/week4_baseline_vs_final_gradcam.png`
- 机器可读结果：`outputs/plantvillage/week4_explainability/baseline_vs_final_gradcam.json`

## 汇总

- 样本数：`12`
- Baseline top-1 正确数：`4`
- Final top-1 正确数：`0`（该集合按 final 错误样本定义，因此为 0）
- Baseline 与 final top-1 完全相同：`5`

## 明细

| test_index | error_type | true | baseline top-1 | final top-1 | observation |
| ---: | --- | --- | --- | --- | --- |
| 198 | visual_similarity | `Potato___Late_blight` | `Potato___Late_blight` (0.950) | `Tomato___Late_blight` (0.848) | Baseline is correct on this final-model failure; compare overlays for changed focus. |
| 6270 | label_question | `Apple___Apple_scab` | `Apple___healthy` (0.866) | `Apple___healthy` (0.832) | Both models choose the same class; Grad-CAM difference mainly reflects confidence or spatial focus. |
| 5109 | visual_similarity | `Tomato___Target_Spot` | `Tomato___Target_Spot` (0.917) | `Tomato___Spider_mites Two-spotted_spider_mite` (0.767) | Baseline is correct on this final-model failure; compare overlays for changed focus. |
| 1099 | visual_similarity | `Corn_(maize)___Northern_Leaf_Blight` | `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` (0.542) | `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` (0.738) | Both models choose the same class; Grad-CAM difference mainly reflects confidence or spatial focus. |
| 530 | visual_similarity | `Tomato___Early_blight` | `Tomato___Target_Spot` (0.888) | `Tomato___Target_Spot` (0.724) | Both models choose the same class; Grad-CAM difference mainly reflects confidence or spatial focus. |
| 166 | visual_similarity | `Potato___Late_blight` | `Tomato___Early_blight` (0.762) | `Tomato___Late_blight` (0.724) | Both models fail but choose different classes, indicating unstable class evidence on this sample. |
| 3453 | low_quality | `Soybean___healthy` | `Peach___healthy` (0.762) | `Corn_(maize)___Northern_Leaf_Blight` (0.195) | Both models fail but choose different classes, indicating unstable class evidence on this sample. |
| 9448 | label_question | `Apple___Black_rot` | `Apple___Black_rot` (0.517) | `Blueberry___healthy` (0.226) | Baseline is correct on this final-model failure; compare overlays for changed focus. |
| 957 | visual_similarity | `Apple___healthy` | `Apple___healthy` (0.980) | `Blueberry___healthy` (0.261) | Baseline is correct on this final-model failure; compare overlays for changed focus. |
| 6186 | visual_similarity | `Tomato___Bacterial_spot` | `Tomato___Target_Spot` (0.911) | `Tomato___Target_Spot` (0.326) | Both models choose the same class; Grad-CAM difference mainly reflects confidence or spatial focus. |
| 8965 | background_bias | `Blueberry___healthy` | `Tomato___Late_blight` (0.712) | `Corn_(maize)___Common_rust_` (0.327) | Both models fail but choose different classes, indicating unstable class evidence on this sample. |
| 6690 | visual_similarity | `Tomato___Septoria_leaf_spot` | `Tomato___Early_blight` (0.963) | `Tomato___Early_blight` (0.331) | Both models choose the same class; Grad-CAM difference mainly reflects confidence or spatial focus. |

## 解释边界

Grad-CAM overlay 只比较目标类别分数与输入区域的相关性，不证明因果机制。该对比集合专门选择最终模型错误样本，不能代表整体测试集分布。
