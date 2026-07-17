# Week 4 Error Analysis

生成时间：2026-07-13

## 摘要

- 样本数：`10709`
- 类别数：`38`
- Accuracy：`0.9953`
- Macro F1：`0.9941`
- 错误样本数：`50`
- 高置信错误阈值：`0.80`
- 高置信错误数：`2`

## 低 F1 类别

| class | precision | recall | f1 | support |
| --- | ---: | ---: | ---: | ---: |
| `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | 0.9712 | 0.9439 | 0.9573 | 107 |
| `Corn_(maize)___Northern_Leaf_Blight` | 0.9643 | 0.9818 | 0.9730 | 220 |
| `Tomato___Target_Spot` | 0.9726 | 0.9861 | 0.9793 | 288 |
| `Tomato___Early_blight` | 0.9952 | 0.9674 | 0.9811 | 215 |
| `Potato___Late_blight` | 0.9952 | 0.9717 | 0.9833 | 212 |
| `Apple___Apple_scab` | 1.0000 | 0.9685 | 0.9840 | 127 |
| `Apple___healthy` | 0.9792 | 0.9895 | 0.9843 | 286 |
| `Apple___Black_rot` | 1.0000 | 0.9726 | 0.9861 | 146 |

## 重点混淆对

| true → predicted | count | true-class share |
| --- | ---: | ---: |
| `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot → Corn_(maize)___Northern_Leaf_Blight` | 6 | 0.0561 |
| `Potato___Late_blight → Tomato___Late_blight` | 6 | 0.0283 |
| `Tomato___Early_blight → Tomato___Target_Spot` | 4 | 0.0186 |
| `Apple___Apple_scab → Apple___healthy` | 3 | 0.0236 |
| `Apple___Black_rot → Apple___healthy` | 3 | 0.0205 |
| `Corn_(maize)___Northern_Leaf_Blight → Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | 3 | 0.0136 |
| `Tomato___Target_Spot → Tomato___Spider_mites Two-spotted_spider_mite` | 3 | 0.0104 |
| `Tomato___Bacterial_spot → Tomato___Target_Spot` | 3 | 0.0069 |
| `Pepper,_bell___Bacterial_spot → Peach___Bacterial_spot` | 2 | 0.0120 |
| `Tomato___Early_blight → Tomato___Septoria_leaf_spot` | 2 | 0.0093 |

## 高置信错误样本

| test_index | true | predicted | confidence |
| ---: | --- | --- | ---: |
| `198` | `Potato___Late_blight` | `Tomato___Late_blight` | 0.8475 |
| `6270` | `Apple___Apple_scab` | `Apple___healthy` | 0.8322 |

## 解释边界

本报告从固定测试集指标和逐样本预测中总结错误模式。混淆对和高置信错误是后续人工审阅与 Grad-CAM 对照的入口，不能单独证明因果机制或真实田间泛化能力。
