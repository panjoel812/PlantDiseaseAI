# Week 4 Attention And Failure-Type Review

生成时间：2026-07-13

## 摘要

本报告完成了 Week 4 固定 Grad-CAM 图集的视觉审阅。审阅对象为
`outputs/plantvillage/week4_explainability/gradcam_atlas/` 中 24 个固定样本：
正确高置信、正确低置信、错误高置信、错误低置信四组各 6 个。

审阅结果已写回本地机器可读文件：

- `outputs/plantvillage/week4_explainability/attention_review.json`

标签含义：

- `attention_region`：`leaf, lesion, background, shadow, border, mixed, unclear`
- `error_type`：`visual_similarity, background_bias, low_quality, occlusion, label_question, domain_shift, not_error, unclear`

## 统计

### 关注区域

| attention_region | count |
| --- | ---: |
| lesion | 14 |
| mixed | 4 |
| leaf | 4 |
| background | 2 |

### 错误类型

| error_type | count |
| --- | ---: |
| not_error | 12 |
| visual_similarity | 8 |
| label_question | 2 |
| low_quality | 1 |
| background_bias | 1 |

仅看 12 个错误样本，主要失败类型为视觉相似：`8/12`。这包括跨作物但症状相似的 late blight，以及同作物内部的小斑点类病害混淆。两个样本更像标签或可见症状疑问，一个样本缺少可见叶片，一个样本明显受黑色背景影响。

## 审阅明细

| group | test_index | true → pred | confidence | attention_region | error_type | review_note |
| --- | ---: | --- | ---: | --- | --- | --- |
| correct_high_confidence | 9750 | Tomato___Leaf_Mold → Tomato___Leaf_Mold | 0.9952 | lesion | not_error | Heatmap centers on diseased tomato leaf tissue; attention aligns with visible leaf mold texture. |
| correct_high_confidence | 1175 | Corn_(maize)___Northern_Leaf_Blight → Corn_(maize)___Northern_Leaf_Blight | 0.9941 | lesion | not_error | Heatmap follows the elongated blight lesion on the maize leaf; minor edge spillover is not dominant. |
| correct_high_confidence | 9749 | Tomato___Leaf_Mold → Tomato___Leaf_Mold | 0.9918 | lesion | not_error | Activation covers the central diseased tomato leaf area rather than the background. |
| correct_high_confidence | 9748 | Tomato___Leaf_Mold → Tomato___Leaf_Mold | 0.9910 | lesion | not_error | Activation is on the central leaf mold region with no major background focus. |
| correct_high_confidence | 9852 | Tomato___Leaf_Mold → Tomato___Leaf_Mold | 0.9901 | lesion | not_error | Hot region spans the main symptomatic leaf area with small edge spillover. |
| correct_high_confidence | 7821 | Squash___Powdery_mildew → Squash___Powdery_mildew | 0.9901 | mixed | not_error | Powdery mildew is diffuse across the leaf, so the heatmap covers broad leaf and symptom regions. |
| correct_low_confidence | 6611 | Tomato___Septoria_leaf_spot → Tomato___Septoria_leaf_spot | 0.1354 | mixed | not_error | Low-confidence correct case; activation is split between the narrow leaf and nearby background or shadow. |
| correct_low_confidence | 9443 | Apple___Black_rot → Apple___Black_rot | 0.2185 | lesion | not_error | Activation is on the lower damaged or spotty apple leaf area; confidence is low because the lesion is subtle and edge-cropped. |
| correct_low_confidence | 5269 | Tomato___Target_Spot → Tomato___Target_Spot | 0.3039 | lesion | not_error | Activation lands on multiple target-spot regions rather than plain background. |
| correct_low_confidence | 691 | Tomato___Early_blight → Tomato___Early_blight | 0.3376 | lesion | not_error | Activation is centered on spot or necrotic tissue consistent with early blight cues. |
| correct_low_confidence | 953 | Apple___healthy → Apple___healthy | 0.3615 | leaf | not_error | Healthy prediction uses leaf blade and edge cues; no lesion target is expected. |
| correct_low_confidence | 6272 | Apple___Apple_scab → Apple___Apple_scab | 0.3759 | mixed | not_error | Activation is near the upper leaf edge and possible scab area; low confidence reflects partial edge focus. |
| error_high_confidence | 198 | Potato___Late_blight → Tomato___Late_blight | 0.8475 | lesion | visual_similarity | Potato and tomato late blight share necrotic lesion texture; the model focuses on the true lesion but assigns the wrong crop/disease class. |
| error_high_confidence | 6270 | Apple___Apple_scab → Apple___healthy | 0.8322 | leaf | label_question | The Apple scab symptom is visually subtle; heatmap is broad leaf interior and the healthy prediction reflects weak or ambiguous visible symptoms. |
| error_high_confidence | 5109 | Tomato___Target_Spot → Tomato___Spider_mites Two-spotted_spider_mite | 0.7670 | lesion | visual_similarity | Target spot and two-spotted spider mite symptoms can both appear as small mottled spots; heatmap is on symptomatic leaf tissue. |
| error_high_confidence | 1099 | Corn_(maize)___Northern_Leaf_Blight → Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot | 0.7380 | mixed | visual_similarity | Corn northern leaf blight and Cercospora/gray leaf spot have similar elongated lesion patterns; activation mixes lesion, veins, and leaf texture. |
| error_high_confidence | 530 | Tomato___Early_blight → Tomato___Target_Spot | 0.7244 | lesion | visual_similarity | Tomato early blight and target spot are visually close spot diseases; heatmap centers on the symptomatic area. |
| error_high_confidence | 166 | Potato___Late_blight → Tomato___Late_blight | 0.7244 | lesion | visual_similarity | Severe late-blight necrosis dominates the leaf; heatmap follows diseased tissue and the wrong class likely reflects cross-crop symptom similarity. |
| error_low_confidence | 3453 | Soybean___healthy → Corn_(maize)___Northern_Leaf_Blight | 0.1950 | background | low_quality | No visible soybean leaf is present in the panel; activation is entirely on background texture. |
| error_low_confidence | 9448 | Apple___Black_rot → Blueberry___healthy | 0.2264 | leaf | label_question | The Apple black rot label is not obvious in the visible crop; heatmap is on broad healthy-looking leaf interior. |
| error_low_confidence | 957 | Apple___healthy → Blueberry___healthy | 0.2609 | leaf | visual_similarity | Healthy apple versus healthy blueberry confusion; activation uses green leaf blade and edge cues rather than disease evidence. |
| error_low_confidence | 6186 | Tomato___Bacterial_spot → Tomato___Target_Spot | 0.3263 | lesion | visual_similarity | Tomato bacterial spot and target spot both show small spot lesions; heatmap is on symptomatic leaf regions. |
| error_low_confidence | 8965 | Blueberry___healthy → Corn_(maize)___Common_rust_ | 0.3275 | background | background_bias | Black background dominates activation, leading to a corn rust prediction despite a healthy blueberry leaf. |
| error_low_confidence | 6690 | Tomato___Septoria_leaf_spot → Tomato___Early_blight | 0.3309 | lesion | visual_similarity | Septoria and early blight are similar tomato spot diseases; activation is on lower symptomatic leaf tissue. |

## 结论

1. 高置信正确样本大多关注病斑或病斑覆盖的叶片区域，说明代表性 Grad-CAM 没有明显只依赖背景。
2. 低置信正确样本更常出现 `mixed` 或边缘关注，说明低置信样本的可解释性更不稳定。
3. 错误样本以视觉相似为主，尤其是同作物 spot 类病害和跨作物 late blight 病斑相似。
4. 背景偏差不是主导失败类型，但存在明确案例：`test_index=8965` 的黑色背景显著影响热区。
5. `test_index=3453` 缺少可见叶片，属于低质量输入；这支持 Week 5 Demo 必须提示闭集模型和输入质量限制。

## 解释边界

Grad-CAM 只能说明目标类别分数与输入区域之间的相关性，不能作为因果解释。本报告是视觉审阅记录，不是植保专家诊断。所有结论仍受 PlantVillage 受控背景、官方 split `leaf_id` 重叠和单 seed 评估限制约束。
