# Dataset：图片和标签如何变成数据集

## 一句话理解

Dataset 就是“很多张图片 + 每张图片对应的答案标签”的统一包装。模型训练时不会直接理解文件夹，它需要一个标准接口：给我第几张图，我就返回这张图和它的标签。

对应代码：

```text
src/plantdisease/data/dataset.py
src/plantdisease/smoke.py
```

## 这个项目里的样本长什么样

在 `dataset.py` 里有一个核心结构：

```python
@dataclass(frozen=True)
class ImageRecord:
    image: Image.Image
    label: int
    sample_id: str
```

它表示一条图片样本。

`image` 是图片本身。

`label` 是数字标签，比如：

```text
0 -> healthy
1 -> synthetic_blight
```

`sample_id` 是样本编号，方便以后追踪是哪一张图。

为什么标签不用文字，而用数字？因为神经网络最后输出的是一组数字分数，训练时也需要用数字类别计算 loss。

## Dataset 的两个核心函数

PyTorch 的 Dataset 最重要的是两个函数：

```python
def __len__(self) -> int:
    return len(self.records)
```

它回答：这个数据集有多少个样本？

```python
def __getitem__(self, index: int):
    record = self.records[index]
    image = record.image.copy()
    if self.transform is not None:
        image = self.transform(image)
    return image, record.label
```

它回答：给我第 `index` 个样本，我返回什么？

返回结果是：

```text
(图片, 标签)
```

训练时 DataLoader 会不断调用 `__getitem__`，把一张张图片组成一个 batch。

## DataLoader 是什么

Dataset 负责“单个样本怎么取”。

DataLoader 负责“怎么一批一批地取”。

在 `smoke.py` 里你会看到：

```python
train_loader = DataLoader(
    Subset(train_dataset, splits["train"]),
    batch_size=config.data.batch_size,
    shuffle=True,
    generator=generator,
    num_workers=0,
)
```

这段代码的意思是：

```text
从训练集里取数据
每次取 batch_size 张图片
训练时打乱顺序
用固定随机种子保证可复现
```

如果 `batch_size=4`，模型一次看到的不是一张图，而是 4 张图。

## 背后的数学

在数学里，一个监督学习数据集可以写成：

```text
D = {(x_1, y_1), (x_2, y_2), ..., (x_n, y_n)}
```

其中：

```text
x_i = 第 i 张图片
y_i = 第 i 张图片的真实类别
n = 样本总数
```

训练模型就是找一个函数：

```text
f_theta(x) -> y
```

这里的 `theta` 是模型参数。它们一开始是随机的，训练时会不断调整。

现实中不会每次都把全部数据喂给模型，而是分成很多 batch：

```text
B = {(x_1, y_1), ..., (x_m, y_m)}
```

`m` 就是 batch size。

## 为什么要划分 train / validation / test

一个科研项目不能只看模型在训练图片上的表现，因为模型可能只是背下来了。

所以要划分：

```text
train：给模型学习
validation：调参数、选模型
test：最后一次公平考试
```

这个项目里 Week 1 已经实现了可复现的分层划分。分层的意思是：每个类别在 train、validation、test 里尽量都有相似比例，避免某个集合里某类样本太少。

## 你现在应该掌握什么

读完这一篇，你只要记住：

```text
图片项目的第一步不是模型，而是数据。
Dataset 负责把图片和标签包装成标准格式。
DataLoader 负责把样本组成 batch。
科研项目必须保存划分方式，否则别人无法复现实验。
```

## 小练习

打开：

```text
src/plantdisease/smoke.py
```

找到：

```python
class_names = ["healthy", "synthetic_blight"]
```

你可以先不改代码，只在心里回答：

```text
如果以后用真实 PlantVillage 数据，这里会变成几个类别？
为什么不能手写一个随便的类别顺序？
```

答案是：真实类别顺序必须来自数据集或固定标签映射，否则训练、评估、推理可能对不上。

