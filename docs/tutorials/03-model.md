# Model：MobileNetV2 到底是什么

## 一句话理解

模型就是一个带参数的函数。输入图片，输出每个类别的分数。

对应代码：

```text
src/plantdisease/models/factory.py
```

## 模型输入和输出

对于图像分类，模型做的是：

```text
输入：一张图片
输出：每个类别的分数
```

如果有两个类别：

```text
healthy
synthetic_blight
```

模型可能输出：

```text
[2.1, -0.4]
```

这还不是概率，只是分数，通常叫 logits。

分数越高，模型越倾向于这个类别。

## MobileNetV2 是什么

MobileNetV2 是一种轻量级卷积神经网络，常用于图像分类。它的特点是参数量和计算量比较小，适合之后做部署实验，比如做网页 Demo 或移动端推理。

在这个项目里，Week 1 先使用 MobileNetV2 作为基线模型。基线的意思是：

```text
先做一个朴素、标准、可复现的版本。
后面所有改进都要和它比较。
```

没有基线，就不知道改进到底有没有用。

## 工厂函数是什么

代码里有：

```python
def create_model(name: str, num_classes: int, pretrained: bool = False) -> nn.Module:
```

你可以把它理解成“模型制造机”。

输入：

```text
模型名字
类别数量
是否使用预训练权重
```

输出：

```text
一个 PyTorch 模型
```

现在它只支持：

```python
mobilenet_v2
```

后面 Week 2 做 Benchmark 时，会加入 ResNet、EfficientNet 等模型。到时候统一从这个工厂函数创建模型，实验会更整洁。

## 为什么要替换最后一层

原始 MobileNetV2 通常是在 ImageNet 上训练的，ImageNet 有 1000 类。

但是我们的植物病害分类不是 1000 类。比如 smoke test 只有 2 类。

所以代码里会替换最后一层：

```python
model.classifier[1] = nn.Linear(model.last_channel, num_classes)
```

意思是：把模型最后输出的类别数量改成当前项目需要的数量。

## 背后的数学

神经网络可以写成：

```text
f_theta(x) = logits
```

其中：

```text
x = 图片张量
theta = 模型参数
logits = 每个类别的原始分数
```

最后一层通常是线性层：

```text
z = W h + b
```

其中：

```text
h = 前面网络提取出的图像特征
W = 权重矩阵
b = 偏置
z = logits
```

如果有 2 个类别，`z` 就有 2 个数字。

如果有 38 个类别，`z` 就有 38 个数字。

## logits 如何变成概率

预测时会用 softmax：

```text
p_i = exp(z_i) / sum_j exp(z_j)
```

它会把 logits 转成概率，所有类别概率加起来等于 1。

比如：

```text
logits = [2.1, -0.4]
softmax(logits) = [0.924, 0.076]
```

这表示模型认为第一个类别概率更高。

## 预训练是什么意思

`pretrained=True` 表示模型先在一个大数据集上学过通用图像特征，再拿来做植物病害分类。

这通常会比从零训练更好，尤其当你的数据不够大时。

当前 smoke test 使用：

```text
pretrained=False
```

因为 smoke test 的目标不是追求准确率，而是验证工程链路。

正式 PlantVillage baseline 时，应该使用预训练权重，并明确记录权重来源。

## 你现在应该掌握什么

读完这一篇，你只要记住：

```text
模型是函数：图片 -> 类别分数。
MobileNetV2 是轻量级图像分类模型。
最后一层要改成项目类别数。
logits 不是概率，softmax 后才是概率。
基线模型是后续科研改进的参照物。
```

## 小练习

打开：

```text
src/plantdisease/models/factory.py
```

找到：

```python
if name != "mobilenet_v2":
    raise ValueError(...)
```

思考：

```text
为什么现在不允许随便传一个模型名？
```

答案是：科研项目需要可控。如果模型名随便传，实验配置可能看起来成功，实际却不可复现或不可比较。

