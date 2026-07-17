# PlantDiseaseAI 新生教程目录

这组文章是给“刚进入大一、会慢慢学 Python 和 AI”的你准备的。目标不是把所有术语一次塞完，而是让你能把这个项目从命令、代码、数学和科研证据四个角度连起来。

你已经跑通了三件事：

```bash
uv sync --all-groups
uv run pytest -q
uv run plant-smoke --output-dir outputs/smoke/week1 --seed 42 --image-size 32
```

这说明当前工程的最小闭环是通的。接下来要理解它。

## 推荐阅读顺序

1. [Dataset：图片和标签如何变成数据集](01-dataset.md)
2. [Transform：图片为什么要预处理](02-transform.md)
3. [Model：MobileNetV2 到底是什么](03-model.md)
4. [Train：模型是怎么学会分类的](04-training.md)
5. [Metrics：准确率、F1、混淆矩阵怎么看](05-metrics.md)
6. [数学总览：这背后的最小数学地图](06-math-primer.md)

## 读代码的顺序

先不要从所有文件开始。你只需要按下面顺序看：

```text
src/plantdisease/cli.py
src/plantdisease/smoke.py
src/plantdisease/data/dataset.py
src/plantdisease/data/transforms.py
src/plantdisease/models/factory.py
src/plantdisease/training/engine.py
src/plantdisease/evaluation/metrics.py
src/plantdisease/inference.py
```

你可以把它们理解成：

```text
命令入口 -> 完整实验流程 -> 数据 -> 图片预处理 -> 模型 -> 训练 -> 指标 -> 推理
```

## 现在最重要的原则

不要急着追求“我全懂了”。AI 项目的学习顺序应该是：

```text
先跑通
再看输出
再读主流程
再理解关键数学
再改一个小参数
再跑一次对比
```

科研项目不是背概念，而是建立一条能复现、能解释、能留下证据的实验链路。

