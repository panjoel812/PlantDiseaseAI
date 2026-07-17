# PlantDiseaseAI Eight-Week Roadmap Documents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一份可直接执行的八周中文研发任务清单，以及一份能指导 AI 自主完成 PlantDiseaseAI 项目的仓库级代理规范。

**Architecture:** 根目录 `TASKS.md` 负责定义“做什么、何时完成、如何验收”，根目录 `AGENTS.md` 负责定义“代理如何工作、如何验证、何时暂停”。两个文件共享相同的八周阶段、证据标准和完成定义，并由最后的静态检查确认相互一致。

**Tech Stack:** Markdown、CommonMark 复选框、POSIX shell 静态检查命令

## Global Constraints

- 文档主体使用中文，模型、框架和指标名称保留常用英文。
- 覆盖完整八周，但本次不实现训练代码、下载数据、安装依赖或运行实验。
- 任何准确率、F1、FPS、参数量、提升幅度和简历数字都必须来自真实实验，不得预填或虚构。
- 图像分类主线优先于 VLM；Week 6 的探索不得阻塞前五周核心成果。
- 每周必须包含目标、任务、交付物、验收标准、证据要求和退出条件。
- 代理在安全且范围明确的技术决策上自主推进；涉及付费、凭据、外部发布、重要删除或研究主问题变更时请求用户确认。
- 当前目录不是 Git 仓库，因此本计划不执行提交；项目初始化 Git 后再按阶段提交。

---

### Task 1: 创建完整八周中文研发任务清单

**Files:**

- Create: `TASKS.md`
- Reference: `docs/superpowers/specs/2026-07-10-eight-week-roadmap-design.md`

**Interfaces:**

- Consumes: 已确认的八周设计规范和用户提供的 PlantVillage 项目路线。

- Produces: 根目录 `TASKS.md`，其周标题和完成定义供 Task 2 的代理规则引用。

- [ ] **Step 1: 写入项目目标、使用方法和全局完成标准**
  
  文件开头明确：项目定位为可复现科研型作品集；复选框只有在证据存在时才可勾选；实测指标不得用附件示例值代替。全局完成标准覆盖可运行代码、固定数据划分、配置化实验、机器可读指标、图表、报告、演示和简历证据。

- [ ] **Step 2: 写入 Week 1–Week 4 任务**
  
  Week 1 必须覆盖仓库与环境、PlantVillage 数据审计、EDA、DataLoader 冒烟测试、MobileNetV2 基线和基础指标；Week 2 必须覆盖五个模型的公平 Benchmark；Week 3 必须覆盖增强、损失、调度器、EMA 和单变量消融；Week 4 必须覆盖 Grad-CAM、混淆类别、失败案例和阶段报告。每周均使用“目标、任务、交付物、验收、证据、退出条件”六段结构。

- [ ] **Step 3: 写入 Week 5–Week 8 任务**
  
  Week 5 必须覆盖 Streamlit、Top-5、置信度、热力图、疾病说明、免责声明、Docker 和 README；Week 6 必须覆盖小型 VLM 选型、VQA 数据、LoRA 或资源受限替代方案及农业助手；Week 7 必须覆盖 GitHub 展示、架构图、GIF/视频、博客和 PPT；Week 8 必须覆盖复现审计、最终报告、简历条目、发布检查和局限性陈述。

- [ ] **Step 4: 写入最终交付物与简历证据模板**
  
  最终交付物逐项列出代码仓库、模型实验、报告、Demo、Docker、博客、PPT、VLM 原型和成果索引。简历模板只允许使用方括号字段，例如 `[最佳模型]`、`[Macro-F1]`、`[测试硬件]`，并明确只有真实结果产生后才能替换。

- [ ] **Step 5: 检查八周结构完整性**
  
  Run:
  
  ```bash
  for week in 1 2 3 4 5 6 7 8; do rg -q "Week ${week}" TASKS.md || exit 1; done
  ```
  
  Expected: 命令退出码为 0，没有输出。

- [ ] **Step 6: 检查每周验收与证据字段数量**
  
  Run:
  
  ```bash
  test "$(rg -c '^#### 验收标准' TASKS.md)" -eq 8
  test "$(rg -c '^#### 科研与简历证据' TASKS.md)" -eq 8
  test "$(rg -c '^#### 退出条件' TASKS.md)" -eq 8
  ```
  
  Expected: 三条命令均退出码为 0。

### Task 2: 创建自主研发工程师代理规范

**Files:**

- Create: `AGENTS.md`
- Read: `TASKS.md`
- Reference: `docs/superpowers/specs/2026-07-10-eight-week-roadmap-design.md`

**Interfaces:**

- Consumes: `TASKS.md` 的周阶段、证据要求和完成定义。

- Produces: 仓库内所有后续代理自动遵守的项目级执行规范。

- [ ] **Step 1: 定义角色、使命和优先级**
  
  将代理定义为自主研发工程师，优先级固定为：正确性与可复现性、科研证据、稳定接口、测试与文档、展示质量、VLM 扩展。要求主动选择当前最高优先级的未完成任务，而不是等待逐条指令。

- [ ] **Step 2: 定义自主边界和暂停条件**
  
  允许代理自主进行安全、可逆、范围明确的技术选择。需要付费或凭据、外部发布、删除重要成果、改变研究主问题，或算力限制导致研究结论发生实质变化时，必须暂停并请求用户决定。

- [ ] **Step 3: 定义标准工作循环和完成定义**
  
  工作循环固定为：读取现状、选择任务、检查依赖、实现、验证、保存证据、更新文档与复选框。明确“代码存在”不等于完成；只有适当测试通过、产物可定位、指标可追溯时才能勾选。完整训练不可运行时只允许标记冒烟测试结果，不得宣称完整实验成功。

- [ ] **Step 4: 定义推荐目录和工程规则**
  
  规定配置、源代码、测试、脚本、Notebook、应用、报告和输出的职责边界。要求共用标签映射和预处理；避免数据泄漏；固定随机种子；配置驱动实验；添加关键测试；环境依赖可复现；数据、权重、密钥、缓存不进 Git。

- [ ] **Step 5: 定义科研、指标和安全规则**
  
  要求统一划分和协议进行 Benchmark，记录代码版本、配置、随机种子、硬件、时间和产物路径；同时报告 Accuracy、Macro Precision/Recall/F1、混淆矩阵和分类别指标；FPS 必须注明硬件、batch size、精度、预热和统计方法；记录失败实验与局限性；农业建议附教育用途声明。

- [ ] **Step 6: 定义文档同步和简历诚信规则**
  
  每完成任务必须更新 `TASKS.md`，每完成阶段同步 README、实验表和成果索引。简历内容只能引用已核验结果，必须保留证据路径；禁止伪造指标、提升幅度、引用、奖项、部署状态和模型能力。

- [ ] **Step 7: 检查关键规则存在**
  
  Run:
  
  ```bash
  rg -q '自主研发工程师' AGENTS.md
  rg -q '不得.*虚构|禁止.*虚构' AGENTS.md
  rg -q 'TASKS\.md' AGENTS.md
  rg -q '数据泄漏' AGENTS.md
  rg -q '随机种子' AGENTS.md
  rg -q '付费|凭据' AGENTS.md
  ```
  
  Expected: 六条命令均退出码为 0。

### Task 3: 交叉验证文档质量和一致性

**Files:**

- Verify: `TASKS.md`
- Verify: `AGENTS.md`
- Verify: `docs/superpowers/specs/2026-07-10-eight-week-roadmap-design.md`

**Interfaces:**

- Consumes: Task 1 和 Task 2 的最终文档。

- Produces: 可交付的、无占位承诺且相互一致的任务与代理规范。

- [ ] **Step 1: 检查文件与标题**
  
  Run:
  
  ```bash
  test -s TASKS.md
  test -s AGENTS.md
  rg -q '^# PlantDiseaseAI 八周研发任务' TASKS.md
  rg -q '^# PlantDiseaseAI 代理执行规范' AGENTS.md
  ```
  
  Expected: 四条命令均退出码为 0。

- [ ] **Step 2: 扫描虚构示例指标和模糊占位符**
  
  Run:
  
  ```bash
  ! rg -n '98\.1|98\.6|98\.8|99\.0|TBD|TODO|待补充|随便|适当处理' TASKS.md AGENTS.md
  ```
  
  Expected: 命令退出码为 0，没有匹配输出。方括号形式的简历字段是有意保留的填写模板，不属于模糊占位符。

- [ ] **Step 3: 人工复核阶段一致性**
  
  对照设计规范检查以下顺序在两个文件中一致：分类基线 → Benchmark → 模型改进与消融 → 可解释性与错误分析 → Demo 与 Docker → VLM → 展示材料 → 复现审计与简历。确认 `AGENTS.md` 没有允许代理越过 Week 1–5 核心门槛直接把 VLM 标记为核心成果。

- [ ] **Step 4: 人工复核措辞真实性**
  
  检查所有成果陈述均为任务要求或模板，而不是已经完成的事实；检查 PlantVillage 高性能没有被描述为真实田间泛化；检查农业防治建议没有被表述为专业诊断。

- [ ] **Step 5: 输出最终文件清单**
  
  Run:
  
  ```bash
  wc -l TASKS.md AGENTS.md docs/superpowers/specs/2026-07-10-eight-week-roadmap-design.md
  ```
  
  Expected: 三个文件均显示非零行数，并输出总行数。
