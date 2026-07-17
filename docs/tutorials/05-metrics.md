# Metrics：准确率、F1、混淆矩阵怎么看

## 一句话理解

Metrics 是模型考试后的成绩单。它不只告诉你“总共对了多少”，还告诉你“哪些类别容易错、错成了什么”。

对应代码：

```text
src/plantdisease/evaluation/metrics.py
src/plantdisease/inference.py
```

## Accuracy 是什么

Accuracy 是准确率：

```text
accuracy = 预测正确的样本数 / 总样本数
```

如果 100 张图片里预测对了 92 张：

```text
accuracy = 92 / 100 = 0.92
```

它直观，但不总是足够。

如果某个数据集 95% 都是健康叶片，模型全猜健康，也可能有很高 accuracy，但它对病害类别几乎没用。

## Precision 是什么

Precision 关注：

```text
模型预测为某类的样本里，有多少是真的？
```

公式：

```text
precision = TP / (TP + FP)
```

其中：

```text
TP = 真正例，预测是这个类，实际也是这个类
FP = 假正例，预测是这个类，实际不是这个类
```

Precision 高，说明模型不太乱报这个类别。

## Recall 是什么

Recall 关注：

```text
真实属于某类的样本里，有多少被模型找出来了？
```

公式：

```text
recall = TP / (TP + FN)
```

其中：

```text
FN = 假负例，实际是这个类，但模型没预测出来
```

Recall 高，说明模型不太漏掉这个类别。

## F1 是什么

F1 是 Precision 和 Recall 的调和平均：

```text
F1 = 2 * precision * recall / (precision + recall)
```

它要求 precision 和 recall 都不能太差。

如果 precision 很高但 recall 很低，F1 不会高。

如果 recall 很高但 precision 很低，F1 也不会高。

## Macro F1 是什么

Macro F1 是先分别计算每个类别的 F1，再求平均。

如果有 3 类：

```text
F1_A = 0.90
F1_B = 0.70
F1_C = 0.50
```

那么：

```text
macro_f1 = (0.90 + 0.70 + 0.50) / 3 = 0.70
```

Macro F1 对少数类更敏感。农业病害数据里，这通常比只看 accuracy 更有研究意义。

## Confusion Matrix 是什么

混淆矩阵记录模型把每个真实类别预测成了什么。

如果有两个类别：

```text
healthy
synthetic_blight
```

混淆矩阵可能是：

```text
              predicted healthy   predicted blight
true healthy          10                 2
true blight            3                 9
```

它告诉你：

```text
健康叶片有 2 张被错判为病害
病害叶片有 3 张被错判为健康
```

这比单独一个 accuracy 更有信息量。

## Top-k 预测是什么

在 `inference.py` 里有：

```python
predict_topk(...)
```

Top-k 的意思是：输出概率最高的前 k 个类别。

比如 Top-3：

```text
1. apple_scab: 0.62
2. apple_black_rot: 0.21
3. apple_healthy: 0.08
```

在真实应用中，Top-k 可以给人类专家更多参考。但它不能替代专业植保诊断。

## 为什么现在的 smoke 指标不能写进简历

你刚跑出来的 `plant-smoke` 是合成小数据，只用于验证工程流程。

它证明的是：

```text
代码能跑
训练链路通
checkpoint 能保存
推理入口能输出
```

它不能证明：

```text
模型真的能识别真实植物病害
模型在 PlantVillage 上达到某个准确率
模型能泛化到真实田间环境
```

以后可以写进简历的是正式实验结果，比如：

```text
在 PlantVillage 固定测试集上完成 5 个 CNN 模型公平 Benchmark，报告 Accuracy、Macro F1、参数量与推理延迟。
```

但前提是这些数字都来自真实训练和可追溯文件。

## 背后的数学

对每个类别，可以定义：

```text
TP: 预测为该类，真实也是该类
FP: 预测为该类，真实不是该类
FN: 没预测为该类，真实是该类
TN: 没预测为该类，真实也不是该类
```

常用指标：

```text
precision = TP / (TP + FP)
recall = TP / (TP + FN)
F1 = 2PR / (P + R)
accuracy = correct / total
```

混淆矩阵：

```text
C[i][j] = 真实类别 i 被预测成类别 j 的数量
```

## 你现在应该掌握什么

读完这一篇，你只要记住：

```text
Accuracy 看总体对不对。
Precision 看预测某类时准不准。
Recall 看真实某类有没有被找全。
F1 平衡 Precision 和 Recall。
Macro F1 对每个类别一视同仁。
混淆矩阵告诉你错在哪里。
```

## 小练习

打开：

```text
outputs/smoke/week1/metrics.json
```

找到：

```text
accuracy
macro_f1
confusion_matrix
per_class
```

先不要纠结数值高低。你现在要练的是：知道每个字段是什么意思。

