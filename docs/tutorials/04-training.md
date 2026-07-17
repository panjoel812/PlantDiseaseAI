# Train：模型是怎么学会分类的

## 一句话理解

训练就是让模型先预测，再看自己错了多少，然后根据错误调整参数。

对应代码：

```text
src/plantdisease/training/engine.py
src/plantdisease/smoke.py
```

## 训练循环在做什么

`engine.py` 里的核心函数是：

```python
train_one_epoch(...)
```

一轮 epoch 的训练大概是：

```text
1. 从 DataLoader 拿一个 batch
2. 把图片送进模型
3. 模型输出 logits
4. 用真实标签计算 loss
5. 反向传播计算梯度
6. 优化器更新模型参数
7. 重复直到训练集跑完一遍
```

代码里最关键的是：

```python
loss = criterion(model(images), labels)
loss.backward()
optimizer.step()
```

这三行就是深度学习训练的核心。

## loss 是什么

loss 可以理解成“模型错得有多严重”。

分类任务常用 Cross Entropy Loss。它会惩罚模型把真实类别的概率预测得太低。

如果真实类别是 `healthy`，模型给出的概率是：

```text
healthy: 0.90
synthetic_blight: 0.10
```

loss 会比较小。

如果模型给出：

```text
healthy: 0.05
synthetic_blight: 0.95
```

loss 会很大。

## Cross Entropy 的数学

模型先输出 logits：

```text
z = [z_1, z_2, ..., z_C]
```

用 softmax 转成概率：

```text
p_i = exp(z_i) / sum_j exp(z_j)
```

如果真实类别是 `y`，交叉熵 loss 是：

```text
L = -log(p_y)
```

意思是：真实类别的预测概率越高，loss 越小。

例如：

```text
p_y = 0.9
L = -log(0.9) ≈ 0.105
```

```text
p_y = 0.01
L = -log(0.01) ≈ 4.605
```

所以模型会被鼓励把真实类别概率变大。

## backward 是什么

`loss.backward()` 的作用是计算梯度。

梯度可以理解成：

```text
每个参数应该往哪个方向改，loss 才会下降？
```

数学上是求导：

```text
dL / dtheta
```

其中：

```text
L = loss
theta = 模型参数
```

## optimizer.step 是什么

优化器根据梯度更新参数。

最简单的梯度下降可以写成：

```text
theta_new = theta_old - learning_rate * gradient
```

其中：

```text
learning_rate = 学习率
gradient = 梯度
```

学习率太小，模型学得很慢。

学习率太大，模型可能震荡甚至训练失败。

## 为什么要有 evaluate

训练集 loss 下降不代表模型真的会泛化。

所以 `engine.py` 里还有：

```python
evaluate(...)
```

评估时会：

```text
关闭训练模式
不计算梯度
只做预测
统计指标
```

代码里：

```python
model.eval()
with torch.inference_mode():
```

意思是告诉 PyTorch：现在不是训练，只是推理和评估。

## 单 batch 过拟合测试是什么

在 `smoke.py` 里有：

```python
overfit_single_batch(...)
```

它的意思是：只拿很小的一批数据，让模型反复学习，看 loss 能不能明显下降。

这不是正式实验，而是工程检查。

如果模型连一个小 batch 都学不会，说明代码链路可能有问题，比如：

```text
标签错了
loss 用错了
模型输出维度错了
optimizer 没有更新参数
数据预处理坏了
```

所以单 batch 过拟合是非常有用的调试方法。

## checkpoint 是什么

训练完模型后，要保存参数：

```text
outputs/smoke/week1/checkpoint.pt
```

checkpoint 就是模型存档。以后不需要重新训练，可以直接加载它做预测。

科研项目里 checkpoint 很重要，因为它是实验证据的一部分。

## 你现在应该掌握什么

读完这一篇，你只要记住：

```text
训练 = 预测 -> 算错多少 -> 求梯度 -> 更新参数。
Cross Entropy 惩罚真实类别概率太低。
学习率控制每次更新参数的步子有多大。
evaluate 只评估，不训练。
checkpoint 是模型训练后的存档。
```

## 小练习

打开：

```text
outputs/smoke/week1/single_batch_overfit.json
```

看里面的：

```text
initial_loss
final_loss
losses
```

如果 `final_loss` 明显小于 `initial_loss`，说明模型确实从这一小批数据里学到了东西。

