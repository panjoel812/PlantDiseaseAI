# PlantDiseaseAI Week 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可安装、可测试的 PlantDiseaseAI 工程，并以合成数据完成数据划分、DataLoader、MobileNetV2、训练、评估、checkpoint 与单图推理的 Week 1 最小闭环。

**Architecture:** 采用 `src/plantdisease` 包结构，将数据、模型、训练、评估和推理分离，通过 YAML 配置与 CLI 组合。正式 PlantVillage 获取和审计使用独立脚本；不依赖外网的测试与合成数据冒烟流程作为本地持续验证基线，真实数据结果只在实际下载与运行后记录。

**Tech Stack:** Python 3.12、uv、PyTorch、torchvision、Hugging Face datasets、scikit-learn、Pillow、matplotlib、PyYAML、pytest、ruff

## Global Constraints

- 目标解释器固定为 Python 3.12；系统 Python 3.9.6 不作为项目运行时。
- 图像分类主线优先；本计划不实现 Week 2 及以后功能。
- 新行为必须遵守 TDD：先写测试并观察正确失败，再写最小实现。
- 真实数据尚未运行前，不得声明 PlantVillage 样本量、指标或基线效果。
- 测试集不得参与训练、早停和模型选择。
- 训练、评估与推理共用标签映射和确定性评估预处理。
- 数据、checkpoint、缓存与本地输出不提交 Git；只提交小型合成证据与机器可读摘要。
- 当前目录无 Git；先初始化 `main`，随后在 `feat/week1-foundation` 分支工作。

---

### Task 1: Git、包结构与依赖环境

**Files:**
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `src/plantdisease/__init__.py`
- Create: empty package markers under `src/plantdisease/{data,models,training,evaluation}`

**Interfaces:**
- Produces: `uv sync --all-groups` 可安装的 Python 3.12 包，CLI 名称预留为 `plant-audit`、`plant-train`、`plant-evaluate`、`plant-predict`、`plant-smoke`。

- [ ] 初始化 Git，创建 `main` 首个文档提交，并切换到 `feat/week1-foundation`。
- [ ] 用 `apply_patch` 创建工程元数据、目录标记、忽略规则、MIT License 和 README 骨架。
- [ ] 运行 `uv sync --all-groups` 生成 `.venv` 与 `uv.lock`；期望 Python 3.12 环境安装成功。
- [ ] 运行 `uv run python -c "import plantdisease; print(plantdisease.__version__)"`；期望输出 `0.1.0`。
- [ ] 提交 `chore: initialize Python project`。

### Task 2: 可复现标签映射与分层划分

**Files:**
- Create: `tests/data/test_splits.py`
- Create: `src/plantdisease/data/splits.py`

**Interfaces:**
- Produces: `stratified_split_indices(labels: Sequence[int], ratios: SplitRatios, seed: int) -> dict[str, list[int]]`
- Produces: `save_split_manifest(path: Path, splits: Mapping[str, Sequence[int]], labels: Sequence[int], class_names: Sequence[str], seed: int) -> None`
- Produces: `load_split_manifest(path: Path) -> SplitManifest`

- [ ] 写测试：相同 seed 得到相同索引；三个集合无重叠且覆盖全部样本；非法 ratio 与稀有类别给出明确错误；manifest 保存加载不漂移。
- [ ] 运行 `uv run pytest tests/data/test_splits.py -q`；期望因模块不存在而失败。
- [ ] 实现冻结 dataclass `SplitRatios`、`SplitManifest` 及分层划分/JSON manifest 函数。
- [ ] 再运行同一测试；期望全部通过。
- [ ] 提交 `feat: add reproducible stratified splits`。

### Task 3: Dataset、Transforms 与数据审计

**Files:**
- Create: `tests/data/test_pipeline.py`
- Create: `tests/data/test_audit.py`
- Create: `src/plantdisease/data/dataset.py`
- Create: `src/plantdisease/data/transforms.py`
- Create: `src/plantdisease/data/audit.py`
- Create: `src/plantdisease/data/huggingface.py`

**Interfaces:**
- Produces: `ImageRecord(image: PIL.Image.Image, label: int, sample_id: str)`
- Produces: `RecordDataset(records: Sequence[ImageRecord], transform: Callable | None) -> torch.utils.data.Dataset`
- Produces: `build_train_transform(image_size: int) -> Callable` and `build_eval_transform(image_size: int) -> Callable`
- Produces: `audit_records(records: Sequence[ImageRecord], class_names: Sequence[str]) -> AuditReport`
- Produces: `load_plantvillage(cache_dir: Path | None = None) -> tuple[list[ImageRecord], list[str]]`

- [ ] 写测试：batch 为 `[N,3,H,W]` float tensor；标签范围正确；eval transform 对同一图片确定；损坏/重复/尺寸/颜色模式审计正确。
- [ ] 运行两个测试文件；期望因模块不存在而失败。
- [ ] 实现 Dataset、训练/评估变换、SHA-256 像素哈希、审计 dataclass 和 HF 适配器；HF 字段检测失败时给出可操作错误。
- [ ] 再运行两个测试文件；期望全部通过。
- [ ] 提交 `feat: add image pipeline and audit`。

### Task 4: 分类指标

**Files:**
- Create: `tests/evaluation/test_metrics.py`
- Create: `src/plantdisease/evaluation/metrics.py`

**Interfaces:**
- Produces: `classification_metrics(y_true: Sequence[int], y_pred: Sequence[int], class_names: Sequence[str]) -> dict[str, object]`
- Produces: `save_metrics(metrics: Mapping[str, object], path: Path) -> None`

- [ ] 写测试：已知 4 样本案例得到正确 Accuracy、Macro Precision/Recall/F1、分类别指标和混淆矩阵；长度不一致与非法标签报错；JSON 可保存。
- [ ] 运行 `uv run pytest tests/evaluation/test_metrics.py -q`；期望因模块不存在而失败。
- [ ] 用 scikit-learn 实现指标，显式 `zero_division=0`，输出 JSON 可序列化原生类型。
- [ ] 再运行同一测试；期望全部通过。
- [ ] 提交 `feat: add classification metrics`。

### Task 5: MobileNetV2、checkpoint 与 Top-5 推理

**Files:**
- Create: `tests/models/test_factory.py`
- Create: `tests/test_inference.py`
- Create: `src/plantdisease/models/factory.py`
- Create: `src/plantdisease/models/checkpoint.py`
- Create: `src/plantdisease/inference.py`

**Interfaces:**
- Produces: `create_model(name: str, num_classes: int, pretrained: bool = False) -> torch.nn.Module`
- Produces: `save_checkpoint(path: Path, model: nn.Module, class_names: Sequence[str], config: Mapping[str, object]) -> None`
- Produces: `load_checkpoint(path: Path, device: torch.device) -> tuple[nn.Module, list[str], dict[str, object]]`
- Produces: `predict_topk(model: nn.Module, image_tensor: Tensor, class_names: Sequence[str], k: int = 5) -> list[Prediction]`

- [ ] 写测试：MobileNetV2 输出类别维度正确；checkpoint round trip 保持 logits；Top-k 降序、概率合法、k 自动截断；未知模型与标签不匹配报错。
- [ ] 运行相关测试；期望因模块不存在而失败。
- [ ] 实现 torchvision MobileNetV2 工厂、版本化 checkpoint schema 和无梯度 Top-k 推理。
- [ ] 再运行相关测试；期望全部通过。
- [ ] 提交 `feat: add MobileNetV2 inference`。

### Task 6: 训练与评估引擎

**Files:**
- Create: `tests/training/test_engine.py`
- Create: `src/plantdisease/training/seed.py`
- Create: `src/plantdisease/training/engine.py`

**Interfaces:**
- Produces: `seed_everything(seed: int, deterministic: bool = True) -> None`
- Produces: `train_one_epoch(model, loader, criterion, optimizer, device) -> EpochResult`
- Produces: `evaluate(model, loader, criterion, device, class_names) -> EvaluationResult`
- Produces: `overfit_single_batch(model, batch, device, steps, learning_rate) -> list[float]`

- [ ] 写测试：seed 重置复现；train 更新参数；evaluate 不更新参数；单 batch Loss 明显下降；空 DataLoader 报错。
- [ ] 运行 `uv run pytest tests/training/test_engine.py -q`；期望因模块不存在而失败。
- [ ] 实现最小训练/评估循环、加权平均 Loss、预测收集和单 batch 过拟合助手。
- [ ] 再运行同一测试；期望全部通过。
- [ ] 提交 `feat: add training and evaluation engine`。

### Task 7: 配置、CLI 与合成数据冒烟闭环

**Files:**
- Create: `tests/test_config.py`
- Create: `tests/test_smoke.py`
- Create: `src/plantdisease/config.py`
- Create: `src/plantdisease/cli.py`
- Create: `src/plantdisease/smoke.py`
- Create: `configs/baseline_mobilenet_v2.yaml`
- Create: `scripts/audit_data.py`
- Create: `scripts/train.py`
- Create: `scripts/evaluate.py`
- Create: `scripts/predict.py`

**Interfaces:**
- Produces: `ExperimentConfig.from_yaml(path: Path) -> ExperimentConfig`
- Produces: `run_smoke(output_dir: Path, seed: int = 42) -> SmokeResult`
- Produces CLI entry points defined in Task 1.

- [ ] 写测试：YAML 配置验证；合成叶片数据闭环生成 config、split、checkpoint、metrics、predictions、curve 和 run manifest；checkpoint 重载预测结构一致。
- [ ] 运行配置与 smoke 测试；期望因模块不存在而失败。
- [ ] 实现严格配置 dataclass、合成 RGB 图像数据集、两类 MobileNetV2 小规模训练闭环和 CLI 薄封装。
- [ ] 再运行相关测试；期望全部通过。
- [ ] 运行 `uv run plant-smoke --output-dir outputs/smoke/week1`；期望生成完整证据并以状态 `smoke_passed` 退出 0。
- [ ] 提交 `feat: add Week 1 smoke pipeline`。

### Task 8: EDA、数据获取说明与 Week 1 研究记录

**Files:**
- Create: `scripts/download_data.py`
- Create: `scripts/eda.py`
- Create: `reports/data_audit.md`
- Create: `reports/week1.md`
- Create: `docs/artifact-index.md`
- Modify: `README.md`
- Modify: `TASKS.md`

**Interfaces:**
- Consumes: Tasks 2–7 的公共接口和真实/合成运行产物。
- Produces: 可执行的 PlantVillage 获取与 EDA 命令、诚实区分真实数据与合成冒烟结果的 Week 1 证据索引。

- [ ] 实现 `plant-audit`/EDA 脚本生成类别分布、尺寸分布、样本图和 JSON 审计摘要；先用合成数据验证。
- [ ] 编写 PlantVillage 下载命令、缓存位置、许可证/来源核验提醒和网络失败处理说明。
- [ ] 完成 README 快速开始、训练/评估/推理命令与项目局限。
- [ ] 写 `reports/week1.md`，解释分类任务边界、真实数据未运行项和合成冒烟证据。
- [ ] 更新 `docs/artifact-index.md` 与 `TASKS.md`；只勾选有实际验证证据的条目。
- [ ] 运行 `uv run pytest -q`、`uv run ruff check .` 和 `uv run plant-smoke --output-dir outputs/smoke/final`。
- [ ] 提交 `docs: record Week 1 evidence`。
