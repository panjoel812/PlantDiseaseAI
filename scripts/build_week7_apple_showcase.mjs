import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const repoRoot = process.cwd();
const qaDir = process.env.QA_DIR;
if (!qaDir) throw new Error("QA_DIR is required");

const finalPptx = path.join(repoRoot, "docs/presentation/week7_apple_showcase_deck.pptx");
const architectureOutput = path.join(repoRoot, "docs/media/week7_apple_architecture.png");

const COLORS = {
  paper: "#F5F5F7",
  ink: "#050608",
  text: "#1D1D1F",
  muted: "#6E6E73",
  blue: "#0071E3",
  green: "#30D158",
  amber: "#FF9F0A",
  red: "#FF453A",
};

const CLASSIFIER_MAIN_PIPELINE = ["Data\\nAudit", "Train", "Evaluate", "Explain", "Serve"];
const EXPLORATORY_VLM_BRANCH = {"from":"Serve","label":"VLM","status":"Exploratory"};

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

async function writeBlob(filePath, blob) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: style.fontSize ?? 30,
    bold: style.bold ?? false,
    color: style.color ?? COLORS.text,
    alignment: style.alignment ?? "left",
  };
  return shape;
}

function addRect(slide, position, fill, radius = "rounded-2xl", line = "none") {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position,
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function addRule(slide, left, top, width, color = COLORS.blue, height = 5) {
  addRect(slide, { left, top, width, height }, color, null);
}

function addHeader(slide, title, kicker, options = {}) {
  const dark = options.dark ?? false;
  addText(slide, kicker.toUpperCase(), { left: 72, top: 42, width: 650, height: 28 }, {
    fontSize: 18,
    bold: true,
    color: dark ? COLORS.green : COLORS.blue,
  });
  addText(slide, title, { left: 72, top: 80, width: options.width ?? 1136, height: options.height ?? 122 }, {
    fontSize: options.fontSize ?? 64,
    bold: true,
    color: dark ? COLORS.paper : COLORS.ink,
  });
}

function addFooter(slide, evidence, page, dark = false) {
  addRule(slide, 72, 662, 1136, dark ? COLORS.text : COLORS.muted, 1);
  addText(slide, evidence, { left: 72, top: 669, width: 1050, height: 32 }, {
    fontSize: 17,
    color: dark ? COLORS.paper : COLORS.muted,
  });
  addText(slide, String(page).padStart(2, "0"), { left: 1148, top: 669, width: 60, height: 32 }, {
    fontSize: 17,
    bold: true,
    color: dark ? COLORS.paper : COLORS.text,
    alignment: "right",
  });
}

function addMetric(slide, value, label, position, color = COLORS.blue) {
  addText(slide, value, { left: position.left, top: position.top, width: position.width, height: 92 }, {
    fontSize: 80,
    bold: true,
    color,
  });
  addText(slide, label, { left: position.left, top: position.top + 94, width: position.width, height: 62 }, {
    fontSize: 27,
    bold: true,
    color: COLORS.text,
  });
}

async function imageBytes(relativePath) {
  const bytes = await fs.readFile(path.join(repoRoot, relativePath));
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function contentType(relativePath) {
  return /\.jpe?g$/i.test(relativePath) ? "image/jpeg" : "image/png";
}

async function addImage(slide, relativePath, position, options = {}) {
  return slide.images.add({
    blob: await imageBytes(relativePath),
    contentType: contentType(relativePath),
    alt: options.alt ?? path.basename(relativePath),
    fit: options.fit ?? "contain",
    position,
    geometry: options.geometry ?? "roundRect",
    borderRadius: options.borderRadius ?? "rounded-2xl",
    ...(options.crop ? { crop: options.crop } : {}),
  });
}

function addNotes(slide, fiveMinute, tenMinute) {
  slide.speakerNotes.textFrame.setText([
    `5-minute talk track: ${fiveMinute}`,
    `10-minute talk track: ${tenMinute}`,
    "Integrity reminder: cite the evidence path on the slide and do not extend these results to field diagnosis.",
  ]);
  slide.speakerNotes.setVisible(true);
}

// 1 — opening tension
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.ink;
  addText(slide, "RESEARCH DEMO · PLANTVILLAGE", { left: 72, top: 70, width: 550, height: 28 }, {
    fontSize: 18, bold: true, color: COLORS.green,
  });
  addText(slide, "Evidence before\ndiagnosis.", { left: 72, top: 142, width: 600, height: 248 }, {
    fontSize: 70, bold: true, color: COLORS.paper,
  });
  addText(slide, "Reproducible classifier, explainability audit, deployable demo, and an exploratory VLM boundary test.", {
    left: 72, top: 430, width: 585, height: 100,
  }, { fontSize: 26, color: COLORS.paper });
  addText(slide, "Educational closed set · not field diagnosis", { left: 72, top: 570, width: 585, height: 34 }, {
    fontSize: 20, bold: true, color: COLORS.amber,
  });
  await addImage(slide, "docs/media/week7_apple_demo_poster.png", {
    left: 716, top: 78, width: 492, height: 530,
  }, { fit: "cover", geometry: "roundRect", borderRadius: "rounded-3xl" });
  addFooter(slide, "Evidence map: docs/week7_evidence_map.md", 1, true);
  addNotes(slide,
    "Open with the gap between a compelling disease demo and a credible evidence chain. This project is intentionally presented as a research and educational system, not a crop doctor.",
    "Frame the communication job: make every result traceable, keep the controlled-dataset boundary visible, and treat the attractive product moment as the end of an evidence chain rather than the starting point.");
}

// 2 — architecture
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "The model is only one link in the evidence chain.", "Classifier-first system", { fontSize: 62, height: 110 });
  const xs = [76, 305, 534, 763, 992];
  const subs = ["split · EDA", "shared protocol", "metrics · speed", "Grad-CAM", "Top-5 · demo"];
  addText(slide, "VERIFIED CLASSIFIER MAIN LINE", { left: 76, top: 225, width: 520, height: 28 }, {
    fontSize: 18, bold: true, color: COLORS.blue,
  });
  // Connector layer first: arrows are placed before nodes so they remain visually behind them.
  for (let i = 0; i < xs.length - 1; i += 1) {
    addRect(slide, { left: xs[i] + 166, top: 335, width: 55, height: 4 }, COLORS.muted, null);
    slide.shapes.add({ geometry: "triangle", position: { left: xs[i] + 210, top: 324, width: 20, height: 26 }, fill: COLORS.muted, line: { style: "solid", fill: "none", width: 0 }, rotation: 90 });
  }
  slide.shapes.add({
    geometry: "line",
    position: { left: 1075, top: 395, width: 0, height: 62 },
    fill: "none",
    line: { style: "dashed", fill: COLORS.amber, width: 3 },
  });
  slide.shapes.add({ geometry: "triangle", position: { left: 1065, top: 447, width: 20, height: 26 }, fill: COLORS.amber, line: { style: "solid", fill: "none", width: 0 }, rotation: 180 });
  for (let i = 0; i < xs.length; i += 1) {
    const statusColor = i === CLASSIFIER_MAIN_PIPELINE.length - 1 ? COLORS.blue : COLORS.muted;
    const label = CLASSIFIER_MAIN_PIPELINE[i].replace("\\n", "\n");
    const node = addRect(slide, { left: xs[i], top: 276, width: 166, height: 119 }, COLORS.paper, "rounded-2xl", statusColor);
    node.name = `architecture-${label.toLowerCase().replace(/\s/g, "-")}`;
    addText(slide, label, { left: xs[i] + 15, top: 291, width: 136, height: 50 }, {
      fontSize: 22,
      bold: true,
      color: i === CLASSIFIER_MAIN_PIPELINE.length - 1 ? statusColor : COLORS.text,
      alignment: "center",
    });
    addText(slide, subs[i], { left: xs[i] + 12, top: 344, width: 142, height: 44 }, {
      fontSize: 17, color: COLORS.muted, alignment: "center",
    });
  }
  addText(slide, "Shared labels · preprocessing · evidence trail", { left: 76, top: 444, width: 770, height: 42 }, {
    fontSize: 30, bold: true, color: COLORS.blue,
  });
  addText(slide, "The classifier remains complete without the VLM.", { left: 76, top: 501, width: 770, height: 42 }, {
    fontSize: 25, color: COLORS.muted,
  });
  addText(slide, "BOUNDED CONTEXT", { left: 887, top: 423, width: 190, height: 24 }, {
    fontSize: 16, bold: true, color: COLORS.amber, alignment: "center",
  });
  const vlmNode = addRect(slide, { left: 992, top: 473, width: 166, height: 96 }, COLORS.paper, "rounded-2xl", COLORS.amber);
  vlmNode.name = `architecture-${EXPLORATORY_VLM_BRANCH.label.toLowerCase()}-branch`;
  addText(slide, EXPLORATORY_VLM_BRANCH.label, { left: 1007, top: 487, width: 136, height: 34 }, {
    fontSize: 24, bold: true, color: COLORS.amber, alignment: "center",
  });
  addText(slide, EXPLORATORY_VLM_BRANCH.status, { left: 1007, top: 529, width: 136, height: 28 }, {
    fontSize: 18, bold: true, color: COLORS.amber, alignment: "center",
  });
  addText(slide, "Secondary branch—not part of the classifier proof chain.", { left: 76, top: 555, width: 770, height: 38 }, {
    fontSize: 22, color: COLORS.muted,
  });
  addFooter(slide, "Architecture contract: docs/week7_showcase_architecture.md", 2);
  addNotes(slide,
    "Walk the verified classifier main line from audited data through serving, then point down to the amber VLM branch as a bounded exploratory extension rather than the next pipeline stage.",
    "Explain the stable interfaces. Training, evaluation, inference, and Streamlit reuse label and preprocessing contracts, so the classifier proof chain is complete at Serve. Only then introduce the dashed amber VLM branch: it consumes bounded classifier context, remains exploratory, and does not replace or extend the classifier evidence claim.");
}

// 3 — split caveat
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "The official split is useful—and not entity isolated.", "Data audit", { fontSize: 60 });
  addMetric(slide, "227", "overlapping leaf_id values across train and test", { left: 72, top: 236, width: 520 }, COLORS.red);
  addRule(slide, 650, 245, 4, COLORS.red, 300);
  addText(slide, "Safe interpretation", { left: 710, top: 246, width: 430, height: 44 }, { fontSize: 30, bold: true });
  addText(slide, "Strong official-split results support controlled comparisons.", { left: 710, top: 316, width: 440, height: 90 }, { fontSize: 30 });
  addText(slide, "They do not prove leakage-free entity separation or field generalization.", { left: 710, top: 430, width: 440, height: 98 }, { fontSize: 30, bold: true, color: COLORS.red });
  addFooter(slide, "Evidence: reports/data_audit.md · outputs/plantvillage/audit.json", 3);
  addNotes(slide,
    "Lead with the 227 overlap finding. It changes the wording of every downstream metric without making the official split useless for model comparison.",
    "Describe the audit process and distinction between sample-level and entity-level isolation. The safe conclusion is comparative performance under the published split, not real-field reliability or strict leakage freedom.");
}

// 4 — benchmark trade-off
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "Accuracy and deployability need different winners.", "Week 2 benchmark", { fontSize: 60 });
  await addImage(slide, "outputs/plantvillage/benchmarks/week2_accuracy_efficiency_pareto.png", { left: 570, top: 205, width: 638, height: 405 }, { fit: "contain" });
  addText(slide, "ResNet50", { left: 72, top: 240, width: 430, height: 46 }, { fontSize: 34, bold: true });
  addText(slide, "0.9830", { left: 72, top: 292, width: 430, height: 82 }, { fontSize: 72, bold: true, color: COLORS.blue });
  addText(slide, "best accuracy candidate", { left: 72, top: 378, width: 430, height: 38 }, { fontSize: 26, color: COLORS.muted });
  addText(slide, "MobileNetV2", { left: 72, top: 468, width: 430, height: 46 }, { fontSize: 34, bold: true });
  addText(slide, "2.27M · 0.31G", { left: 72, top: 516, width: 430, height: 58 }, { fontSize: 48, bold: true, color: COLORS.green });
  addText(slide, "lightweight deployment candidate", { left: 72, top: 580, width: 440, height: 38 }, { fontSize: 26, color: COLORS.muted });
  addFooter(slide, "Evidence: reports/week2_benchmark_progress.md · official split, shared protocol", 4);
  addNotes(slide,
    "Use the Pareto view to show why one model cannot answer both research accuracy and lightweight deployment questions.",
    "ResNet50 reached 0.9830 test accuracy and 0.9743 Macro F1. MobileNetV2 offered 2.27 million parameters, 0.31G FLOPs, and measured batch-32 MPS throughput of 644.3 images per second excluding preprocessing.");
}

// 5 — ablation selection
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "Controlled ablation selected the final classifier.", "Week 3 decision", { fontSize: 60 });
  await addImage(slide, "reports/figures/week3_validation_macro_f1_curves.png", { left: 548, top: 208, width: 660, height: 390 }, { fit: "contain" });
  addMetric(slide, "0.9953", "Test Accuracy", { left: 72, top: 240, width: 400 }, COLORS.blue);
  addMetric(slide, "0.9941", "Macro F1", { left: 72, top: 445, width: 400 }, COLORS.green);
  addText(slide, "ResNet50 + Label Smoothing + Cosine Scheduler", { left: 560, top: 584, width: 630, height: 48 }, {
    fontSize: 25, bold: true, color: COLORS.text, alignment: "center",
  });
  addFooter(slide, "Evidence: reports/week3_final_model_decision.md · seed 42 · official split", 5);
  addNotes(slide,
    "Show that the final model was selected by a controlled ablation program rather than by a single lucky score.",
    "The selected ResNet50 combines label smoothing and a cosine schedule. Accuracy 0.9953 and Macro F1 0.9941 are a seed-42 official-split result and inherit the documented split limitation.");
}

// 6 — Grad-CAM boundary
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "Grad-CAM shows relevance, not causality.", "Week 4 explainability", { fontSize: 64 });
  await addImage(slide, "reports/figures/week4_baseline_vs_final_gradcam.png", { left: 72, top: 250, width: 860, height: 330 }, {
    fit: "cover",
    crop: { left: 0, top: 0, right: 0, bottom: 0.88 },
  });
  addText(slide, "24", { left: 985, top: 238, width: 220, height: 100 }, { fontSize: 92, bold: true, color: COLORS.blue, alignment: "center" });
  addText(slide, "fixed samples", { left: 970, top: 345, width: 250, height: 42 }, { fontSize: 30, bold: true, alignment: "center" });
  addRule(slide, 982, 425, 226, COLORS.amber, 4);
  addText(slide, "Localization aid\n≠ causal proof", { left: 970, top: 452, width: 250, height: 92 }, { fontSize: 30, bold: true, color: COLORS.amber, alignment: "center" });
  addFooter(slide, "Evidence: reports/week4_consistency_audit.md · 24 fixed Grad-CAM samples", 6);
  addNotes(slide,
    "Compare baseline and final attention patterns while keeping the interpretation boundary explicit: the heatmap shows relevance to a prediction, not a causal biological explanation.",
    "The Week 4 atlas fixes 24 samples across correct and incorrect, high- and low-confidence groups. It also includes error analysis, attention review, and reproducibility checks so attractive examples are not cherry-picked.");
}

// 7 — calibration
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "High accuracy still needs confidence auditing.", "Calibration", { fontSize: 54, height: 168 });
  await addImage(slide, "reports/figures/week4_reliability_diagram.png", { left: 72, top: 300, width: 650, height: 325 }, { fit: "contain" });
  const metrics = [["0.0965", "ECE"], ["0.3348", "MCE"], ["0.0140", "Brier"]];
  metrics.forEach(([value, label], index) => {
    addText(slide, value, { left: 792, top: 305 + index * 96, width: 350, height: 58 }, { fontSize: 50, bold: true, color: index === 1 ? COLORS.amber : COLORS.blue });
    addText(slide, label, { left: 800, top: 361 + index * 96, width: 330, height: 30 }, { fontSize: 22, bold: true, color: COLORS.muted });
  });
  addText(slide, "Top-label calibration only", { left: 790, top: 600, width: 360, height: 34 }, { fontSize: 22, bold: true, color: COLORS.red });
  addFooter(slide, "Evidence: reports/week4_calibration.md · outputs/plantvillage/week4_explainability/calibration.json", 7);
  addNotes(slide,
    "Use the reliability diagram to separate correctness from confidence quality. High accuracy does not guarantee well-calibrated probabilities.",
    "Report ECE 0.0965, MCE 0.3348, and Brier 0.0140 as top-label calibration metrics. This is not full multiclass calibration and should not be presented as a guarantee for high-stakes decisions.");
}

// 8 — product moment
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.ink;
  addHeader(slide, "The same serving layer powers the product moment.", "Week 5 demo", { dark: true, fontSize: 60 });
  await addImage(slide, "docs/media/week7_apple_demo_poster.png", { left: 570, top: 190, width: 638, height: 430 }, { fit: "cover" });
  addText(slide, "Top-5", { left: 72, top: 250, width: 410, height: 66 }, { fontSize: 56, bold: true, color: COLORS.paper });
  addText(slide, "probabilities with shared labels", { left: 72, top: 315, width: 430, height: 55 }, { fontSize: 28, color: COLORS.paper });
  addText(slide, "Grad-CAM", { left: 72, top: 402, width: 410, height: 66 }, { fontSize: 56, bold: true, color: COLORS.green });
  addText(slide, "fixed-example evidence path", { left: 72, top: 468, width: 430, height: 55 }, { fontSize: 28, color: COLORS.paper });
  addText(slide, "129.8 ms", { left: 72, top: 562, width: 220, height: 42 }, { fontSize: 34, bold: true, color: COLORS.amber });
  addText(slide, "Apple container fixed-example total", { left: 300, top: 568, width: 240, height: 50 }, { fontSize: 20, color: COLORS.paper });
  addFooter(slide, "Evidence: outputs/plantvillage/week5_demo/container_e2e.json · one sample, not a benchmark", 8, true);
  addNotes(slide,
    "Connect engineering evidence to the product experience: the same serving layer drives the local app and Apple container flow with Top-5 and Grad-CAM.",
    "The 129.8 millisecond figure is one CPU-only Apple container fixed-example total, not a latency distribution. Keep the educational closed-set warning visible and avoid MPS claims inside the container.");
}

// 9 — VLM comparison
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "Prompt constraints reduced format risk, not disease ambiguity.", "Week 6 Qwen3-VL smoke", { fontSize: 56 });
  const rows = [
    ["Original", "0/15", 0],
    ["Short", "10/15", 10],
    ["Choice", "11/15", 11],
    ["Few-shot choice", "11/15", 11],
  ];
  rows.forEach(([label, value, score], index) => {
    const y = 230 + index * 88;
    addText(slide, label, { left: 72, top: y, width: 260, height: 38 }, { fontSize: 28, bold: true });
    addRect(slide, { left: 345, top: y + 5, width: 560, height: 25 }, COLORS.muted, "rounded-full");
    if (score > 0) addRect(slide, { left: 345, top: y + 5, width: 560 * (score / 15), height: 25 }, score === 11 ? COLORS.green : COLORS.blue, "rounded-full");
    addText(slide, value, { left: 930, top: y - 3, width: 150, height: 45 }, { fontSize: 34, bold: true, color: score === 11 ? COLORS.green : COLORS.text });
  });
  addText(slide, "Condition best", { left: 860, top: 560, width: 210, height: 36 }, { fontSize: 26, bold: true, color: COLORS.muted });
  addText(slide, "1/5", { left: 1080, top: 542, width: 130, height: 65 }, { fontSize: 54, bold: true, color: COLORS.red });
  addFooter(slide, "Evidence: reports/week6_vlm_prompt_compare.md · 5 images / 15 questions · MLX 4-bit smoke", 9);
  addNotes(slide,
    "Show the progression from unconstrained to choice-based prompts. Format compliance and risk-word flags improved, but condition recognition stayed weak.",
    "Original scored 0 of 15, short 10 of 15, choice 11 of 15, and few-shot choice 11 of 15. Plant and health-status questions drove the gains; disease condition remained at best 1 of 5.");
}

// 10 — assistant refusals
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "A safe assistant knows when to stop.", "Prototype safety", { fontSize: 66 });
  const items = [
    ["Educational summary", "bounded classifier context", COLORS.green, "SUMMARY"],
    ["High-risk refusal", "no pesticide or dosage advice", COLORS.red, "STOP"],
    ["Low-confidence refusal", "uncertainty stays visible", COLORS.amber, "PAUSE"],
    ["Out-of-scope refusal", "non-leaf input is rejected", COLORS.blue, "BOUNDARY"],
  ];
  items.forEach(([title, subtitle, color, tag], index) => {
    const y = 220 + index * 98;
    addRule(slide, 72, y, 12, color, 72);
    addText(slide, title, { left: 110, top: y - 2, width: 420, height: 38 }, { fontSize: 30, bold: true });
    addText(slide, subtitle, { left: 110, top: y + 42, width: 520, height: 30 }, { fontSize: 22, color: COLORS.muted });
    addText(slide, tag, { left: 860, top: y + 12, width: 280, height: 42 }, { fontSize: 26, bold: true, color, alignment: "right" });
  });
  addFooter(slide, "Evidence: reports/week6_vlm_assistant.md · outputs/plantvillage/week6_vlm/vlm_assistant_demo.json", 10);
  addNotes(slide,
    "Treat refusal as a capability, not an error. The prototype only summarizes bounded educational evidence when confidence and scope allow it.",
    "Walk through the four tested actions: educational summary, high-risk refusal, low-confidence refusal, and out-of-scope refusal. It does not provide pesticide, dosage, regulatory, or professional diagnostic guidance.");
}

// 11 — evidence ledger
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addHeader(slide, "Verified, smoke-tested, and pending are different states.", "Evidence ledger", { fontSize: 56 });
  const columns = [
    ["VERIFIED", COLORS.green, ["Classifier pipeline", "Benchmark + ablation", "Grad-CAM + calibration", "Local/container demo"]],
    ["SMOKE-TESTED", COLORS.amber, ["Qwen3-VL prompts", "Safety-bounded assistant", "5-image VQA comparison", "MLX 4-bit inference"]],
    ["PENDING", COLORS.red, ["LoRA / QLoRA", "Manual VQA audit", "Field validation", "Entity-isolated study"]],
  ];
  columns.forEach(([heading, color, items], index) => {
    const x = 72 + index * 380;
    addText(slide, heading, { left: x, top: 225, width: 330, height: 40 }, { fontSize: 28, bold: true, color });
    addRule(slide, x, 278, 330, color, 4);
    items.forEach((item, itemIndex) => {
      addText(slide, item, { left: x, top: 310 + itemIndex * 66, width: 330, height: 42 }, { fontSize: 25, bold: itemIndex === 0, color: COLORS.text });
    });
  });
  addFooter(slide, "Status source: TASKS.md · docs/week7_evidence_map.md", 11);
  addNotes(slide,
    "Pause on the distinction between verified, smoke-tested, and pending. This vocabulary prevents a pipeline check from becoming an inflated research claim.",
    "Classification, explainability, and demo work have direct evidence. Qwen and the assistant are smoke-tested prototypes. LoRA, per-entry manual VQA audit, field validation, and an entity-isolated study remain pending.");
}

// 12 — synthesis and handoff
{
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.ink;
  addText(slide, "WEEK 8 HANDOFF", { left: 72, top: 70, width: 420, height: 28 }, { fontSize: 18, bold: true, color: COLORS.green });
  addText(slide, "Credible AI needs\nevidence and limits.", { left: 72, top: 150, width: 800, height: 200 }, { fontSize: 82, bold: true, color: COLORS.paper });
  addRule(slide, 72, 400, 180, COLORS.green, 6);
  addText(slide, "Reproduce.", { left: 72, top: 440, width: 300, height: 56 }, { fontSize: 42, bold: true, color: COLORS.paper });
  addText(slide, "Audit.", { left: 390, top: 440, width: 220, height: 56 }, { fontSize: 42, bold: true, color: COLORS.blue });
  addText(slide, "Release honestly.", { left: 635, top: 440, width: 410, height: 56 }, { fontSize: 42, bold: true, color: COLORS.green });
  addText(slide, "Next: clean-environment reproduction · artifact audit · final publication decision", { left: 72, top: 560, width: 1040, height: 50 }, { fontSize: 27, color: COLORS.paper });
  addFooter(slide, "Handoff: TASKS.md · docs/artifact-index.md · reports/week7_public_release_check.md", 12, true);
  addNotes(slide,
    "Close by resolving the opening: the strongest contribution is the evidence chain and the discipline to state its limits.",
    "Week 8 should add no major feature. Reproduce in a clean environment, audit public artifacts and claims, correct any drift, and make a deliberate release decision without overstating field or VLM capability.");
}

await fs.mkdir(qaDir, { recursive: true });
for (const [index, slide] of presentation.slides.items.entries()) {
  const stem = `slide-${String(index + 1).padStart(2, "0")}`;
  await writeBlob(path.join(qaDir, `${stem}.png`), await presentation.export({ slide, format: "png", scale: 2 }));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(qaDir, `${stem}.layout.json`), await layout.text());
}

await writeBlob(path.join(qaDir, "deck-montage.webp"), await presentation.export({ format: "webp", montage: true, scale: 1 }));
await writeBlob(architectureOutput, await presentation.export({ slide: presentation.slides.items[1], format: "png", scale: 2 }));
const inspect = await presentation.inspect({ kind: "slide,textbox,shape,image,notes,layout", maxChars: 50000 });
await fs.writeFile(path.join(qaDir, "deck.inspect.ndjson"), inspect.ndjson);
const pptx = await PresentationFile.exportPptx(presentation);
await fs.mkdir(path.dirname(finalPptx), { recursive: true });
await pptx.save(finalPptx);

console.log(JSON.stringify({ status: "completed", slides: presentation.slides.items.length, finalPptx, architectureOutput, qaDir }));
