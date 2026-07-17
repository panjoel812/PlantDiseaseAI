# Week 4 Grad-CAM Reproducibility Check

生成时间：2026-07-13

## 验证目标

对同一 checkpoint、同一冻结样本、同一目标类别和同一 target layer，执行两层复现性检查：

1. 重新生成 Grad-CAM atlas，比较原始 atlas 与复现 atlas 的样本元数据、PNG panel SHA256 和像素差异。
2. 在同一 CPU 进程内对每个样本连续生成两次原始 Grad-CAM heatmap 张量，直接比较数值差异，避免 PNG 编码和渲染量化影响。

## 输入与命令证据

- 原始 manifest：`outputs/plantvillage/week4_explainability/gradcam_atlas/gradcam_atlas_manifest.json`
- 复现 manifest：`outputs/plantvillage/week4_explainability/gradcam_atlas_repro/gradcam_atlas_manifest.json`
- checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- target layer：`layer4.2`
- target mode：`predicted`
- atlas 级机器可读复现性结果：`outputs/plantvillage/week4_explainability/gradcam_reproducibility.json`
- direct heatmap 机器可读复现性结果：`outputs/plantvillage/week4_explainability/gradcam_reproducibility_direct.json`

复现命令：

```bash
uv run plant-gradcam-atlas --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt --frozen-samples outputs/plantvillage/week4_explainability/frozen_samples.json --output-dir outputs/plantvillage/week4_explainability/gradcam_atlas_repro --cache-dir data/huggingface --report reports/week4_gradcam_atlas_repro.md --device cpu --target-layer layer4.2 --target-mode predicted --alpha 0.45 --colormap turbo
```

## 结果

- 样本数：`24`
- 元数据完全一致（排除输出路径）：`24/24`
- 直接 heatmap 张量精确一致：`24/24`，全局最大绝对差异 `0.0`
- PNG panel 字节级一致：`12/24`
- PNG panel 像素近似一致（最大通道差 ≤ 5/255）：`24/24`
- PNG panel 全局最大通道差：`5/255`；最大平均通道差：`4.52e-05`

结论：Grad-CAM heatmap 本身在当前 CPU 环境、固定输入与固定目标类别下可复现；atlas PNG 重新渲染时有少量像素级量化差异，因此报告同时保留 SHA256 和像素容差证据。

## 样本哈希摘要

| group | test_index | target | metadata match | panel SHA256 match | original SHA256 prefix |
| --- | ---: | --- | --- | --- | --- |
| correct_high_confidence | 1175 | `Corn_(maize)___Northern_Leaf_Blight` | True | True | `fa15bbbd8b110044` |
| correct_high_confidence | 7821 | `Squash___Powdery_mildew` | True | False | `87226ad033f495ec` |
| correct_high_confidence | 9748 | `Tomato___Leaf_Mold` | True | True | `8e6924a81378a215` |
| correct_high_confidence | 9749 | `Tomato___Leaf_Mold` | True | False | `dc1be76d1c5ff358` |
| correct_high_confidence | 9750 | `Tomato___Leaf_Mold` | True | False | `b966e687090a75b8` |
| correct_high_confidence | 9852 | `Tomato___Leaf_Mold` | True | True | `9f9d1e5bff6583fa` |
| correct_low_confidence | 691 | `Tomato___Early_blight` | True | True | `0e41597f4d2a938a` |
| correct_low_confidence | 953 | `Apple___healthy` | True | True | `5c55e70aeeae874d` |
| correct_low_confidence | 5269 | `Tomato___Target_Spot` | True | False | `ef8d5a345afa8d9d` |
| correct_low_confidence | 6272 | `Apple___Apple_scab` | True | True | `c681adbe367b3d1d` |
| correct_low_confidence | 6611 | `Tomato___Septoria_leaf_spot` | True | False | `eb6e9c956a1be55c` |
| correct_low_confidence | 9443 | `Apple___Black_rot` | True | True | `e2e03361e627e095` |
| error_high_confidence | 166 | `Tomato___Late_blight` | True | True | `2035f2a239841c1e` |
| error_high_confidence | 198 | `Tomato___Late_blight` | True | True | `6798d183f27df040` |
| error_high_confidence | 530 | `Tomato___Target_Spot` | True | False | `98e50506f9a075d7` |
| error_high_confidence | 1099 | `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | True | False | `eddc1ccced81e776` |
| error_high_confidence | 5109 | `Tomato___Spider_mites Two-spotted_spider_mite` | True | True | `2fe1487787e95e1d` |
| error_high_confidence | 6270 | `Apple___healthy` | True | False | `fba207c4328c8773` |
| error_low_confidence | 957 | `Blueberry___healthy` | True | True | `7ef24e03fdde6dc7` |
| error_low_confidence | 3453 | `Corn_(maize)___Northern_Leaf_Blight` | True | False | `f82a52617cd4bb4f` |
| error_low_confidence | 6186 | `Tomato___Target_Spot` | True | False | `0f5636d0be9ac1e6` |
| error_low_confidence | 6690 | `Tomato___Early_blight` | True | True | `3df3656f9888967f` |
| error_low_confidence | 8965 | `Corn_(maize)___Common_rust_` | True | False | `e7593f798e4be043` |
| error_low_confidence | 9448 | `Blueberry___healthy` | True | False | `8b08ec4e70517081` |

## 边界

该检查证明当前 CPU 环境、当前依赖版本和固定输入下 Grad-CAM heatmap 数值可复现；PNG panel 作为展示图，允许由渲染/量化产生的极小像素差异。不声称不同设备后端（例如 MPS/GPU）逐位一致。
