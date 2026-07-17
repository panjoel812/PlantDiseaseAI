# Week 4 Grad-CAM Atlas

生成时间：2026-07-13

## 配置

- Atlas manifest：`outputs/plantvillage/week4_explainability/gradcam_atlas/gradcam_atlas_manifest.json`
- 输出目录：`outputs/plantvillage/week4_explainability/gradcam_atlas`
- 目标层：`layer4.2`
- Target mode：`predicted`
- 样本数量：`24`

## 目标层选择说明

ResNet 系列使用最后一个 residual block 的输出作为 Grad-CAM 目标模块，而不是 block 内部最后一个卷积层。这样 hook 捕获的是残差合并后的最终空间特征，更接近分类头实际使用的表示；热力图仍只能解释相关性，若关注背景则应记录为潜在背景偏差证据。

## 样本图集

| 分组 | test_index | target | panel |
| --- | --- | --- | --- |
| `correct_high_confidence` | `9750` | `Tomato___Leaf_Mold` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/01_test-9750_target-31_Tomato___Leaf_Mold.png` |
| `correct_high_confidence` | `1175` | `Corn_(maize)___Northern_Leaf_Blight` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/02_test-1175_target-9_Corn__maize____Northern_Leaf_Blight.png` |
| `correct_high_confidence` | `9749` | `Tomato___Leaf_Mold` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/03_test-9749_target-31_Tomato___Leaf_Mold.png` |
| `correct_high_confidence` | `9748` | `Tomato___Leaf_Mold` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/04_test-9748_target-31_Tomato___Leaf_Mold.png` |
| `correct_high_confidence` | `9852` | `Tomato___Leaf_Mold` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/05_test-9852_target-31_Tomato___Leaf_Mold.png` |
| `correct_high_confidence` | `7821` | `Squash___Powdery_mildew` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_high_confidence/06_test-7821_target-25_Squash___Powdery_mildew.png` |
| `correct_low_confidence` | `6611` | `Tomato___Septoria_leaf_spot` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/07_test-6611_target-32_Tomato___Septoria_leaf_spot.png` |
| `correct_low_confidence` | `9443` | `Apple___Black_rot` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/08_test-9443_target-1_Apple___Black_rot.png` |
| `correct_low_confidence` | `5269` | `Tomato___Target_Spot` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/09_test-5269_target-34_Tomato___Target_Spot.png` |
| `correct_low_confidence` | `691` | `Tomato___Early_blight` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/10_test-691_target-29_Tomato___Early_blight.png` |
| `correct_low_confidence` | `953` | `Apple___healthy` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/11_test-953_target-3_Apple___healthy.png` |
| `correct_low_confidence` | `6272` | `Apple___Apple_scab` | `outputs/plantvillage/week4_explainability/gradcam_atlas/correct_low_confidence/12_test-6272_target-0_Apple___Apple_scab.png` |
| `error_high_confidence` | `198` | `Tomato___Late_blight` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/13_test-198_target-30_Tomato___Late_blight.png` |
| `error_high_confidence` | `6270` | `Apple___healthy` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/14_test-6270_target-3_Apple___healthy.png` |
| `error_high_confidence` | `5109` | `Tomato___Spider_mites Two-spotted_spider_mite` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/15_test-5109_target-33_Tomato___Spider_mites_Two-spotted_spider_mite.png` |
| `error_high_confidence` | `1099` | `Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/16_test-1099_target-7_Corn__maize____Cercospora_leaf_spot_Gray_leaf_spot.png` |
| `error_high_confidence` | `530` | `Tomato___Target_Spot` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/17_test-530_target-34_Tomato___Target_Spot.png` |
| `error_high_confidence` | `166` | `Tomato___Late_blight` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_high_confidence/18_test-166_target-30_Tomato___Late_blight.png` |
| `error_low_confidence` | `3453` | `Corn_(maize)___Northern_Leaf_Blight` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/19_test-3453_target-9_Corn__maize____Northern_Leaf_Blight.png` |
| `error_low_confidence` | `9448` | `Blueberry___healthy` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/20_test-9448_target-4_Blueberry___healthy.png` |
| `error_low_confidence` | `957` | `Blueberry___healthy` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/21_test-957_target-4_Blueberry___healthy.png` |
| `error_low_confidence` | `6186` | `Tomato___Target_Spot` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/22_test-6186_target-34_Tomato___Target_Spot.png` |
| `error_low_confidence` | `8965` | `Corn_(maize)___Common_rust_` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/23_test-8965_target-8_Corn__maize____Common_rust.png` |
| `error_low_confidence` | `6690` | `Tomato___Early_blight` | `outputs/plantvillage/week4_explainability/gradcam_atlas/error_low_confidence/24_test-6690_target-29_Tomato___Early_blight.png` |

## 解释边界

Grad-CAM 图只能作为目标类别分数与输入区域的相关性可视化，不能表述为因果解释，也不能代表真实田间泛化能力。
