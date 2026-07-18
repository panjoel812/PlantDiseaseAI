[English](README.md) | [简体中文](README.zh-CN.md)

本页是完整中文运行指南；如需对照术语，请查看[完整英文运行指南](README.md)。

平台表述仅表示项目预期接口，不代表每个平台都完成运行审计。Docker Engine/Desktop 未在本次发布环境中运行，Windows PowerShell 仅经过静态检查；本机使用 Apple `container`。用户上传的田间图片、论文和演示材料另有边界，详见[资源许可说明](ASSET_LICENSES.md)。

<p align="center"><strong>PLANTDISEASEAI · RESEARCH DEMO</strong></p>

# Evidence before diagnosis.

PlantVillage 闭集分类、Grad-CAM 相关性可视化、React / FastAPI 主演示、Streamlit / Apple `container` 兼容入口，以及明确标注边界的 Qwen3-VL smoke。

![PlantDiseaseAI React Liquid Glass demo](reports/figures/week8_react_demo_desktop.png)

| 0.9953 | 0.9941 | 5 models |
| ---: | ---: | ---: |
| Test Accuracy | Macro F1 | Shared benchmark |

> **Research boundary:** official split 含 227 个 train/test 重叠 `leaf_id`；结果不是田间泛化证明。Grad-CAM 不是因果解释，VLM 不是专业诊断系统。

[Animated demo](docs/media/week7_apple_demo.gif) · [20-slide research defense](docs/presentation/plantdisease_ai_week8_research_defense.pptx) · [中文论文](paper/out/plantdisease_ai_zh.pdf) · [English paper](paper/out/plantdisease_ai_en.pdf) · [Week 8 audit](reports/week8_reproducibility.md) · [Artifact index](docs/artifact-index.md)

*React Demo media uses the supplied field image with no verified ground truth; the visible result is a model prediction, not field-accuracy evidence.*

## React Demo

React Demo 默认加载用户提供的田间玉米叶图片 `app/examples/field_corn_leaf.jpeg`。该图片是无已验证真值的域外交互样例；页面返回的是模型预测，不是田间准确率或专业诊断结论。

结果现在按四步显示：

1. **OpenCV 单叶分离**：只接受轮廓清楚、未明显截断的一片叶子，去除背景，并展示透明 cutout、覆盖率、实心度和长宽比；多叶重叠时先要求用户点选目标叶片，整株或分离失败会在模型运行前拒绝。
2. **OpenCV 可见证据**：在原始分辨率上定位叶内病斑候选，报告面积、数量、最大区域、主要形状、粗粒度颜色、分布和叠加图。该步骤只描述像素，不根据手写规则诊断病害。
3. **植物识别与 unknown 门控**：隔离输入的 14 类 MobileNetV2 先判断植物。最高作物必须达到 `60%`、领先第二名 `10` 个百分点；配置原型索引时还需通过余弦相似度、原型间隔和分类头一致性检查。
4. **作物内病害**：只有前三步接受后，38 类 ResNet50 才保留已选作物的病害；最高条件达到 `65%` 且领先第二名 `15` 个百分点后才开放诊断、Grad-CAM 和管理建议。

这会阻止“低置信错误作物 → 高置信错误病害”的级联。作物模型与病害模型已经分离，但两者仍是 PlantVillage 闭集模型，不是开放世界植物学识别器，也不能证明田间准确率。OpenCV 病斑遮罩只是确定性的可见证据估计，不是真值分割或病害分类器。

### 开放世界分层识别研究（实验支线）

为解决“域外葡萄叶被强制判成番茄，再继续输出番茄病害”的根本问题，OpenLeaf-14 的单叶分离与实验性拒识门控现已接入 React Demo：

```text
图片 → OpenCV 自动提取优势叶片，或一键点选目标叶片 + 纯度门控
     → 本地 114 类目录（UCI 100 + PlantVillage 14）
     → 仅当本地身份不确定时调用可选 Pl@ntNet 广域身份
                  → 接受植物 → 叶片内病斑框/局部 crop → 宿主专用病害模型
                  → 未知植物 → 不输出病害
```

离线低算力默认路径现在是冻结 MobileNetV2 + 本地 114 类线性头：UCI Leaf100 的 100 种受控叶片轮廓，加上 PlantVillage 14 种作物。只有一片前景明显占优时 OpenCV 才自动选择；若至少两片可行绿色组件重叠、最佳组件不足可行前景的 90%，API 会先返回 `409 leaf_selection_required`，页面要求用户点一下目标叶片，而不是猜测。原有轮廓代理原型门控默认关闭，仅保留为显式实验选项。

### 一键点选叶片与玉米非生物胁迫拒答

点选发生在模型运行之前。React 摄影卡把点击位置换算为原图归一化坐标，并显示固定十字标记；鼠标经过不会造成标记抖动，方向键可按 `0.01` 微调。点击种子的 GrabCut 必须包含点击点、保留足够候选前景、通过长叶主轴纯度检查、覆盖原图 `3%–85%`，且边界接触不超过 `0.18`。任何门控失败都保留可审计原因，但不会进入植物或疾病模型。

植物身份接受为 Corn 后，另一个独立 OpenCV 安全门控只测量中脉方向的黄/褐/干枯形态：异常覆盖率、中轴占比、纵向连续性、两侧对称性和离轴离散病斑。五项固定条件全部满足时，页面只显示 **Suspected abiotic / nutrient stress**，清除传染性病名、疾病知识、诊断 Grad-CAM 和管理建议权限；闭集疾病分数只能作为“counterfactual only”证据展示。这个分支**不能确认缺氮**，具体原因仍需土壤/组织检测与本地农艺背景。

网页会自动发送坐标；直接调用 API 时可使用：

```bash
curl -X POST http://127.0.0.1:8000/api/classify \
  -F image=@/你的路径/leaf.jpg \
  -F target_x=0.43 -F target_y=0.47 \
  -F top_k=5 -F include_gradcam=true
```

`target_x` 与 `target_y` 必须同时提供，且均为 `[0, 1]` 内有限值；非法输入在模型前返回 HTTP 422。详见[目标叶片与非生物门控 QA](reports/target-leaf-abiotic-qa.md)和[机器可读证据](reports/metrics/target_leaf_abiotic_qa.json)。

植物身份、疾病 ResNet50 与 Grad-CAM 现在使用同一张 OpenCV 分离叶片和中性背景图，不再向模型暴露手、土壤、天空、花盆或相邻植物。病斑面积、颜色、形状和分布通常保持为独立可见证据。当前仅为 Grape 启用一个明确标记为实验性的窄范围保护：当整叶模型把 `healthy` 排第一、但病斑覆盖超过由训练集健康葡萄叶校准的阈值时，使用两个中性背景病斑 ROI 仅在已确认的葡萄病害类别中重新排序，并生成候选病斑 Grad-CAM。ROI 分数没有田间校准，因此仍不开放正式诊断和管理建议。详见[葡萄病斑聚焦 pilot](reports/grape_lesion_focus_pilot.md)。该处理只能减少背景线索并暴露证据冲突，不等同于已证明田间准确率提升；分割质量不合格时会拒绝分类。

seed 42 实跑使用 1,896 张训练、524 张验证和 748 张测试图；混合受控测试 Accuracy `0.9158`、Macro F1 `0.9117`，UCI 子集 Accuracy `0.9133`，PlantVillage 子集 `0.9174`。这些不是田间准确率。用户提供的田间葡萄图上，本地模型输出 Strawberry `46.36%`、Peach `24.01%`、Grape `20.65%`，因此正确行为仍是拒绝病害，而不是降低阈值。详见[本地 114 类 pilot 报告](reports/openleaf114_local_pilot.md)。

如需更强的田间广域身份，可在 React 页面的 Classifier 面板中直接配置临时 Pl@ntNet API key。本地预测通过门控时不会请求 Pl@ntNet；只有本地身份不确定或本地 checkpoint 不可用时才调用，以节省每日额度。官方当前 Free 方案为 `€0`、每天 500 次识别、可识别 50,000+ 物种；自 2026-02-13 起失败请求也消耗免费额度。密钥只保存在 FastAPI 进程内，也可通过 `PLANTNET_API_KEY` 提供，不会回传浏览器。价格与额度可能变化，请以[官方价格](https://my.plantnet.org/pricing)、[额度说明](https://my.plantnet.org/doc/api/quota)和[条款](https://my.plantnet.org/terms_of_use)为准。

候选叶片仍需轮廓完整、面积合理且没有明显被边缘截断；多叶照片会选择质量最好的一片，严重重叠到无法形成合格轮廓时才会拒绝。花、果实、整株和分离失败仍会要求重新拍摄。叶形是重要证据，但近缘物种叶形可能相似，病害也可能改变轮廓，因此物种识别仍同时观察去背景后的叶脉与纹理，不能只靠手写形状规则下结论。Pl@ntNet 的账户、配额、输入和分数语义见[官方单物种识别 API](https://my.plantnet.org/doc/api/identify)。

已完成一个低算力真实 pilot：896 张训练、224 张验证、448 张被 OpenCV 接受的 official-test 叶片，条件 Accuracy `0.9241`、Macro F1 `0.9230`；若把 469 个尝试样本中的 21 个预处理拒绝也计为端到端失败，管线成功率为 `0.8827`。这些数字来自小样本、单 seed、PlantVillage 闭集协议，不能与旧作物 checkpoint 直接比较，也不是 OOD 或田间指标。详见[OpenLeaf-14 pilot 报告](reports/openleaf14_pilot.md)。

随后用其中 6 类临时作为伪未知类完成内部拒识 sanity check：unknown AUROC `0.7530`；已接受的已知叶片准确率 `0.9753`，但已知覆盖率只有 `0.6328`，伪未知误接受率仍为 `0.2083`。这不是外部 OOD 证据，反而说明 MobileNetV2 原型门控尚不能部署。详见[六类留出报告](reports/openleaf14_open_set_holdout6.md)。

这里的目标是“可扩展的已知植物目录 + 明确的 unknown”，不是声称能识别世界上所有植物。完整数据协议、Pl@ntNet-300K / PlantWild / PlantSeg 数据阶梯、开放集指标、算力档位与命令见[开放世界研究方案](docs/research/open_world_hierarchical_plant_research.md)；默认配置见[`configs/openworld_research.yaml`](configs/openworld_research.yaml)，清单格式见[`configs/openworld_manifest.example.jsonl`](configs/openworld_manifest.example.jsonl)，已运行验证及其边界见[研究脚手架证据](reports/openworld_research_scaffold.md)。目前只完成研究脚手架与合成验证，不声称已得到真实大规模数据指标。

新版界面使用 `liquid-glass-react` 提供轻量材质边缘，并以雾白、浅蓝、嫩绿构成通透背景。React Demo 采用“先上传、后查看结果”的纵向流程：摄影卡与 Analyze 操作位于顶部，分析成功后页面会移动到照片下方完整展开的 Classifier 与 Management guidance。结果卡使用正常文档流，不再通过嵌套纵向滚动隐藏证据；移动端保持“上传 → 分类器 → 助手”的顺序。大型卡片保持零弹性，底部叶片与露珠不接收指针事件并在 `prefers-reduced-motion` 下停止。页眉 Logo 将用户提供的 Desmos Bézier 内部曲线与 PlantDiseaseAI 叶片融合；外部源 SVG 保持原样，运行时不依赖该个人路径。

从[UCI 官方页面](https://archive.ics.uci.edu/dataset/241/one%2Bhundred%2Bplant%2Bspecies%2Bleaves%2Bdata%2Bset)下载约 35 MB、CC BY 4.0 的 Leaf100 zip；PlantVillage 缓存就绪后训练本地 114 类头。权重保存在被 Git 忽略的 `outputs/`：

```bash
uv run python scripts/train_leaf_catalog.py \
  --uci-archive /你的路径/uci_leaf100.zip \
  --cache-dir data/huggingface \
  --output-dir outputs/openleaf/leaf114_uci100_pv14_balanced_seed42 \
  --head-epochs 80 --device cpu --seed 42
```

随后在两个终端分别启动同时使用作物与病害 checkpoint 的 FastAPI 和 React：

```bash
uv run python scripts/run_demo_api.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --crop-checkpoint outputs/openleaf/leaf114_uci100_pv14_balanced_seed42/checkpoint.pt \
  --device mps --host 127.0.0.1 --port 8000
```

原型索引默认关闭；只有显式传入 `--openworld-index outputs/plantvillage/leaf14_external_ood_shape6_seed42/index` 才会启用。省略该参数时 Demo 仍执行最佳叶片选择、作物概率与间隔门控，但不会声称完成 unknown 拒识。现有阈值来自受控无纹理轮廓代理，不是彩色田间 OOD 校准，页面会明确显示该证据边界。

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
# production bundle verification
npm run build
```

浏览器访问 `http://127.0.0.1:5173/`。分类、Top-5 与 Grad-CAM 使用本地 checkpoint；Qwen 是可选本地探索能力，仅在 Apple Silicon、`uv sync --group vlm` 已安装 MLX-VLM 且 `mlx-community/Qwen3-VL-4B-Instruct-4bit` 权重已存在于本地 Hugging Face cache 时可用。**No automatic download:** API 只检查本地 cache，不会自动下载模型权重。固定 smoke 边界仍为 choice/few-shot `11/15`、fine-grained condition `1/5`，不代表完整 VQA 评估或专业诊断能力。

首次本地体验 Qwen 时，需要明确允许一次约 3 GB 的模型下载；完成后重新启动 API，并在已打开的 React 面板点击 **Check again**（或刷新页面），面板才会重新读取 `/api/qwen/status`：

```bash
uv sync --group vlm
uv run --group vlm hf download mlx-community/Qwen3-VL-4B-Instruct-4bit
```

### Qwen visual evidence 与云端管理建议

React 助手卡现在明确分为两个互不混淆的模式：

- **Visual evidence**：可选本地 Qwen3-VL 只描述图片中可见的斑点、颜色、形状、边缘、纹理和分布。低置信或域外警告不会阻断这类像素观察，但诊断、治疗、农药剂量和法规问题不会发送给 Qwen。主界面只显示最多六条清理后的完整观察；原始模型文本保留在默认关闭的 **Raw response** 中供审计。
- **Management guidance**：用户在页面中手动选择 OpenAI、Claude 或 Gemini。服务端把作物优先分类假设、概率、警告以及可选的 Qwen 视觉观察作为不确定证据，生成有条件的教育性管理建议。

三家云端供应商彼此独立，**没有 automatic fallback**。页面会始终显示当前选中的供应商；未配置的供应商显示 `Not configured` 并保持禁用。

本地体验时，可直接打开助手顶部的 **API setup**，为准备使用的供应商粘贴 API Key。密码输入框在请求成功后立即清空；Key 通过 `POST /api/advice/providers/{provider}/configure` 发送，只保存在加锁的 FastAPI **进程内存**中，不会返回页面、写入 React state、`localStorage`、`sessionStorage`、Cookie、URL 或 Git。点击 **Clear** 会调用 DELETE 清除覆盖值；重启 API 也会全部清除。临时值只在当前进程覆盖同名环境变量，配置动作本身不会产生付费模型调用。

服务端部署仍推荐使用环境变量或正式 Secret Manager。按需在启动 FastAPI 的同一个终端设置供应商 Key；模型名都有当前默认值，也可以显式覆盖，完整模板见 `.env.example`：

```bash
# OpenAI Responses API
export OPENAI_API_KEY="your-server-side-key"
export OPENAI_MODEL="gpt-5.4-mini"

# Anthropic Messages API
export ANTHROPIC_API_KEY="your-server-side-key"
export ANTHROPIC_MODEL="claude-sonnet-5"

# Gemini Interactions API
export GEMINI_API_KEY="your-server-side-key"
export GEMINI_MODEL="gemini-3.5-flash"
```

只需要设置准备使用的供应商。随后照常启动 FastAPI 与 React；浏览器从 `/api/advice/providers` 读取非敏感配置状态，并把建议请求发送到 `/api/advice/ask`。请不要使用 `VITE_OPENAI_API_KEY`、`VITE_ANTHROPIC_API_KEY` 或类似前端环境变量，它们会被打包进浏览器代码。

网页配置入口面向 localhost。如果把 API 暴露到其他机器，必须使用 HTTPS、身份认证与服务端 Secret Manager，不能通过不可信连接传输凭据。

云端 API 需要网络、对应账户、有效凭据，并可能产生费用。本仓库自动测试使用注入的本地假传输，验证三种原生 API 载荷和错误处理，不会访问付费接口；在没有用户凭据时，不能声称真实云端回答已经端到端验证。

“如何管理/下一步做什么”可以获得低风险、条件式建议；具体农药产品、剂量、浓度、稀释比例、复入间隔和采收安全间隔仍会被本地边界拦截，因为这些内容必须依据作物、地区和已登记产品标签。所有回答均为教育用途，不是专业农业诊断或处方。

## 快速开始

需要 Python 3.12 与 [uv](https://docs.astral.sh/uv/)。

```bash
uv sync --all-groups
uv run pytest -q
uv run ruff check .
uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32
```

## 新生教程

如果你刚开始学习 AI 项目，建议先读 [docs/tutorials/README.md](docs/tutorials/README.md)。教程按 Dataset、Transform、Model、Train、Metrics 和基础数学六个主题解释本项目代码。

公开展示用的架构和功能说明见 [docs/project-architecture.md](docs/project-architecture.md)。

冒烟运行会生成：

- 固定 split 与数据审计 JSON；
- MobileNetV2 单 batch 过拟合 Loss；
- checkpoint、测试指标与 Top-2 预测；
- 类别分布、尺寸分布与样本图；
- Python、PyTorch、设备和验证范围清单。

## PlantVillage 数据

仓库适配器固定使用已检查的上游 loader revision，并锁定仍支持该脚本的 `datasets 3.x`。上游数据约 2 GB，下载到被 Git 忽略的 `data/huggingface/`：

```bash
uv run python scripts/download_data.py --cache-dir data/huggingface
uv run plant-audit \
  --cache-dir data/huggingface \
  --output outputs/plantvillage/audit.json
uv run python scripts/eda.py \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/eda
```

完成数据下载后，可先跑一个真实数据小样本训练管线验证：

```bash
uv run plant-train \
  --config configs/smoke_plantvillage_mobilenet_v2.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/smoke_mobilenet_v2_seed42 \
  --max-samples 500 \
  --log-every 5
```

这只验证 PlantVillage 数据能够进入训练—评估—checkpoint 链路，不代表正式模型效果。

正式 MobileNetV2 baseline 使用完整数据、224 输入尺寸和预训练权重：

```bash
uv run plant-train \
  --config configs/baseline_mobilenet_v2.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/baseline_mobilenet_v2_seed42 \
  --log-every 20
```

运行结束后查看正式测试集指标：

```bash
uv run plant-evaluate \
  --metrics outputs/plantvillage/baseline_mobilenet_v2_seed42/metrics.json
```

当前已验证 baseline 产物：

- `outputs/plantvillage/baseline_mobilenet_v2_seed42/metrics.json`
- `outputs/plantvillage/baseline_mobilenet_v2_seed42/checkpoint.pt`
- `outputs/plantvillage/baseline_mobilenet_v2_seed42/training_curve.png`
- `outputs/plantvillage/baseline_mobilenet_v2_seed42/run_manifest.json`

训练会输出当前 epoch、batch 进度、已处理样本数和当前 batch loss。PlantVillage 正式训练使用 Hugging Face split 懒加载图片，只在 batch 读取时解码单张图片，避免一次性把完整图片集载入内存。

## Week 2 Benchmark 进度

当前报告见 [reports/week2_benchmark_progress.md](reports/week2_benchmark_progress.md)。截至 2026-07-11，五个候选模型的正式训练和效率测量均已完成：

| 模型 | Test Acc | Test Macro F1 | Params | FLOPs | Latency | Throughput |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| MobileNetV2 | 0.9760 | 0.9674 | 2.27M | 0.31G | 6.49 ms | 644.3 img/s |
| ResNet18 | 0.9774 | 0.9661 | 11.20M | 1.82G | 2.82 ms | 564.5 img/s |
| ResNet50 | 0.9830 | 0.9743 | 23.59M | 4.11G | 7.42 ms | 165.9 img/s |
| EfficientNet-B0 | 0.9804 | 0.9703 | 4.06M | 0.40G | 7.25 ms | 305.6 img/s |
| EfficientNetV2-S | 0.9794 | 0.9708 | 20.23M | 2.88G | 14.99 ms | 133.4 img/s |

效率测量使用 MPS、float32、batch-1 延迟、batch-32 吞吐、10 次 warmup、50 次测量，且不包含预处理。峰值内存未测量。

如果要做更适合学习调试的均衡小实验，可按每个类别取固定数量样本：

```bash
uv run plant-train \
  --config configs/baseline_mobilenet_v2.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/balanced_probe10_mobilenet_v2_seed42 \
  --samples-per-class 10 \
  --log-every 10
```

均衡小实验用于理解采样、训练和指标，不替代完整 baseline。

官方 split 包含 `leaf_id`。本地检查发现 train/test 有 227 个重叠 `leaf_id`，后续 Week 2 Benchmark 应补充叶片实体隔离 split，或在所有官方 split 结果中明确标注该限制。

## Week 3 Ablation 进度

消融矩阵见 [reports/week3_ablation_matrix.md](reports/week3_ablation_matrix.md)，当前结果见 [reports/week3_ablation_results.md](reports/week3_ablation_results.md)。当前已实现并测试：

- RandAugment、Random Erasing、Mixup、CutMix；
- Label Smoothing、Focal Loss、soft-label Cross Entropy；
- 按 batch step 的 Cosine scheduler；
- EMA 参数滑动平均与评估时权重切换；
- baseline 训练入口的配置记录、manifest 和 checkpoint 方法记录。

关闭全部改进开关的冻结 ResNet50 基线已经完成，并确认与 Week 2 协议可比：

```bash
uv run plant-train \
  --config configs/week3_ablation/00_resnet50_baseline.yaml \
  --cache-dir data/huggingface \
  --output-dir outputs/plantvillage/week3_ablation/00_resnet50_baseline_seed42 \
  --log-every 50
```

`01_label_smoothing` 已完成，seed 42 单次测试 Macro F1 为 0.9865。`02_focal_loss` 也已完成，seed 42 单次测试 Macro F1 为 0.9652，低于 00 baseline。`03_cosine_scheduler` 已完成，seed 42 单次测试 Macro F1 为 0.9898，是最强单变量。`04_ema` 已完成，seed 42 单次测试 Macro F1 为 0.9673，低于 00 baseline。`05_randaugment` 已完成，seed 42 单次测试 Macro F1 为 0.9698，低于 00 baseline。`06_random_erasing` 已完成，seed 42 单次测试 Macro F1 为 0.9683，低于 00 baseline。`07_mixup` 已完成，seed 42 单次测试 Macro F1 为 0.9793，高于 00 baseline 但低于 Label Smoothing 和 Cosine Scheduler。`08_cutmix` 已完成，seed 42 单次测试 Macro F1 为 0.9863，接近 Label Smoothing 但低于 Cosine Scheduler。`09_combo_candidate` 已完成，组合 Label Smoothing `0.1` + Cosine Scheduler，seed 42 单次测试 Macro F1 为 0.9941，是当前最强候选。

当前候选 checkpoint 可用于 Week 4 Grad-CAM / 错误分析，也可直接做单图 Top-5 推理：

```bash
uv run plant-predict \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --image /path/to/image.jpg \
  --top-k 5
```

## Week 4：Grad-CAM 基础能力

项目已实现原生 PyTorch Grad-CAM 核心和统一目标层解析，单张及批量热力图会对齐输入尺寸并逐样本归一化到 `[0, 1]`；即使调用方外层处于 `torch.inference_mode()`，核心也会在内部临时启用 autograd 以生成梯度。当前正式候选使用 `09_combo_candidate` ResNet50 checkpoint，目标层冻结为最后一个 residual block 输出 `layer4.2`。

已新增逐样本预测记录与四象限样本冻结入口，并已生成本地证据：

- 逐样本预测：`outputs/plantvillage/week4_explainability/predictions.json`，`10709` 条
- 冻结样本：`outputs/plantvillage/week4_explainability/frozen_samples.json`
- 摘要报告：`reports/week4_frozen_samples.md`

复现命令为：

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

当前固定样本索引、Grad-CAM 图集、错误分析报告、人工审阅、校准分析、baseline/final 同样本对比、Grad-CAM 复现性验证和 Week 1–4 阶段报告均已生成。Grad-CAM 表示相关性，不能作为因果解释或真实田间泛化证据。

固定样本 Grad-CAM 图集可用以下命令生成。默认 target 为预测类别，用于解释模型为什么给出该预测；错误样本同样解释错误预测类别。

```bash
uv run plant-gradcam-atlas \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --frozen-samples outputs/plantvillage/week4_explainability/frozen_samples.json \
  --output-dir outputs/plantvillage/week4_explainability/gradcam_atlas \
  --cache-dir data/huggingface \
  --report reports/week4_gradcam_atlas.md \
  --device auto \
  --target-layer layer4.2 \
  --target-mode predicted \
  --alpha 0.45 \
  --colormap turbo
```

图集产物：

- 图集目录：`outputs/plantvillage/week4_explainability/gradcam_atlas/`
- 图集 manifest：`outputs/plantvillage/week4_explainability/gradcam_atlas/gradcam_atlas_manifest.json`
- 摘要报告：`reports/week4_gradcam_atlas.md`

错误分析可用以下命令复现。输出 JSON 包含非归一化混淆矩阵、行归一化混淆矩阵、低 F1 类别、重点混淆对和高置信错误样本；Markdown 报告保留重点项用于阶段报告引用。

```bash
uv run plant-error-analysis \
  --metrics outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json \
  --predictions outputs/plantvillage/week4_explainability/predictions.json \
  --output outputs/plantvillage/week4_explainability/error_analysis.json \
  --report reports/week4_error_analysis.md \
  --low-f1-count 8 \
  --confusion-pair-count 10 \
  --high-confidence-threshold 0.8 \
  --high-confidence-error-count 20
```

错误分析产物：

- 机器可读结果：`outputs/plantvillage/week4_explainability/error_analysis.json`
- 摘要报告：`reports/week4_error_analysis.md`

人工关注区域与错误类型审阅入口可用以下命令复现。该命令会生成候选提示；当前仓库中的 `attention_review.json` 已完成 24 个固定样本的人工填写。

```bash
uv run plant-attention-review \
  --atlas-manifest outputs/plantvillage/week4_explainability/gradcam_atlas/gradcam_atlas_manifest.json \
  --error-analysis outputs/plantvillage/week4_explainability/error_analysis.json \
  --output outputs/plantvillage/week4_explainability/attention_review.json \
  --report reports/week4_attention_review.md
```

审阅产物：

- 可编辑 JSON：`outputs/plantvillage/week4_explainability/attention_review.json`
- 摘要报告：`reports/week4_attention_review.md`

校准分析可用以下命令复现。当前报告使用 top-label confidence 计算 ECE/MCE/Brier，并生成 reliability diagram；这不是完整多类别概率校准评估。

```bash
uv run plant-calibration-analysis \
  --predictions outputs/plantvillage/week4_explainability/predictions.json \
  --output outputs/plantvillage/week4_explainability/calibration.json \
  --report reports/week4_calibration.md \
  --figure reports/figures/week4_reliability_diagram.png \
  --bins 10
```

校准分析产物：

- 机器可读结果：`outputs/plantvillage/week4_explainability/calibration.json`
- 摘要报告：`reports/week4_calibration.md`
- Reliability diagram：`reports/figures/week4_reliability_diagram.png`

baseline/final 同样本对比、Grad-CAM 复现性验证和阶段报告一致性审计产物：

- Baseline Grad-CAM 图集：`reports/week4_baseline_gradcam_atlas.md`
- 同样本对比报告：`reports/week4_baseline_vs_final_gradcam.md`
- 同样本对比图：`reports/figures/week4_baseline_vs_final_gradcam.png`
- Grad-CAM 复现性报告：`reports/week4_gradcam_reproducibility.md`
- 阶段报告一致性审计：`reports/week4_consistency_audit.md`

Week 1–4 阶段报告汇总了方法、结果、可解释性、错误分析、校准、局限和参考文献；中英文论文现已在 Week 8 扩展并定稿：

- 阶段报告：`reports/week4_stage_report.md`
- 阶段报告一致性审计：`reports/week4_consistency_audit.md`
- LaTeX 中文源文件：`paper/zh/main.tex`
- LaTeX English source：`paper/en/main.tex`
- 最终 PDF：`paper/out/plantdisease_ai_zh.pdf`、`paper/out/plantdisease_ai_en.pdf`
- 双语结构与共享数字审计：`reports/release/week8_paper_audit.json`

## 推理

对 smoke checkpoint 或正式 PlantVillage checkpoint 可使用 `plant-predict`。输入必须是本地图片：

```bash
uv run plant-predict \
  --checkpoint outputs/smoke/week1/checkpoint.pt \
  --image /path/to/image.jpg \
  --top-k 5
```

正式 PlantVillage checkpoint 示例：

```bash
uv run plant-predict \
  --checkpoint outputs/plantvillage/baseline_mobilenet_v2_seed42/checkpoint.pt \
  --image /path/to/image.jpg \
  --top-k 5
```

## Week 5 Demo

Week 5 新增 UI 无关服务层与 Streamlit Demo。服务层统一负责 checkpoint 加载、预处理、Top-5、Grad-CAM、耗时、模型版本、疾病知识卡、低置信提示和安全声明；Streamlit 只负责上传与展示，避免 Demo 与离线评估逻辑漂移。

本地 Demo：

```bash
uv run streamlit run app/streamlit_app.py \
  --server.address 127.0.0.1 \
  --server.port 8505 \
  --server.headless true \
  -- \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --device cpu
```

固定合成样例端到端验证：

```bash
uv run python scripts/demo_e2e.py \
  --checkpoint outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/checkpoint.pt \
  --image app/examples/synthetic_leaf.png \
  --output outputs/plantvillage/week5_demo/local_e2e.json \
  --overlay-output outputs/plantvillage/week5_demo/local_e2e_overlay.png \
  --device cpu \
  --top-k 5
```

已验证本地证据见 [reports/week5_demo_engineering.md](reports/week5_demo_engineering.md)。截图位于 `reports/figures/week5_streamlit_demo.jpg`。固定样例是合成工程 smoke 输入，不代表真实 PlantVillage 准确率。

Apple `container` 入口使用 `Containerfile`，不会把 checkpoint、原始数据、`outputs/`、`.venv/` 或密钥放进镜像上下文。当前已验证 CPU-only Apple `container` build/run、Streamlit healthcheck 和容器内固定样例 Top-5 + Grad-CAM。容器镜像 digest 为 `sha256:28528ad628fc5fa7095aba0a6ef75600ca8fecff4b02b6d6a50ca7ecb783c771`，镜像 variant size 约 `909 MiB`；一次运行时资源采样为 `821.67 MiB / 1.00 GiB`。这些是 Demo 工程验证数据，不是严格性能 benchmark。

当前 `Containerfile` 为 CPU-only Demo，安装依赖时使用 `uv pip install --torch-backend cpu -e .`。如果 build 输出里出现大量 `nvidia-*` 包，说明正在跑旧镜像步骤；请 `Ctrl+C` 停止后，用最新分支重新 build。

如果 `container build` 在 bootstrap BuildKit 时报告 `Rosetta is not installed`，先安装 Rosetta 2：

```bash
/usr/sbin/softwareupdate --install-rosetta --agree-to-license
```

```bash
container system start --enable-kernel-install --timeout 300 && \
container build -f Containerfile -t localhost/plantdisease-ai:week5 . && \
container run --rm -p 8501:8501 \
  -v "$PWD/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42:/models" \
  localhost/plantdisease-ai:week5
```

启动后访问 `http://127.0.0.1:8501`。使用 `&&` 是为了防止 `container system start` 失败后继续运行后续命令；使用 `localhost/plantdisease-ai:week5` 是为了避免本地镜像不存在时误去 Docker Hub 拉取 `library/plantdisease-ai:week5`。若你的本机 help 显示参数差异，请以 `container system start --help`、`container build --help` 和 `container run --help` 为准。

容器内固定样例验证命令：

```bash
container exec <container-id> .venv/bin/python scripts/demo_e2e.py \
  --checkpoint /models/checkpoint.pt \
  --image app/examples/synthetic_leaf.png \
  --output /tmp/week5_container_e2e.json \
  --overlay-output /tmp/week5_container_e2e_overlay.png \
  --device cpu \
  --top-k 5
```

已验证容器内输出复制到 `outputs/plantvillage/week5_demo/container_e2e.json` 和 `outputs/plantvillage/week5_demo/container_e2e_overlay.png`；详见 [reports/week5_demo_engineering.md](reports/week5_demo_engineering.md)。

### Windows / Linux：Docker 兼容路径（未在本机实测）

本次公开发布继续如实记录 `container: not_run`；下列命令是提供给他人的兼容路径，不是本机 Docker 实测声明。

本项目作者使用 Apple `container`，没有在本次交付中安装或实测 Docker。下面路径提供给使用 Docker Engine / Docker Desktop 的 Windows 与 Linux 用户；它复用同一个 CPU-only `Containerfile`，不构成已验证声明。

先在仓库根目录构建镜像：

```bash
docker build -f Containerfile -t plantdisease-ai:week8 .
```

Linux（Bash）挂载 checkpoint 目录并启动：

```bash
docker run --rm -p 8501:8501 \
  --mount type=bind,source="$(pwd)/outputs/plantvillage/week3_ablation/09_combo_candidate_seed42",target=/models,readonly \
  plantdisease-ai:week8
```

Windows（PowerShell）挂载 checkpoint 目录并启动：

```powershell
docker run --rm -p 8501:8501 `
  --mount "type=bind,source=$($PWD.Path)\outputs\plantvillage\week3_ablation\09_combo_candidate_seed42,target=/models,readonly" `
  plantdisease-ai:week8
```

访问 `http://127.0.0.1:8501`。如果 checkpoint 位于其他目录，请替换 `source`；容器内目标路径保持 `/models`。Windows 用户需先在 Docker Desktop 中允许访问该磁盘/目录。

## Week 6 VLM Exploration

Week 6 已启动为探索性扩展，不覆盖 Week 1–5 分类主线。当前完成了本机硬件与小型 VLM 候选调研、VQA schema、24 图/72 问 source-grounded seed 数据构建、实体级 split 泄漏检查、Qwen3-VL zero-shot/choice/few-shot choice smoke baseline、按题型拆解的错误/风险分析、72 条人工审计模板，以及安全边界明确的农业助手原型。证据见 [reports/week6_vlm_selection.md](reports/week6_vlm_selection.md)、[reports/week6_vqa_datacard.md](reports/week6_vqa_datacard.md)、[reports/week6_vlm_experiment.md](reports/week6_vlm_experiment.md)、[reports/week6_vlm_result_analysis.md](reports/week6_vlm_result_analysis.md)、[reports/week6_vlm_prompt_compare.md](reports/week6_vlm_prompt_compare.md)、[reports/week6_vqa_manual_audit_template.md](reports/week6_vqa_manual_audit_template.md) 与 [reports/week6_vlm_assistant.md](reports/week6_vlm_assistant.md)。

当前选择 `Qwen/Qwen3-VL-4B-Instruct` 作为源模型，使用 `mlx-community/Qwen3-VL-4B-Instruct-4bit` 作为 Apple Silicon MLX 运行时。2026-07-13 的真实 smoke 在 5 张测试图/15 个问题上完成：原始 prompt 严格 normalized exact-match 为 0/15；短答案 prompt 为 10/15；`choice` 和 `few_shot_choice` 均为 11/15。两个 choice prompt 将自动风险词标记降到 0，但 condition 题仍只有 1/5。该结果只是小样本冒烟基线，不是完整 VQA 评估；LoRA/QLoRA 尚未完成，不能写成已微调结果。

构建 Week6 seed VQA 数据：

```bash
uv run python scripts/build_vqa_dataset.py \
  --frozen-samples outputs/plantvillage/week4_explainability/frozen_samples.json \
  --output outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --summary outputs/plantvillage/week6_vlm/vqa_seed_summary.json
```

记录一次不下载模型的 Week6 baseline skip 证据：

```bash
uv run python scripts/run_vlm_baseline.py \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_skipped.json \
  --skip-reason "Qwen3-VL model download not run"
```

在 Apple Silicon 上安装 MLX-VLM 并重新运行真实 Qwen3-VL zero-shot smoke：

```bash
uv sync --group vlm
uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json \
  --split test \
  --cache-dir data/huggingface \
  --allow-model-download \
  --max-tokens 32
```

运行短答案 prompt 版本：

```bash
uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json \
  --split test \
  --cache-dir data/huggingface \
  --prompt-style short \
  --allow-model-download \
  --max-tokens 8
```

分析原始 prompt 与短答案 prompt 的错误、混淆和风险标记：

```bash
uv run python scripts/analyze_vlm_results.py \
  --dataset outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --result outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke.json \
  --result outputs/plantvillage/week6_vlm/qwen3_vl_zero_shot_smoke_short.json \
  --output-json outputs/plantvillage/week6_vlm/vlm_result_analysis.json \
  --report reports/week6_vlm_result_analysis.md
```

生成人工 VQA 审计模板。当前模板状态为 `pending_human_review`，不能写成已完成人工审计：

```bash
uv run python scripts/build_vqa_audit_template.py \
  --dataset outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --analysis outputs/plantvillage/week6_vlm/vlm_result_analysis.json \
  --output-json outputs/plantvillage/week6_vlm/vqa_manual_audit_template.json \
  --report reports/week6_vqa_manual_audit_template.md
```

生成农业助手安全原型的固定 demo。它覆盖教育性摘要、高风险农药剂量拒答、低置信拒答和越界拒答；这不是 LoRA 微调结果，也不是专业诊断系统：

```bash
uv run python scripts/demo_vlm_assistant.py \
  --output outputs/plantvillage/week6_vlm/vlm_assistant_demo.json
```

为了定位 condition 题全错是“开放式回答漂移”还是“视觉识别失败”，当前新增并运行了 `choice` 与 `few_shot_choice` 两种 prompt_style。真实结果显示：choice 约束能消除风险词和自由生成漂移，但 condition 仍只有 1/5，说明模型在细粒度病害条件识别上仍弱。

```bash
uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_choice_smoke.json \
  --split test \
  --cache-dir data/huggingface \
  --prompt-style choice \
  --allow-model-download \
  --max-tokens 16

uv run --group vlm python scripts/run_vlm_baseline.py \
  --input outputs/plantvillage/week6_vlm/vqa_seed.jsonl \
  --output outputs/plantvillage/week6_vlm/qwen3_vl_few_shot_choice_smoke.json \
  --split test \
  --cache-dir data/huggingface \
  --prompt-style few_shot_choice \
  --allow-model-download \
  --max-tokens 16
```

## Week 8 本地发布候选

`week8-rc1` 已记录三条互补的历史本地复现通道：仓库外干净环境、冻结 checkpoint 本地证据重算，以及 Apple `container` linux/arm64 构建与 Streamlit health probe。历史干净环境实际通过 **226 tests**、Ruff、`ty`、claim/link audit、synthetic smoke、package build 与 CLI help。刷新后的交付 manifest 不继承未复跑的运行状态；项目未创建 tag，也未发布远程 release。GitHub 分支或 PR 仅发布可审计源码与小型交付物，不代表模型部署。

- 复现报告：[reports/week8_reproducibility.md](reports/week8_reproducibility.md)
- 发布 manifest：[reports/release/week8_rc1_manifest.json](reports/release/week8_rc1_manifest.json)
- claim ledger：[reports/release/week8_claim_evidence.json](reports/release/week8_claim_evidence.json)
- 最终实验报告：[reports/final_experiment_report.md](reports/final_experiment_report.md)
- 模型卡 / 数据卡：[reports/model_card.md](reports/model_card.md) / [reports/data_card.md](reports/data_card.md)
- 中英文论文：[paper/out/plantdisease_ai_zh.pdf](paper/out/plantdisease_ai_zh.pdf) / [paper/out/plantdisease_ai_en.pdf](paper/out/plantdisease_ai_en.pdf)
- 20 页答辩材料：[PowerPoint](docs/presentation/plantdisease_ai_week8_research_defense.pptx) / [Keynote](docs/presentation/plantdisease_ai_week8_research_defense.key) / [QA](reports/week8_presentation_qa.md)
- 简历与导师材料：[docs/resume/week8_resume_evidence.md](docs/resume/week8_resume_evidence.md) / [docs/mentor/week8_mentor_summary.md](docs/mentor/week8_mentor_summary.md)
- 发布检查清单：[docs/release/week8_release_checklist.md](docs/release/week8_release_checklist.md)

正式结果仍受 official split 中 227 个重叠 `leaf_id`、单 seed、受控背景、无外部田间验证等限制；完整未完成项见发布检查清单。

## 项目结构

```text
configs/                  实验配置
src/plantdisease/data/    数据、划分、Transforms、审计与 EDA
src/plantdisease/models/  MobileNetV2 与 checkpoint
src/plantdisease/serving/ Week 5 推理服务、缓存和疾病知识卡
src/plantdisease/vlm/     Week 6 VQA schema、seed 数据构建和后续 VLM 实验
src/plantdisease/training/训练与随机种子
src/plantdisease/evaluation/分类指标
app/                      Streamlit Demo 和固定示例图片
scripts/                  数据、EDA、训练、评估、推理入口
tests/                    单元与端到端 smoke tests
reports/                  数据审计与阶段报告
docs/artifact-index.md    成果证据索引
Containerfile             Apple container CPU Demo 镜像定义
```

## 研究边界

本项目解决整张叶片图像的 image classification：每张图输出一个类别。不提供病斑位置，因此不是 detection；不提供逐像素 mask，因此不是 segmentation。

PlantVillage 背景受控，与真实田间环境存在明显域差异。数据集上的性能不能直接代表真实田间泛化能力。

## 安全声明

项目输出仅供教育和研究使用，不构成农业诊断、农药或植保处置建议。

## License

[MIT](LICENSE)
