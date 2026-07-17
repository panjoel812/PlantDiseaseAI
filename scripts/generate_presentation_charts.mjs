import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
let sharp;
try {
  sharp = require("sharp");
} catch (error) {
  throw new Error(
    "Unable to load the bundled 'sharp' renderer. Set NODE_PATH to the workspace dependency node_modules directory before running this generator.",
    { cause: error },
  );
}

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = process.env.PRESENTATION_CHARTS_OUT
  ? path.resolve(process.env.PRESENTATION_CHARTS_OUT)
  : path.join(ROOT, "docs/presentation/charts/english-transparent");
fs.mkdirSync(OUT, { recursive: true });

const E = {
  ink: "#1D1D1F",
  secondary: "#6E6E73",
  track: "#E8E8ED",
  blue: "#0A84FF",
  mint: "#32D7C4",
  violet: "#7D5FFF",
  coral: "#FF6B5E",
  amber: "#FFB340",
};

const EDITORIAL_FONT = "SF Pro Display, SF Pro Text, Helvetica Neue, Arial, sans-serif";

function readJson(rel) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, rel), "utf8"));
}

function readText(rel) {
  return fs.readFileSync(path.join(ROOT, rel), "utf8");
}

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function n(value, digits = 0) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function pct(value, digits = 2) {
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function editorialText(x, y, text, size = 26, weight = 400, fill = E.ink, anchor = "start", extra = "") {
  return `<text x="${x}" y="${y}" font-family="${EDITORIAL_FONT}" font-size="${size}" font-weight="${weight}" fill="${fill}" text-anchor="${anchor}" ${extra}>${esc(text)}</text>`;
}

function roundedRect(x, y, w, h, fill, r = h / 2, opacity = 1, extra = "") {
  return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" opacity="${opacity}" ${extra}/>`;
}

function line(x1, y1, x2, y2, stroke = E.track, width = 2, dash = "") {
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${stroke}" stroke-width="${width}" ${dash ? `stroke-dasharray="${dash}"` : ""}/>`;
}

function circle(cx, cy, r, fill, extra = "") {
  return `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${fill}" ${extra}/>`;
}

function bubbleRadius(params) {
  return 18 + 28 * Math.sqrt(params / 24e6);
}

function editorialCanvas(body, width = 1600, height = 900) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${body}</svg>`;
}

function metricTransitionRow({ y, label, before, after, delta, color }) {
  return [
    editorialText(90, y, label, 30, 600, E.secondary),
    editorialText(90, y + 116, before, 118, 650, E.ink, "start", 'letter-spacing="-3"'),
    editorialText(585, y + 105, "→", 74, 500, E.secondary),
    editorialText(745, y + 116, after, 118, 650, E.ink, "start", 'letter-spacing="-3"'),
    roundedRect(1250, y + 40, 260, 92, color, 46),
    editorialText(1380, y + 104, delta, 38, 650, "#FFFFFF", "middle"),
    line(90, y + 174, 1510, y + 174, E.track, 2),
  ].join("");
}

function capsuleBar(x, y, width, height, fraction, color) {
  const fillWidth = Math.max(0, Math.min(width, width * fraction));
  const fillRadius = fillWidth === 0 ? height / 2 : fillWidth <= height * 1.2 ? Math.min(4, fillWidth / 4) : height / 2;
  return roundedRect(x, y, width, height, E.track, height / 2)
    + roundedRect(x, y, fillWidth, height, color, fillRadius);
}

function valueLabel(x, y, value, label, color = E.ink) {
  return editorialText(x, y, value, 112, 650, color, "start", 'letter-spacing="-3"')
    + editorialText(x, y + 46, label.toUpperCase(), 24, 550, E.secondary);
}

function zeroAxisBar({ x0, y, scale, delta, color }) {
  const width = Math.abs(delta) * scale;
  const x = delta < 0 ? x0 - width : x0;
  return roundedRect(x, y, width, 36, color, 18);
}

function openTableRow({ y, cells, accent }) {
  const xs = [125, 250, 980, 1390];
  return roundedRect(90, y - 30, 10, 54, accent, 5)
    + cells.map((cell, index) => editorialText(xs[index], y, cell, index === 1 ? 28 : 24, index === 1 ? 600 : 500, E.ink)).join("")
    + line(90, y + 36, 1510, y + 36, E.track, 2);
}

function segmentBar({ id, x, y, width, height, values, colors }) {
  const total = values.reduce((sum, value) => sum + value, 0);
  let cursor = x;
  const segments = values.map((value, index) => {
    const segmentWidth = width * value / total;
    const rect = `<rect x="${cursor}" y="${y}" width="${segmentWidth + 0.5}" height="${height}" fill="${colors[index]}"/>`;
    cursor += segmentWidth;
    return rect;
  }).join("");
  return `<defs><clipPath id="${id}"><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${height / 2}"/></clipPath></defs><g clip-path="url(#${id})">${segments}</g>`;
}

function axisLabel(x, y, value, anchor = "middle") {
  return editorialText(x, y, value, 20, 500, E.secondary, anchor);
}

function cleanClassName(raw) {
  const [cropRaw, conditionRaw = ""] = raw.split("___");
  const crop = cropRaw
    .replaceAll("_", " ")
    .replace("Corn (maize)", "Corn")
    .replace("Cherry (including sour)", "Cherry")
    .replace("Pepper, bell", "Bell pepper")
    .trim();
  const condition = conditionRaw
    .replaceAll("_", " ")
    .replace("Haunglongbing (Citrus greening)", "Citrus greening")
    .replace("Spider mites Two-spotted spider mite", "Two-spotted spider mite")
    .replace("Cercospora leaf spot Gray leaf spot", "Gray leaf spot")
    .replace("Leaf blight (Isariopsis Leaf Spot)", "Leaf blight")
    .replace("Tomato Yellow Leaf Curl Virus", "Yellow leaf curl virus")
    .replace("Tomato mosaic virus", "Mosaic virus")
    .trim();
  return `${crop} · ${condition}`;
}

const audit = readJson("outputs/plantvillage/audit.json");
const finalMetrics = readJson("outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json");
const finalManifest = readJson("outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/run_manifest.json");
const error = readJson("outputs/plantvillage/week4_explainability/error_analysis.json");
const attention = readJson("outputs/plantvillage/week4_explainability/attention_review.json");
const calibration = readJson("outputs/plantvillage/week4_explainability/calibration.json");
const reproHeatmap = readJson("outputs/plantvillage/week4_explainability/gradcam_reproducibility_direct.json");
const reproAtlas = readJson("outputs/plantvillage/week4_explainability/gradcam_reproducibility.json");
const demoLocal = readJson("outputs/plantvillage/week5_demo/local_e2e.json");
const demoContainer = readJson("outputs/plantvillage/week5_demo/container_e2e.json");
const vqa = readJson("outputs/plantvillage/week6_vlm/vqa_seed_summary.json");
const cleanRepro = readJson("outputs/plantvillage/week8_release/week8-rc1/clean_repro.json");
const claimEvidence = readJson("outputs/plantvillage/week8_release/week8-rc1/claims.json");
const containerEvidence = readText("reports/week5_demo_engineering.md");
const week8Evidence = readText("reports/week8_reproducibility.md");
const dataAuditEvidence = readText("reports/data_audit.md");
const containerMemory = Number(containerEvidence.match(/Memory Usage: ([\d.]+) MiB/)?.[1]);
const containerLimitGiB = Number(containerEvidence.match(/Memory Usage: [\d.]+ MiB \/ ([\d.]+) GiB/)?.[1]);
const containerImageMiB = Number(containerEvidence.match(/variant size: [\d,]+ bytes \(~([\d.]+) MiB\)/)?.[1]);
const containerCpuLimit = Number(containerEvidence.match(/linux\s+arm64\s+running\s+\S+\s+(\d+)\s+1024 MB/)?.[1]);
const containerHealth = week8Evidence.match(/health endpoint returned `([^`]+)`/)?.[1].toUpperCase();
if (![containerMemory, containerLimitGiB, containerImageMiB, containerCpuLimit].every(Number.isFinite) || !containerHealth) {
  throw new Error("Unable to derive Apple container facts from the recorded Week 5/8 evidence");
}
const pytestResult = cleanRepro.commands.find((command) => command.name === "pytest");
const cleanTestCount = Number(pytestResult?.stdout.match(/(\d+) passed/)?.[1]);
const overlapCount = Number(claimEvidence.claim_results.find((claim) => claim.claim_id === "official_split_overlap")?.value);
const imagePathOverlapCount = Number(dataAuditEvidence.match(/train\/test[^\n]*`image_path`[^\n]*?(\d+)/)?.[1]);
const questionTypeCount = Object.keys(vqa.question_type_counts).length;
if (![overlapCount, imagePathOverlapCount, questionTypeCount].every(Number.isFinite)) {
  throw new Error("Unable to derive split-overlap and VQA type counts from recorded evidence");
}
const protocolQualifier = `seed 42 · official split · ${overlapCount} overlapping leaf_id values`;

function sourceWithProtocol(source) {
  return `${source} · ${protocolQualifier}`;
}

function humanizeKey(key) {
  const text = key.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

const modelDefs = [
  ["MobileNetV2", "baseline_mobilenet_v2_best_seed42", "mobilenet_v2_seed42", 32],
  ["ResNet18", "baseline_resnet18_seed42", "resnet18_seed42", 32],
  ["ResNet50", "baseline_resnet50_seed42", "resnet50_seed42", 16],
  ["EfficientNet-B0", "baseline_efficientnet_b0_seed42", "efficientnet_b0_seed42", 32],
  ["EfficientNetV2-S", "baseline_efficientnet_v2_s_seed42", "efficientnet_v2_s_seed42", 8],
];

const models = modelDefs.map(([name, run, benchmark, batch]) => {
  const metrics = readJson(`outputs/plantvillage/${run}/metrics.json`);
  const manifest = readJson(`outputs/plantvillage/${run}/run_manifest.json`);
  const perf = readJson(`outputs/plantvillage/benchmarks/${benchmark}.json`);
  return {
    name,
    accuracy: metrics.accuracy,
    macroF1: metrics.macro_f1,
    params: perf.parameters.total,
    flops: perf.flops.total,
    latency: perf.latency.summary_ms.mean,
    throughput: perf.throughput.images_per_second,
    durationMin: manifest.duration_seconds / 60,
    bestEpoch: manifest.best_epoch,
    batch,
  };
});

const ablationDefs = [
  ["00", "Baseline", "00_resnet50_baseline_seed42"],
  ["01", "Label smoothing", "01_label_smoothing_seed42"],
  ["02", "Focal loss", "02_focal_loss_seed42"],
  ["03", "Cosine schedule", "03_cosine_scheduler_seed42"],
  ["04", "EMA", "04_ema_seed42"],
  ["05", "RandAugment", "05_randaugment_seed42"],
  ["06", "Random erasing", "06_random_erasing_seed42"],
  ["07", "Mixup", "07_mixup_seed42"],
  ["08", "CutMix", "08_cutmix_seed42"],
  ["09", "Smoothing + cosine", "09_combo_candidate_seed42"],
];

const ablations = ablationDefs.map(([id, label, dir]) => {
  const metrics = readJson(`outputs/plantvillage/week3_ablation/${dir}/metrics.json`);
  const manifest = readJson(`outputs/plantvillage/week3_ablation/${dir}/run_manifest.json`);
  return {
    id,
    label,
    accuracy: metrics.accuracy,
    macroF1: metrics.macro_f1,
    durationMin: manifest.duration_seconds / 60,
    bestEpoch: manifest.best_epoch,
  };
});

const promptDefs = [
  ["Original", "qwen3_vl_zero_shot_smoke.json"],
  ["Short", "qwen3_vl_zero_shot_smoke_short.json"],
  ["Choice", "qwen3_vl_choice_smoke.json"],
  ["Few-shot choice", "qwen3_vl_few_shot_choice_smoke.json"],
];

const prompts = promptDefs.map(([name, file]) => {
  const result = readJson(`outputs/plantvillage/week6_vlm/${file}`);
  const condition = result.records.filter((r) => r.question_type === "condition");
  return {
    name,
    correct: result.metrics.correct_count,
    total: result.metrics.question_count,
    conditionCorrect: condition.filter((r) => r.normalized_exact_match).length,
    conditionTotal: condition.length,
    imageCount: new Set(result.records.map((r) => r.image_ref)).size,
  };
});

const charts = [];

const slideUses = {
  "01-project-evidence-snapshot": "Open with the audited evidence footprint.",
  "02-dataset-composition": "Introduce dataset scale and label space.",
  "03-split-and-overlap": "Explain the official split and overlap limitation.",
  "04-class-distribution": "Appendix view of class balance.",
  "05-model-accuracy-f1": "Compare predictive quality across backbones.",
  "06-model-efficiency-pareto": "Discuss compute and throughput trade-offs.",
  "07-model-latency": "Report batch-1 engineering latency.",
  "08-ablation-macro-f1": "Show the controlled ablation ranking.",
  "09-ablation-delta": "Highlight gains and regressions from baseline.",
  "10-ablation-duration": "Compare ablation cost and selection epoch.",
  "11-final-improvement": "Present baseline-to-final improvement.",
  "12-error-audit": "Quantify the final model's residual errors.",
  "13-top-confusions": "Explain the most frequent confusion pairs.",
  "14-attention-review": "Summarize the manual Grad-CAM review.",
  "15-calibration": "Discuss confidence calibration and uncertainty.",
  "16-gradcam-reproducibility": "Document explainability reproducibility.",
  "17-demo-timing-observations": "Show bounded local/container observations.",
  "18-vqa-seed-composition": "Introduce the small VQA seed dataset.",
  "19-vlm-prompt-comparison": "Compare bounded VLM smoke prompts.",
  "20-clean-reproducibility": "Summarize clean-environment release checks.",
  "21-eight-week-evidence-timeline": "Close with the staged evidence journey.",
  "22-apple-container-facts": "Present container engineering facts.",
  "23-per-class-f1": "Appendix view of every class F1 score.",
  "24-full-confusion-matrix": "Appendix view of all normalized confusions.",
};

function addEditorial(slug, title, subtitle, source, render, width = 1600, height = 900) {
  const slideUse = slideUses[slug];
  if (!slideUse) throw new Error(`Missing slide-use suggestion for ${slug}`);
  charts.push({ slug, title, subtitle, source, slideUse, width, height, svg: editorialCanvas(render(), width, height) });
}

addEditorial("01-project-evidence-snapshot", "Project Evidence Snapshot", "One research system, five audited signals", "Sources: final metrics, Week 4 analysis, Week 8 reproducibility audit", () => {
  const xs = [70, 315, 570, 925, 1320];
  const values = [`${models.length}`, `${ablations.length}`, finalMetrics.macro_f1.toFixed(4), `${error.summary.error_count} / ${n(error.summary.sample_count)}`, `${cleanTestCount}`];
  const labels = ["Models", "Ablations", "Macro F1", "Errors", "Tests"];
  return values.map((value, index) => editorialText(xs[index], 500, value, index === 3 ? 70 : index === 2 ? 90 : 112, 650, index === 2 ? E.mint : index === 3 ? E.coral : E.ink, "start", 'letter-spacing="-3"')
    + editorialText(xs[index], 550, labels[index].toUpperCase(), 24, 550, E.secondary)).join("")
    + line(70, 610, 1530, 610, E.track, 2);
});

addEditorial("02-dataset-composition", "Dataset Composition", "Audited PlantVillage rows and label space", "Source: outputs/plantvillage/audit.json and final split manifest", () => {
  const development = finalManifest.train_sample_count + finalManifest.validation_sample_count;
  const test = finalManifest.test_sample_count;
  const total = development + test;
  return valueLabel(70, 260, n(total), "Images")
    + segmentBar({ id: "dataset", x: 70, y: 390, width: 1460, height: 78, values: [development, test], colors: [E.blue, E.mint] })
    + editorialText(70, 520, `${n(development)}  DEVELOPMENT`, 28, 600, E.blue)
    + editorialText(1530, 520, `${n(test)}  TEST`, 28, 600, E.mint, "end")
    + valueLabel(70, 730, `${Object.keys(audit.class_counts).length}`, "Classes")
    + valueLabel(520, 730, `${audit.duplicate_groups.length}`, "Duplicate groups", E.coral);
});

addEditorial("03-split-and-overlap", "Reproducible Split, Known Entity Overlap", "The split is fixed, but not leaf-entity isolated", "Sources: final split manifest and reports/data_audit.md", () => {
  const values = [finalManifest.train_sample_count, finalManifest.validation_sample_count, finalManifest.test_sample_count];
  const labels = ["Train", "Validation", "Test"];
  const colors = [E.blue, E.violet, E.mint];
  return segmentBar({ id: "split", x: 70, y: 210, width: 1460, height: 78, values, colors })
    + labels.map((label, index) => editorialText(70 + index * 380, 350, `${label} ${n(values[index])}`, 30, 600, colors[index])).join("")
    + valueLabel(70, 610, `Seed ${finalManifest.seed}`, "Fixed split")
    + valueLabel(660, 610, `${overlapCount}`, "Overlapping leaf_id")
    + valueLabel(1220, 610, `${imagePathOverlapCount}`, "Overlapping paths");
});

addEditorial("04-class-distribution", "Full 38-Class Development Distribution", "Train + validation counts, ordered by crop and condition", "Source: outputs/plantvillage/audit.json", () => {
  const rows = Object.entries(audit.class_counts).map(([label, count]) => ({ label: cleanClassName(label), count }));
  const max = Math.max(...rows.map((row) => row.count));
  return rows.map((row, index) => {
    const column = index < 19 ? 0 : 1;
    const rowIndex = index % 19;
    const x = 55 + column * 1000;
    const y = 70 + rowIndex * 60;
    return editorialText(x, y + 24, row.label, 20, 500)
      + capsuleBar(x + 500, y + 5, 360, 24, row.count / max, column === 0 ? E.blue : E.mint)
      + editorialText(x + 900, y + 25, n(row.count), 20, 600, E.ink, "end");
  }).join("");
}, 2000, 1240);

addEditorial("05-model-accuracy-f1", "Five-Model Accuracy and Macro F1", "Shared official-split protocol; higher is better", "Source: reports/week2_benchmark_progress.md and model metrics JSON", () => {
  const min = 0.94, max = 1.0, x0 = 390, width = 970;
  const parts = [];
  for (let value = min; value <= max + 0.0001; value += 0.01) {
    const x = x0 + width * (value - min) / (max - min);
    parts.push(line(x, 135, x, 730, E.track, value === min || value >= max ? 2 : 1));
    parts.push(axisLabel(x, 780, `${Math.round(value * 100)}%`));
  }
  models.forEach((model, index) => {
    const y = 190 + index * 108;
    const ax = x0 + width * (model.accuracy - min) / (max - min);
    const fx = x0 + width * (model.macroF1 - min) / (max - min);
    parts.push(editorialText(70, y + 8, model.name, 28, 600));
    parts.push(line(Math.min(ax, fx), y, Math.max(ax, fx), y, E.secondary, 4));
    parts.push(circle(ax, y, 14, E.blue, `data-role="quantitative-dot"`));
    parts.push(circle(fx, y, 14, E.mint, `data-role="quantitative-dot"`));
    parts.push(editorialText(1510, y + 9, `${pct(model.accuracy)} / ${pct(model.macroF1)}`, 23, 600, E.ink, "end"));
  });
  parts.push(circle(390, 842, 10, E.blue, `data-role="quantitative-legend"`));
  parts.push(editorialText(414, 850, "Accuracy", 22, 550));
  parts.push(circle(570, 842, 10, E.mint, `data-role="quantitative-legend"`));
  parts.push(editorialText(594, 850, "Macro F1", 22, 550));
  return parts.join("");
});

addEditorial("06-model-efficiency-pareto", "Model Efficiency Pareto", "FLOPs on x-axis, throughput on y-axis, bubble size = parameters", "Source: Week 2 benchmark JSON; MPS, float32, batch-32 throughput", () => {
  const x0 = 150, y0 = 735, width = 1120, height = 570, maxX = 4.5e9, maxY = 700;
  const parts = [];
  for (let value = 0; value <= 4; value += 1) {
    const x = x0 + width * value * 1e9 / maxX;
    parts.push(line(x, y0, x, y0 - height, E.track, 1));
    parts.push(axisLabel(x, y0 + 38, `${value}G`));
  }
  for (let value = 0; value <= 700; value += 100) {
    const y = y0 - height * value / maxY;
    parts.push(line(x0, y, x0 + width, y, E.track, 1));
    parts.push(axisLabel(x0 - 20, y + 7, `${value}`, "end"));
  }
  parts.push(line(x0, y0, x0 + width, y0, E.secondary, 2));
  parts.push(line(x0, y0, x0, y0 - height, E.secondary, 2));
  models.forEach((model, index) => {
    const x = x0 + width * model.flops / maxX;
    const y = y0 - height * model.throughput / maxY;
    const radius = bubbleRadius(model.params);
    parts.push(circle(x, y, radius, index === 0 ? E.mint : E.blue, `opacity="0.9" data-role="quantitative-bubble" data-parameters="${model.params}"`));
    const dx = model.name === "MobileNetV2" ? 34 : model.name === "EfficientNet-B0" ? 30 : 18;
    const dy = model.name === "ResNet18" ? -34 : -radius - 12;
    parts.push(editorialText(x + dx, y + dy, model.name, 21, 600));
  });
  parts.push(editorialText(710, 825, "FLOPs", 24, 600, E.secondary, "middle"));
  parts.push(`<text x="46" y="450" transform="rotate(-90 46 450)" font-family="${EDITORIAL_FONT}" font-size="24" font-weight="600" fill="${E.secondary}" text-anchor="middle">Throughput (images/s)</text>`);
  parts.push(editorialText(1350, 205, "Parameters", 24, 600, E.secondary));
  [[5e6, "5M", 280], [25e6, "25M", 380]].forEach(([params, label, y]) => {
    const radius = bubbleRadius(params);
    parts.push(circle(1380, y, radius, E.blue, `opacity="0.9" data-role="quantitative-legend" data-parameters="${params}"`));
    parts.push(editorialText(1380 + radius + 24, y + 8, label, 22, 550));
  });
  return parts.join("");
});

addEditorial("07-model-latency", "Batch-1 Model Latency", "Mean MPS latency; preprocessing excluded", "Source: Week 2 benchmark JSON; 10 warm-ups and 50 measured iterations", () => {
  const x0 = 390, width = 1000, max = 16;
  const parts = [];
  for (let value = 0; value <= max; value += 4) {
    const x = x0 + width * value / max;
    parts.push(line(x, 120, x, 730, E.track, value === 0 ? 3 : 1));
    parts.push(axisLabel(x, 790, `${value} ms`));
  }
  models.forEach((model, index) => {
    const y = 175 + index * 108;
    parts.push(editorialText(70, y + 34, model.name, 28, 600));
    parts.push(roundedRect(x0, y, width * model.latency / max, 50, index === 1 ? E.mint : E.blue, 25));
    parts.push(editorialText(1510, y + 36, `${model.latency.toFixed(2)} ms`, 27, 600, E.ink, "end"));
  });
  return parts.join("");
});

addEditorial("08-ablation-macro-f1", "Controlled Ablation: Test Macro F1", "Ten seed-42 runs under the frozen official-split protocol", sourceWithProtocol("Source: Week 3 ablation metrics JSON"), () => {
  const min = 0.95, max = 1.0, x0 = 480, width = 930;
  const ranked = [...ablations].sort((a, b) => b.macroF1 - a.macroF1);
  return ranked.map((item, index) => {
    const y = 75 + index * 80;
    const selected = item.id === "09";
    return editorialText(70, y + 30, `${item.id}  ${item.label}`, 25, selected ? 650 : 500)
      + capsuleBar(x0, y, width, 38, (item.macroF1 - min) / (max - min), selected ? E.mint : E.blue)
      + editorialText(1520, y + 31, item.macroF1.toFixed(4), 25, 650, selected ? E.mint : E.ink, "end");
  }).join("")
    + editorialText(x0, 870, "0.9500", 20, 500, E.secondary)
    + editorialText(x0 + width, 870, "1.0000", 20, 500, E.secondary, "end");
});

addEditorial("09-ablation-delta", "Ablation Delta from Frozen Baseline", "Change in Test Macro F1, measured in percentage points", sourceWithProtocol("Source: Week 3 ablation metrics JSON"), () => {
  const baseline = ablations[0].macroF1, x0 = 850, scale = 250;
  const parts = [line(x0, 80, x0, 790, E.secondary, 3)];
  ablations.slice(1).forEach((item, index) => {
    const y = 95 + index * 82;
    const delta = (item.macroF1 - baseline) * 100;
    parts.push(editorialText(70, y + 29, `${item.id}  ${item.label}`, 25, 550));
    parts.push(zeroAxisBar({ x0, y, scale, delta, color: delta < 0 ? E.coral : E.mint }));
    parts.push(editorialText(delta < 0 ? x0 - Math.abs(delta) * scale - 20 : x0 + delta * scale + 20, y + 29, `${delta >= 0 ? "+" : ""}${delta.toFixed(2)} pp`, 24, 650, delta < 0 ? E.coral : E.ink, delta < 0 ? "end" : "start"));
  });
  parts.push(editorialText(x0, 850, "0 pp", 21, 550, E.secondary, "middle"));
  return parts.join("");
});

addEditorial("10-ablation-duration", "Ablation Runtime and Best Epoch", "A high-contrast comparison table from formal run manifests", "Source: Week 3 run manifests", () => {
  const parts = [
    editorialText(90, 70, "RUN", 20, 600, E.secondary),
    editorialText(250, 70, "ABLATION", 20, 600, E.secondary),
    editorialText(980, 70, "DURATION", 20, 600, E.secondary),
    editorialText(1390, 70, "BEST EPOCH", 20, 600, E.secondary),
    line(90, 98, 1510, 98, E.ink, 2),
  ];
  ablations.forEach((item, index) => {
    parts.push(openTableRow({ y: 145 + index * 72, cells: [item.id, item.label, `${item.durationMin.toFixed(1)} min`, `${item.bestEpoch}`], accent: item.id === "09" ? E.mint : E.blue }));
  });
  return parts.join("");
});

addEditorial("11-final-improvement", "Baseline to Final Candidate", "Label smoothing + cosine schedule under the same seed-42 protocol", "Source: Week 3 baseline and final metrics JSON", () => {
  const base = ablations[0];
  const fin = ablations[9];
  const accuracyDelta = (fin.accuracy - base.accuracy) * 100;
  const f1Delta = (fin.macroF1 - base.macroF1) * 100;
  return metricTransitionRow({
    y: 160,
    label: "ACCURACY",
    before: pct(base.accuracy),
    after: pct(fin.accuracy),
    delta: `+${accuracyDelta.toFixed(2)} pp`,
    color: E.blue,
  }) + metricTransitionRow({
    y: 500,
    label: "MACRO F1",
    before: pct(base.macroF1),
    after: pct(fin.macroF1),
    delta: `+${f1Delta.toFixed(2)} pp`,
    color: E.mint,
  });
});

addEditorial("12-error-audit", "Test Error Audit", "Every error remains traceable to a sample, label, prediction, and confidence", sourceWithProtocol("Source: outputs/plantvillage/week4_explainability/error_analysis.json"), () => {
  const summary = error.summary;
  return valueLabel(70, 340, `${summary.error_count}`, "Errors", E.coral)
    + editorialText(70, 640, pct(summary.error_count / summary.sample_count), 88, 650, E.ink, "start", 'letter-spacing="-3"')
    + editorialText(70, 690, "ERROR RATE", 24, 550, E.secondary)
    + valueLabel(590, 260, n(summary.sample_count), "Test images")
    + valueLabel(1120, 260, pct(summary.accuracy), "Accuracy", E.mint)
    + valueLabel(590, 610, `${summary.high_confidence_error_count}`, "High-confidence errors", E.coral)
    + valueLabel(1120, 610, summary.high_confidence_threshold.toFixed(2), "Threshold");
});

addEditorial("13-top-confusions", "Top Confusion Pairs", "Most frequent true → predicted class errors", sourceWithProtocol("Source: Week 4 error-analysis JSON"), () => {
  const pairs = error.confusion_pairs.slice(0, 8);
  const max = Math.max(...pairs.map((pair) => pair.count));
  return pairs.map((pair, index) => {
    const y = 70 + index * 104;
    const label = `${cleanClassName(pair.true_class_name)} → ${cleanClassName(pair.predicted_class_name)}`;
    return editorialText(70, y + 26, label, 23, 550)
      + line(900, y + 45, 900, y + 88, E.secondary, 2)
      + capsuleBar(900, y + 49, 510, 34, pair.count / max, E.coral)
      + editorialText(1510, y + 77, `${pair.count}`, 27, 650, E.ink, "end");
  }).join("");
});

addEditorial("14-attention-review", "Grad-CAM Attention Review", `Manual review of ${attention.summary.sample_count} fixed samples; relevance is non-causal`, sourceWithProtocol("Source: outputs/plantvillage/week4_explainability/attention_review.json"), () => {
  const attentionEntries = ["lesion", "mixed", "leaf", "background"].map((key) => [key, attention.summary.attention_region_counts[key]]);
  const errorEntries = Object.entries(attention.summary.error_type_counts).filter(([key]) => key !== "not_error");
  const failedSamples = attention.summary.sample_count - attention.summary.error_type_counts.not_error;
  const colors = [E.violet, E.blue, E.mint, E.track];
  const directLabels = (entries, y) => entries.map(([key, count], index) => {
    const x = 70 + index * 375;
    return roundedRect(x, y, 20, 20, colors[index], 4)
      + editorialText(x + 34, y + 18, `${humanizeKey(key)} ${count}`, 22, 550);
  }).join("");
  return editorialText(70, 150, "ATTENTION REGION", 24, 600, E.secondary)
    + segmentBar({ id: "attention", x: 70, y: 190, width: 1460, height: 72, values: attentionEntries.map(([, count]) => count), colors })
    + directLabels(attentionEntries, 315)
    + editorialText(70, 500, `ERROR TYPE · ${failedSamples} FAILED SAMPLES`, 24, 600, E.secondary)
    + segmentBar({ id: "attention-errors", x: 70, y: 540, width: 1460, height: 72, values: errorEntries.map(([, count]) => count), colors })
    + directLabels(errorEntries, 665);
});

addEditorial("15-calibration", "Confidence Calibration", "Reliability diagram with top-label calibration metrics", sourceWithProtocol("Source: outputs/plantvillage/week4_explainability/calibration.json"), () => {
  const x0 = 150, y0 = 740, width = 760, height = 600;
  const bins = calibration.bins.filter((bin) => bin.count > 0);
  const parts = [];
  for (let value = 0; value <= 1.0001; value += 0.2) {
    const x = x0 + width * value;
    const y = y0 - height * value;
    parts.push(line(x, y0, x, y0 - height, E.track, 1));
    parts.push(line(x0, y, x0 + width, y, E.track, 1));
    parts.push(axisLabel(x, y0 + 38, value.toFixed(1)));
    parts.push(axisLabel(x0 - 18, y + 7, value.toFixed(1), "end"));
  }
  parts.push(line(x0, y0, x0 + width, y0 - height, E.secondary, 2, "10 10"));
  const points = bins.map((bin) => `${x0 + width * bin.avg_confidence},${y0 - height * bin.accuracy}`).join(" ");
  parts.push(`<polyline points="${points}" fill="none" stroke="${E.blue}" stroke-width="7" stroke-linejoin="round"/>`);
  bins.forEach((bin) => parts.push(circle(x0 + width * bin.avg_confidence, y0 - height * bin.accuracy, 10, E.mint, `stroke="${E.ink}" stroke-width="2" data-role="quantitative-dot"`)));
  parts.push(editorialText(530, 825, "Confidence", 23, 600, E.secondary, "middle"));
  parts.push(`<text x="45" y="440" transform="rotate(-90 45 440)" font-family="${EDITORIAL_FONT}" font-size="23" font-weight="600" fill="${E.secondary}" text-anchor="middle">Empirical accuracy</text>`);
  const summary = calibration.summary;
  parts.push(valueLabel(1040, 260, summary.top_label_ece.toFixed(4), "ECE"));
  parts.push(valueLabel(1040, 520, summary.top_label_mce.toFixed(4), "MCE"));
  parts.push(valueLabel(1040, 780, summary.top_label_brier.toFixed(4), "Brier"));
  return parts.join("");
});

addEditorial("16-gradcam-reproducibility", "Grad-CAM Reproducibility", "Fixed checkpoint, samples, target layer, and predicted-class target", sourceWithProtocol("Source: direct heatmap reproducibility JSON and atlas report"), () => {
  const atlasMaxDiff = Math.max(...reproAtlas.rows.map((row) => row.panel_max_channel_abs_diff));
  const rows = [
    ["TARGET LAYER", reproHeatmap.target_layer],
    ["TARGET MODE", reproHeatmap.target_mode],
    ["MAX ABS DIFFERENCE", reproHeatmap.max_abs_diff_overall.toFixed(1)],
    ["ATLAS TOLERANCE", `≤ ${atlasMaxDiff} / 255`],
  ];
  return editorialText(70, 390, `${reproHeatmap.exact_heatmap_match_count} / ${reproHeatmap.sample_count}`, 152, 650, E.mint, "start", 'letter-spacing="-5"')
    + editorialText(70, 450, "EXACT MATCHES", 26, 600, E.secondary)
    + rows.map(([label, value], index) => {
      const y = 185 + index * 150;
      return editorialText(850, y, label, 23, 600, E.secondary)
        + editorialText(850, y + 65, value, 52, 650, E.ink)
        + line(850, y + 92, 1510, y + 92, E.track, 2);
    }).join("");
});

addEditorial("17-demo-timing-observations", "Fixed-Example Timing Observations", "Engineering observations on one synthetic image — not latency benchmarks", "Sources: Week 5 local and Apple-container E2E JSON", () => {
  const rows = [["Local CPU", demoLocal.timings_ms], ["Apple container CPU", demoContainer.timings_ms]];
  const max = Math.max(...rows.map(([, timing]) => timing.total_ms));
  const colors = [E.track, E.blue, E.mint, E.coral];
  const parts = [];
  rows.forEach(([label, timing], index) => {
    const y = 180 + index * 310;
    const other = Math.max(0, timing.total_ms - timing.preprocess_ms - timing.prediction_ms - timing.gradcam_ms);
    const values = [timing.preprocess_ms, timing.prediction_ms, timing.gradcam_ms, other];
    parts.push(editorialText(70, y, label, 32, 650));
    parts.push(segmentBar({ id: `timing-${index}`, x: 70, y: y + 55, width: 1200 * timing.total_ms / max, height: 74, values, colors }));
    parts.push(editorialText(1510, y + 110, `${timing.total_ms.toFixed(1)} ms`, 42, 650, E.ink, "end"));
    parts.push(editorialText(70, y + 175, `Preprocess ${timing.preprocess_ms.toFixed(1)} · Prediction ${timing.prediction_ms.toFixed(1)} · Grad-CAM ${timing.gradcam_ms.toFixed(1)} · Other ${other.toFixed(1)} ms`, 23, 500, E.secondary));
  });
  return parts.join("");
});

addEditorial("18-vqa-seed-composition", "VQA Seed Composition", "Label-grounded questions with a grouped split audit", "Source: outputs/plantvillage/week6_vlm/vqa_seed_summary.json", () => {
  const splitValues = [vqa.split_counts.train, vqa.split_counts.validation, vqa.split_counts.test];
  const typeValues = [vqa.question_type_counts.plant, vqa.question_type_counts.condition, vqa.question_type_counts.health_status];
  return valueLabel(70, 210, `${vqa.image_count}`, "Images")
    + valueLabel(470, 210, `${vqa.sample_count}`, "Questions")
    + valueLabel(870, 210, `${questionTypeCount}`, "Question types")
    + valueLabel(1270, 210, `${vqa.entity_split_leakage}`, "Leakage flag", E.mint)
    + editorialText(70, 430, `SPLIT · ${splitValues.join(" / ")}`, 24, 600, E.secondary)
    + segmentBar({ id: "vqa-split", x: 70, y: 465, width: 1460, height: 66, values: splitValues, colors: [E.blue, E.violet, E.mint] })
    + editorialText(70, 580, `Train ${splitValues[0]}`, 22, 600, E.blue)
    + editorialText(320, 580, `Validation ${splitValues[1]}`, 22, 600, E.violet)
    + editorialText(620, 580, `Test ${splitValues[2]}`, 22, 600, E.mint)
    + editorialText(70, 710, `QUESTION TYPES · ${typeValues.join(" / ")}`, 24, 600, E.secondary)
    + segmentBar({ id: "vqa-types", x: 70, y: 745, width: 1460, height: 66, values: typeValues, colors: [E.violet, E.blue, E.mint] })
    + editorialText(70, 860, `Plant ${typeValues[0]} · Condition ${typeValues[1]} · Health status ${typeValues[2]}`, 22, 600, E.ink);
});

addEditorial("19-vlm-prompt-comparison", "Qwen3-VL Prompt Comparison", `${prompts[0].imageCount} images · ${prompts[0].total} questions · strict exact match`, "Source: Week 6 Qwen3-VL smoke JSON", () => {
  return prompts.map((prompt, index) => {
    const y = 110 + index * 185;
    return editorialText(70, y + 40, prompt.name, 30, 650)
      + capsuleBar(420, y, 850, 62, prompt.correct / prompt.total, index < 2 ? E.blue : E.mint)
      + editorialText(1310, y + 30, `${prompt.correct} / ${prompt.total}`, 30, 650)
      + editorialText(1310, y + 66, `Condition ${prompt.conditionCorrect} / ${prompt.conditionTotal}`, 20, 550, prompt.conditionCorrect ? E.mint : E.coral);
  }).join("");
});

addEditorial("20-clean-reproducibility", "Clean Reproducibility Audit", "Repository-external locked environment", "Sources: Week 8 clean-repro and claim-evidence JSON", () => {
  const passed = cleanRepro.commands.filter((command) => command.status === "passed").length;
  const rows = [["PYTEST", `${cleanTestCount}`], ["BROKEN LINKS", `${claimEvidence.counts.broken_links}`], ["NUMERICAL CLAIMS", `${claimEvidence.counts.claims}`], ["BOUNDARY CLAIMS", `${claimEvidence.counts.boundaries}`]];
  return editorialText(70, 390, `${passed} / ${cleanRepro.commands.length}`, 152, 650, E.mint, "start", 'letter-spacing="-5"')
    + editorialText(70, 450, "CHECKS PASSED", 26, 600, E.secondary)
    + rows.map(([label, value], index) => {
      const column = index % 2;
      const row = Math.floor(index / 2);
      const x = 720 + column * 500;
      const y = 235 + row * 330;
      return editorialText(x, y, value, 104, 650, index === 1 ? E.blue : E.ink, "start", 'letter-spacing="-3"')
        + editorialText(x, y + 48, label, 23, 600, E.secondary);
    }).join("");
});

addEditorial("21-eight-week-evidence-timeline", "Eight-Week Evidence Timeline", "Each stage closes one research or engineering dependency", "Source: TASKS.md and docs/artifact-index.md", () => {
  const labels = [["W1", "Data + baseline"], ["W2", "5-model benchmark"], ["W3", "Ablation"], ["W4", "Errors + Grad-CAM"], ["W5", "Demo + container"], ["W6", "VLM smoke"], ["W7", "Showcase assets"], ["W8", "Release audit"]];
  const startX = 100, gap = 200, y = 410;
  const pathEnd = startX + 7 * gap;
  const parts = [`<path id="timeline-path" d="M ${startX} ${y} H ${pathEnd}" fill="none" stroke="${E.track}" stroke-width="6" stroke-linecap="round"/>`];
  labels.forEach(([week, label], index) => {
    const x = startX + index * gap;
    const color = index < 4 ? E.blue : E.mint;
    parts.push(`<g class="timeline-node" data-week="${week}">`);
    parts.push(line(x, y - 22, x, y + 22, color, 4));
    parts.push(roundedRect(x - 9, y - 9, 18, 18, color, 4, 1, 'data-role="timeline-marker"'));
    parts.push(editorialText(x, y - 74, week, 24, 650, color, "middle"));
    parts.push(editorialText(x, y + 82, label, 20, 550, E.ink, "middle", 'data-role="timeline-action"'));
    parts.push(`</g>`);
  });
  return parts.join("");
});

addEditorial("22-apple-container-facts", "Apple Container Engineering Facts", "Historical Week 5 runtime evidence and current Week 8 health audit", "Sources: Week 5 engineering report and Week 8 reproducibility report", () => {
  const limitMiB = containerLimitGiB * 1024;
  return editorialText(70, 235, `${containerMemory.toFixed(2)} MiB / ${containerLimitGiB.toFixed(0)} GiB`, 104, 650, E.ink, "start", 'letter-spacing="-3"')
    + editorialText(70, 295, `${(containerMemory / limitMiB * 100).toFixed(1)}% MEMORY`, 26, 600, E.secondary)
    + capsuleBar(70, 350, 1460, 68, containerMemory / limitMiB, E.blue)
    + valueLabel(70, 700, `~${containerImageMiB.toFixed(0)} MiB`, "Image")
    + valueLabel(610, 700, `${containerCpuLimit} CPUs`, "Limit")
    + valueLabel(1130, 700, containerHealth, "Health", E.mint);
});

addEditorial("23-per-class-f1", "Per-Class F1 — All 38 Classes", "Final selected classifier · shared 0.95–1.00 scale · support shown for every class", sourceWithProtocol("Source: final selected run metrics.json"), () => {
  const entries = Object.entries(finalMetrics.per_class), min = 0.95, max = 1.0;
  const parts = [];
  [0, 1].forEach((column) => {
    const x0 = 520 + column * 1000;
    const width = 360;
    for (let value = min; value <= max + 0.0001; value += 0.01) {
      const x = x0 + width * (value - min) / (max - min);
      parts.push(line(x, 42, x, 1160, E.track, value === min || value >= max ? 2 : 1));
      parts.push(axisLabel(x, 1210, value.toFixed(2)));
    }
  });
  entries.forEach(([rawName, metrics], index) => {
    const column = index < 19 ? 0 : 1;
    const row = index % 19;
    const x = 45 + column * 1000;
    const x0 = x + 475;
    const y = 70 + row * 58;
    const dotX = x0 + 360 * (metrics.f1 - min) / (max - min);
    parts.push(editorialText(x, y + 8, cleanClassName(rawName), 18, 500));
    parts.push(line(x0, y, x0 + 360, y, E.track, 3));
    parts.push(circle(dotX, y, 10, metrics.f1 >= 0.99 ? E.mint : E.blue, `data-role="quantitative-dot"`));
    parts.push(editorialText(x + 850, y + 8, `${metrics.f1.toFixed(3)} · n=${metrics.support}`, 16, 600, E.ink));
  });
  return parts.join("");
}, 2000, 1240);

addEditorial("24-full-confusion-matrix", "Normalized Confusion Matrix — All 38 Classes", "Rows are true classes; columns are predictions · blue diagonal, coral off-diagonal errors", sourceWithProtocol("Source: Week 4 error-analysis JSON · final selected classifier"), () => {
  const matrix = error.normalized_confusion_matrix;
  const names = error.class_names;
  const size = 1026;
  const cell = size / names.length;
  const x0 = 95;
  const y0 = 210;
  const maxOffDiagonal = Math.max(...matrix.flatMap((row, i) => row.filter((_, j) => i !== j)));
  const cells = matrix.map((row, i) => row.map((value, j) => {
    const isDiagonal = i === j;
    const opacity = isDiagonal
      ? 0.15 + 0.85 * value
      : value === 0 ? 0 : 0.16 + 0.84 * value / maxOffDiagonal;
    return `<rect x="${x0 + j * cell}" y="${y0 + i * cell}" width="${cell + 0.25}" height="${cell + 0.25}" fill="${isDiagonal ? E.blue : E.coral}" opacity="${opacity}"/>`;
  }).join("")).join("");
  const ticks = names.map((_, index) => {
    const x = x0 + (index + 0.5) * cell;
    const y = y0 + (index + 0.5) * cell;
    return editorialText(x, y0 - 12, `${index}`, 12, 500, E.secondary, "middle")
      + editorialText(x0 - 12, y + 4, `${index}`, 12, 500, E.secondary, "end");
  }).join("");
  const key = names.map((name, index) => {
    const column = index < 19 ? 0 : 1;
    const row = index % 19;
    const x = 1190 + column * 390;
    const y = 220 + row * 52;
    return `<rect x="${x}" y="${y}" width="34" height="28" fill="${E.blue}"/>`
      + editorialText(x + 17, y + 20, `${index}`, 13, 650, "#FFFFFF", "middle")
      + editorialText(x + 46, y + 20, cleanClassName(name), 14, 500);
  }).join("");
  return cells + ticks
    + editorialText(x0 + size / 2, 1288, "Predicted class", 18, 600, E.secondary, "middle")
    + `<text x="38" y="${y0 + size / 2}" transform="rotate(-90 38 ${y0 + size / 2})" font-family="${EDITORIAL_FONT}" font-size="18" font-weight="600" fill="${E.secondary}" text-anchor="middle">True class</text>`
    + editorialText(1190, 174, "CLASS INDEX", 17, 600, E.secondary)
    + key
    + `<rect x="1190" y="1245" width="22" height="22" fill="${E.blue}"/>`
    + editorialText(1224, 1263, "Correct", 16, 600)
    + `<rect x="1460" y="1245" width="22" height="22" fill="${E.coral}"/>`
    + editorialText(1494, 1263, "Error", 16, 600);
}, 2000, 1360);

async function writeOutputs() {
  const manifestRows = [];
  for (const chart of charts) {
    const svgPath = path.join(OUT, `${chart.slug}.svg`);
    const pngPath = path.join(OUT, `${chart.slug}.png`);
    fs.writeFileSync(svgPath, chart.svg, "utf8");
    await sharp(Buffer.from(chart.svg))
      .resize({ width: 3200 })
      .png({ compressionLevel: 9 })
      .toFile(pngPath);
    manifestRows.push(`| ${chart.slug} | ${chart.title} | [SVG](./${chart.slug}.svg) | [PNG](./${chart.slug}.png) | ${chart.source} | ${chart.slideUse} |`);
  }

  const readme = `# English Transparent Presentation Charts

All assets use English labels, transparent backgrounds, editable SVG, and 2× PNG raster exports. Values are read from PlantDiseaseAI evidence files by \`scripts/generate_presentation_charts.mjs\`.

## Usage boundaries

- Final classifier results are seed-42 official-split observations with ${overlapCount} overlapping \`leaf_id\` values.
- Timing figures are fixed synthetic-input engineering observations, not general benchmarks.
- VLM figures are a 5-image / 15-question smoke study; LoRA/QLoRA was not completed.
- Grad-CAM is non-causal relevance visualization.
- Chart 20 records the frozen Week 8 RC snapshot: ${claimEvidence.counts.claims} numerical claims and ${claimEvidence.counts.boundaries} boundary claims; the current worktree may contain later claims.

| File | Chart | SVG | PNG | Evidence | Slide use |
| --- | --- | --- | --- | --- | --- |
${manifestRows.join("\n")}
`;
  fs.writeFileSync(path.join(OUT, "README.md"), readme, "utf8");

  const cols = 4;
  const thumbW = 380;
  const thumbH = 214;
  const gap = 20;
  const thumbs = [];
  for (let i = 0; i < charts.length; i++) {
    const input = path.join(OUT, `${charts[i].slug}.png`);
    const buffer = await sharp(input).resize({ width: thumbW, height: thumbH, fit: "contain", background: { r: 255, g: 255, b: 255, alpha: 0 } }).toBuffer();
    thumbs.push({ input: buffer, left: gap + (i % cols) * (thumbW + gap), top: gap + Math.floor(i / cols) * (thumbH + gap) });
  }
  const rows = Math.ceil(charts.length / cols);
  await sharp({
    create: {
      width: cols * (thumbW + gap) + gap,
      height: rows * (thumbH + gap) + gap,
      channels: 4,
      background: { r: 255, g: 255, b: 255, alpha: 1 },
    },
  }).composite(thumbs).png().toFile(path.join(OUT, "_qa-contact-sheet.png"));

  console.log(JSON.stringify({ status: "completed", chart_count: charts.length, output_dir: path.relative(ROOT, OUT) }));
}

await writeOutputs();
