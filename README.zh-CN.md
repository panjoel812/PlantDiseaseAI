[English](README.md) | [简体中文](README.zh-CN.md)

# PlantDiseaseAI 中文入口

PlantDiseaseAI 是一个强调证据链与能力边界的植物叶片病害分类研究项目。
正式候选的 0.9953 Accuracy / 0.9941 Macro F1 是 official split、single
seed 42 的单次结果；train/test 存在 227 个重叠 `leaf_id`，不能当作田间泛化或
专业诊断证据。

## 从哪里开始

- [完整英文运行指南](README.md)：安装、数据、训练、评估、React、Streamlit、
  Linux/Windows Docker 与故障排查。
- [新生代码教程](docs/tutorials/README.md)：Dataset、Transform、Model、Train、
  Metrics 与数学基础。
- [中文论文](paper/out/plantdisease_ai_zh.pdf)
- [双语答辩大纲](docs/presentation/plantdisease_ai_complete_bilingual_outline.md)
- [成果证据索引](docs/artifact-index.md)

## 三条体验路径

1. 合成 smoke：不需要 PlantVillage 或 checkpoint，只验证代码链路。
2. React/Streamlit Demo：需要本地兼容 checkpoint；仓库不提供自动下载。
3. 完整研究复现：需要约 2 GB PlantVillage 数据，并按配置训练与审计。

## 平台说明

| 能力 | macOS Apple Silicon | Linux | Windows 11 + WSL2/Docker Desktop |
| --- | --- | --- | --- |
| Python smoke/训练/评估 | 支持 | 支持；CPU/CUDA 取决于本地 PyTorch | 通过 WSL2；原生 PowerShell 不是已审计 Python 路径 |
| React/FastAPI 分类界面 | 支持 | 使用兼容 checkpoint | 通过 WSL2 |
| Streamlit 容器 | Apple `container` 或 Docker | Docker Engine | Docker Desktop WSL2 backend |
| Qwen MLX 面板 | 可选，仅本地权重 | 当前不支持 | 当前不支持 |

上表中的“支持”仅表示项目预期接口，不表示每个平台都完成了运行审计。只有
[Week 8 复现报告](reports/week8_reproducibility.md)中记录的具体环境才是已完成的
审计证据；Linux/Windows 行不能解读为已完成跨平台验证。

分类主线可在 macOS、Linux 以及 Windows 11 的 WSL2 环境运行；Windows 容器
使用 Docker Desktop WSL2 backend。可选 Qwen 面板当前依赖 Apple Silicon
上的 MLX 与已存在的本地权重，Linux/Windows 不支持；浏览器与 API 不会自动下载
Qwen 权重。仓库也不会自动下载或提供最终分类 checkpoint。

Docker Engine/Desktop 未在本次发布环境中运行；本地使用 Apple `container`，
发布证据继续记录 `container: not_run`。Windows PowerShell 仅经过静态检查。
具体豁免和发布边界见[发布决策记录](docs/release/publication_decisions.md)。

## 安全边界

项目输出仅供教育和研究使用，不构成专业植物诊断、农药、剂量或处置建议。
Grad-CAM 是相关性可视化，不是因果解释。田间样例没有已验证真值，页面结果只是
模型 prediction。

## 许可

项目代码适用 [MIT License](LICENSE)，另有说明的资源除外。用户提供的田间图片及其
在截图、演示文稿中的直接可见复制或裁剪不属于 MIT 许可范围，也未授予复用许可；
详见[资源许可说明](ASSET_LICENSES.md)。
