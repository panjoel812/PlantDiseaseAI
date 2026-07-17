# Transform：图片为什么要预处理

## 一句话理解

Transform 是把普通图片变成模型能吃的输入。人看到的是图片，模型看到的是数字矩阵。

对应代码：

```text
src/plantdisease/data/transforms.py
```

## 图片在模型眼里是什么

一张 RGB 图片可以理解成三个二维表：

```text
R 通道：红色强度
G 通道：绿色强度
B 通道：蓝色强度
```

如果图片大小是 32x32，那么模型看到的形状通常是：

```text
3 x 32 x 32
```

这里的 `3` 是 RGB 三个通道。

PyTorch 常用顺序是：

```text
Channel x Height x Width
```

简称 `C x H x W`。

## 训练预处理和评估预处理为什么不同

项目里有两个函数：

```python
build_train_transform(...)
build_eval_transform(...)
```

训练时：

```python
transforms.RandomResizedCrop(...)
transforms.RandomHorizontalFlip()
transforms.RandomRotation(10)
transforms.ColorJitter(...)
```

这些是随机增强。它们会让图片发生轻微变化，比如裁剪、翻转、旋转、颜色变化。

为什么要这样？因为模型如果只见过一模一样的训练图，容易死记硬背。随机增强相当于告诉模型：

```text
叶片稍微转一点、亮一点、暗一点，也应该还是同一类。
```

评估时：

```python
transforms.Resize((image_size, image_size))
```

评估不能使用随机增强。因为评估应该稳定，同一张图每次测试应该得到一致的输入。

## ToTensor 做了什么

普通图片像素一般是 0 到 255 的整数。

`ToTensor()` 会把它变成 0 到 1 之间的小数：

```text
0   -> 0.0
255 -> 1.0
128 -> 0.5019...
```

模型更适合处理这种数值范围。

## Normalize 做了什么

代码里有：

```python
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)
```

然后：

```python
transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
```

它的数学公式是：

```text
z = (x - mean) / std
```

其中：

```text
x = 原始像素值，已经缩放到 0 到 1
mean = 均值
std = 标准差
z = 归一化后的值
```

为什么用 ImageNet 的均值和标准差？因为 MobileNetV2 这类模型通常是在 ImageNet 上预训练的。即使现在 smoke test 里没有使用预训练权重，保留这个标准也方便后面切换到预训练模型。

## 背后的数学

Transform 本质上是一个函数：

```text
T(x) -> x'
```

其中：

```text
x = 原始图片
x' = 模型输入张量
```

训练时使用随机 transform：

```text
x' = T_random(x)
```

同一张图片每次可能略有不同。

评估时使用确定性 transform：

```text
x' = T_eval(x)
```

同一张图片每次都一样。

这对科研很重要。训练可以随机增强，测试必须公平稳定。

## 一个常见误区

很多初学者会觉得：

```text
图片不就是图片吗？为什么要 Normalize？
```

问题在于神经网络是数值计算。不同通道、不同范围的数据如果分布很乱，训练会更难。归一化的作用是让输入数字落在更适合优化的范围。

## 你现在应该掌握什么

读完这一篇，你只要记住：

```text
Transform 把图片变成 Tensor。
训练集可以随机增强，验证集和测试集不能随机。
Normalize 的公式是 z = (x - mean) / std。
输入形状通常是 C x H x W。
```

## 小练习

打开：

```text
src/plantdisease/data/transforms.py
```

找到：

```python
transforms.RandomRotation(10)
```

思考两个问题：

```text
如果旋转角度太大，会不会让叶片图像变得不自然？
如果测试时也随机旋转，会不会导致同一模型每次评估结果不同？
```

这就是为什么数据增强要谨慎，也要只放在训练阶段。

