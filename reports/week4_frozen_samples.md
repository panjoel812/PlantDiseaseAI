# Week 4 Frozen Explainability Samples

生成时间：2026-07-13

## 冻结对象

- 模型：`resnet50`
- Checkpoint：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt`
- Split manifest：`outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json`
- 目标层：`layer4.2`
- 逐样本预测：`outputs/plantvillage/week4_explainability/predictions.json`
- 冻结样本：`outputs/plantvillage/week4_explainability/frozen_samples.json`

## 生成命令

```bash
uv run plant-freeze-samples \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --split-manifest outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/split.json \
  --output-dir outputs/plantvillage/week4_explainability \
  --cache-dir data/huggingface \
  --samples-per-group 6 \
  --top-k 5 \
  --batch-size 64 \
  --device auto \
  --target-layer layer4.2 \
  --progress-every 10
```

## 运行结果

- 逐样本预测数量：`10709`
- 每组目标样本数：`6`
- 当前说明：预测记录和冻结索引不受目标层影响；本轮已按修正后的 `layer4.2` 重新生成 manifest 元数据。
- 实际选中：
  - `correct_high_confidence`: `6`
  - `correct_low_confidence`: `6`
  - `error_high_confidence`: `6`
  - `error_low_confidence`: `6`

## 冻结索引

索引为官方 Hugging Face `test` split 内的 `test_index`。

| 分组 | test_index |
| --- | --- |
| `correct_high_confidence` | `9750`, `1175`, `9749`, `9748`, `9852`, `7821` |
| `correct_low_confidence` | `6611`, `9443`, `5269`, `691`, `953`, `6272` |
| `error_high_confidence` | `198`, `6270`, `5109`, `1099`, `530`, `166` |
| `error_low_confidence` | `3453`, `9448`, `957`, `6186`, `8965`, `6690` |

## 解释边界

这些索引用于固定 Week 4 Grad-CAM 图集和错误分析样本，避免只挑选好看的案例。Grad-CAM 后续结果只能解释为目标类别分数与输入区域的相关性热力图，不能表述为因果解释，也不能代表真实田间泛化能力。

## 目标层修正说明

`test_index=9750` 的高置信正确样本暴露出旧目标层 `layer4.2.conv3` 的解释图偏差：该层位于 ResNet bottleneck 内部、残差合并之前，热力峰值会落到叶片外背景区域。诊断对比显示，同一张图改用最后一个 residual block 输出 `layer4.2` 后，热点回到叶片区域。因此正式 Week 4 ResNet50 目标层修正为 `layer4.2`；冻结样本索引不变，因为索引由预测结果决定，不依赖 Grad-CAM 目标层。
