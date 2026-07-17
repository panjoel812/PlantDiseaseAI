# 数学总览：这背后的最小数学地图

## 一句话理解

这个项目背后的数学主线是：把图片变成数字，用一个带参数的函数做预测，用 loss 衡量错误，再用梯度下降不断改参数。

你现在不需要把所有数学都学完。你只需要先知道每块数学在项目里扮演什么角色。

## 1. 图片是张量

一张 RGB 图片可以看成三维数组：

```text
x ∈ R^(C x H x W)
```

其中：

```text
C = 通道数，RGB 图片是 3
H = 高度
W = 宽度
```

如果图片是 32x32：

```text
x ∈ R^(3 x 32 x 32)
```

一个 batch 的图片是四维张量：

```text
X ∈ R^(B x C x H x W)
```

其中 `B` 是 batch size。

## 2. 标签是整数

分类任务里，每张图有一个标签：

```text
y ∈ {0, 1, ..., C-1}
```

如果有两个类别：

```text
0 = healthy
1 = synthetic_blight
```

真实数据里可能有更多类别。

## 3. 模型是函数

模型可以写成：

```text
f_theta(x) = z
```

其中：

```text
theta = 模型参数
x = 图片
z = logits
```

logits 是每个类别的原始分数。

如果有 2 类：

```text
z ∈ R^2
```

如果有 38 类：

```text
z ∈ R^38
```

## 4. Softmax 把分数变成概率

softmax 公式：

```text
p_i = exp(z_i) / sum_j exp(z_j)
```

它有两个作用：

```text
每个 p_i 都大于 0
所有 p_i 加起来等于 1
```

所以可以把它理解为每个类别的预测概率。

## 5. Cross Entropy 衡量错误

如果真实类别是 `y`，交叉熵是：

```text
L = -log(p_y)
```

真实类别概率越高，loss 越小。

真实类别概率越低，loss 越大。

这就是模型学习的压力来源。

## 6. 梯度告诉参数怎么改

训练的目标是让平均 loss 尽量小：

```text
min_theta 1/n * sum_i L(f_theta(x_i), y_i)
```

这句话的意思是：

```text
找到一组模型参数 theta
让所有训练样本上的平均错误最小
```

梯度是：

```text
∂L / ∂theta
```

它告诉我们：如果想让 loss 下降，每个参数应该往哪个方向改。

## 7. 梯度下降更新参数

最简单的更新公式：

```text
theta <- theta - lr * gradient
```

其中：

```text
lr = learning rate，学习率
```

学习率像步长。

步长太小，走得慢。

步长太大，可能越过最低点。

## 8. 训练集、验证集、测试集

数据必须拆开：

```text
train：用来学习参数
validation：用来调方法、选模型
test：最后报告结果
```

如果测试集参与了调参，就像考试前偷看答案，结果不可信。

农业 AI 项目尤其要注意数据泄漏。比如同一片叶子的近似重复图片如果同时出现在训练集和测试集，模型可能不是学会病害，而是记住了那片叶子。

## 9. 指标是实验语言

训练时优化的是 loss。

报告时常用的是：

```text
Accuracy
Macro Precision
Macro Recall
Macro F1
Confusion Matrix
```

loss 用来训练，metrics 用来解释实验结果。

这两个不是一回事。

## 10. 你需要补的数学路线

如果你是大一新生，建议按这个顺序学：

```text
高中函数与导数
线性代数：向量、矩阵、矩阵乘法
概率：条件概率、分布、期望
微积分：偏导数、链式法则
优化：梯度下降
机器学习：训练集、测试集、过拟合、泛化
深度学习：神经网络、卷积、反向传播
```

不要一上来死磕反向传播推导。先知道它在工程里对应：

```python
loss.backward()
optimizer.step()
```

再慢慢补数学。

## 这个项目里的数学和代码对应表

| 数学概念 | 代码位置 | 工程含义 |
| --- | --- | --- |
| 数据集 D | `data/dataset.py` | 图片和标签的集合 |
| 变换 T(x) | `data/transforms.py` | 图片预处理和增强 |
| 模型 f_theta | `models/factory.py` | MobileNetV2 |
| logits z | `training/engine.py` | 模型输出的类别分数 |
| Cross Entropy | `training/engine.py` | 分类 loss |
| 梯度 | `loss.backward()` | 参数更新方向 |
| 优化器 | `optimizer.step()` | 修改模型参数 |
| 指标 | `evaluation/metrics.py` | 实验成绩单 |
| Top-k | `inference.py` | 概率最高的若干类别 |

## 最重要的一句话

深度学习不是魔法。它就是：

```text
数字输入 -> 函数计算 -> 错误度量 -> 求导 -> 调参数 -> 重复很多次
```

你现在已经把这条链路跑通了。接下来要做的，就是一点一点把每个环节看懂、改动、验证、记录。

