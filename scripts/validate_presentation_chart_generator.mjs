import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(os.tmpdir(), `plantdisease-chart-generator-validation-${process.pid}`);
const GENERATOR = path.join(ROOT, "scripts/generate_presentation_charts.mjs");
const BUNDLED_NODE_MODULES = path.join(
  os.homedir(),
  ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules",
);
const expectedSlugs = [
  "01-project-evidence-snapshot",
  "02-dataset-composition",
  "03-split-and-overlap",
  "04-class-distribution",
  "05-model-accuracy-f1",
  "06-model-efficiency-pareto",
  "07-model-latency",
  "08-ablation-macro-f1",
  "09-ablation-delta",
  "10-ablation-duration",
  "11-final-improvement",
  "12-error-audit",
  "13-top-confusions",
  "14-attention-review",
  "15-calibration",
  "16-gradcam-reproducibility",
  "17-demo-timing-observations",
  "18-vqa-seed-composition",
  "19-vlm-prompt-comparison",
  "20-clean-reproducibility",
  "21-eight-week-evidence-timeline",
  "22-apple-container-facts",
  "23-per-class-f1",
  "24-full-confusion-matrix",
];

const circleAllowed = new Set([
  "05-model-accuracy-f1",
  "06-model-efficiency-pareto",
  "15-calibration",
  "23-per-class-f1",
]);
const approvedColors = new Set([
  "#1D1D1F", "#6E6E73", "#E8E8ED", "#0A84FF", "#32D7C4",
  "#7D5FFF", "#FF6B5E", "#FFB340", "#FFFFFF",
]);
const accentColors = new Set(["#0A84FF", "#32D7C4", "#7D5FFF", "#FF6B5E", "#FFB340"]);
const threeAccentCharts = new Map([
  ["02-dataset-composition", "development, test, and duplicate-group evidence"],
  ["03-split-and-overlap", "train, validation, and test splits"],
  ["14-attention-review", "three attention/error categories plus a neutral fourth"],
  ["17-demo-timing-observations", "prediction, Grad-CAM, and other time"],
  ["18-vqa-seed-composition", "three split and question-type categories"],
  ["19-vlm-prompt-comparison", "prompt score, selected score, and condition status"],
]);
const oldChartTitles = {
  "01-project-evidence-snapshot": "Project Evidence Snapshot",
  "02-dataset-composition": "Dataset Composition",
  "03-split-and-overlap": "Reproducible Split, Known Entity Overlap",
  "04-class-distribution": "Full 38-Class Development Distribution",
  "05-model-accuracy-f1": "Five-Model Accuracy and Macro F1",
  "06-model-efficiency-pareto": "Model Efficiency Pareto",
  "07-model-latency": "Batch-1 Model Latency",
  "08-ablation-macro-f1": "Controlled Ablation: Test Macro F1",
  "09-ablation-delta": "Ablation Delta from Frozen Baseline",
  "10-ablation-duration": "Ablation Runtime and Best Epoch",
  "11-final-improvement": "Baseline to Final Candidate",
  "12-error-audit": "Test Error Audit",
  "13-top-confusions": "Top Confusion Pairs",
  "14-attention-review": "Grad-CAM Attention Review",
  "15-calibration": "Confidence Calibration",
  "16-gradcam-reproducibility": "Grad-CAM Reproducibility",
  "17-demo-timing-observations": "Fixed-Example Timing Observations",
  "18-vqa-seed-composition": "VQA Seed Composition",
  "19-vlm-prompt-comparison": "Qwen3-VL Prompt Comparison",
  "20-clean-reproducibility": "Clean Reproducibility Audit",
  "21-eight-week-evidence-timeline": "Eight-Week Evidence Timeline",
  "22-apple-container-facts": "Apple Container Engineering Facts",
  "23-per-class-f1": "Per-Class F1 — All 38 Classes",
  "24-full-confusion-matrix": "Normalized Confusion Matrix — All 38 Classes",
};
const requiredDirectTokens = {
  "01-project-evidence-snapshot": ["5", "10", "0.9941", "50 / 10,709", "226"],
  "02-dataset-composition": ["54,305", "43,596", "10,709", "38", "14"],
  "03-split-and-overlap": ["Seed 42", "227", "Train", "Validation", "Test"],
  "04-class-distribution": ["Apple · Apple scab", "Tomato · Yellow leaf curl virus"],
  "05-model-accuracy-f1": ["94%", "100%", "Accuracy", "Macro F1", "MobileNetV2", "EfficientNetV2-S"],
  "06-model-efficiency-pareto": ["FLOPs", "Throughput", "Parameters", "MobileNetV2", "ResNet50"],
  "07-model-latency": ["0 ms", "6.49 ms", "2.82 ms", "14.99 ms"],
  "08-ablation-macro-f1": ["Baseline", "Smoothing + cosine", "0.9941"],
  "09-ablation-delta": ["0 pp", "+1.98 pp", "Focal loss"],
  "10-ablation-duration": ["RUN", "ABLATION", "DURATION", "BEST EPOCH"],
  "11-final-improvement": ["98.30%", "99.53%", "+1.23 pp", "97.43%", "99.41%", "+1.98 pp"],
  "12-error-audit": ["50", "10,709", "99.53%", "0.80", "0.47%"],
  "13-top-confusions": ["→", "3"],
  "14-attention-review": ["ATTENTION REGION", "FAILED SAMPLES"],
  "15-calibration": ["Confidence", "Empirical accuracy", "ECE", "MCE", "BRIER"],
  "16-gradcam-reproducibility": ["24 / 24", "layer4.2", "predicted", "0.0"],
  "17-demo-timing-observations": ["Local CPU", "Apple container CPU", "ms"],
  "18-vqa-seed-composition": ["24", "72", "48", "9", "15", "24 / 24 / 24"],
  "19-vlm-prompt-comparison": ["Original", "Short", "Choice", "Few-shot choice"],
  "20-clean-reproducibility": ["8 / 8", "226", "0"],
  "21-eight-week-evidence-timeline": ["W1", "W8", "Data + baseline", "Release audit"],
  "22-apple-container-facts": ["821.67 MiB / 1 GiB", "80.2%", "~909 MiB", "4 CPUs", "OK"],
  "23-per-class-f1": ["0.95", "1.00", "n="],
  "24-full-confusion-matrix": ["True", "Predicted", "0", "37", "Correct", "Error"],
};

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: "utf8", ...options });
  assert.equal(
    result.status,
    0,
    `${command} ${args.join(" ")} failed\nstdout:\n${result.stdout}\nstderr:\n${result.stderr}`,
  );
  return result.stdout;
}

function sipsMetadata(file) {
  const stdout = run("/usr/bin/sips", ["-g", "pixelWidth", "-g", "pixelHeight", "-g", "hasAlpha", file]);
  const width = Number(stdout.match(/pixelWidth:\s*(\d+)/)?.[1]);
  const height = Number(stdout.match(/pixelHeight:\s*(\d+)/)?.[1]);
  const hasAlpha = stdout.match(/hasAlpha:\s*(\w+)/)?.[1];
  return { width, height, hasAlpha };
}

function readJson(rel) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, rel), "utf8"));
}

function parseSvgXml(svg, slug) {
  const stack = [];
  const tagPattern = /<!--[\s\S]*?-->|<[^>]+>/g;
  let cursor = 0;
  for (const match of svg.matchAll(tagPattern)) {
    const between = svg.slice(cursor, match.index);
    assert.doesNotMatch(between, /[<>]/, `${slug} contains malformed XML text`);
    cursor = match.index + match[0].length;
    const token = match[0];
    if (token.startsWith("<!--") || token.startsWith("<?") || token.startsWith("<!")) continue;
    const parsed = token.match(/^<\s*(\/?)\s*([A-Za-z_][\w:.-]*)/);
    assert.ok(parsed, `${slug} contains an invalid XML tag: ${token}`);
    const [, closing, name] = parsed;
    if (closing) {
      assert.equal(stack.pop(), name, `${slug} closes <${name}> out of order`);
    } else if (!/\/\s*>$/.test(token)) {
      stack.push(name);
    }
  }
  assert.doesNotMatch(svg.slice(cursor), /[<>]/, `${slug} contains trailing malformed XML text`);
  assert.deepEqual(stack, [], `${slug} contains unclosed XML tags`);
}

function numericAttribute(tag, name, fallback = undefined) {
  const value = tag.match(new RegExp(`\\b${name}=(?:"([^"]+)"|'([^']+)')`, "i"));
  if (!value) return fallback;
  const parsed = Number(value[1] ?? value[2]);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function assertSvgBounds(svg, slug) {
  const viewBox = svg.match(/viewBox=(?:"([^"]+)"|'([^']+)')/i)?.slice(1).find(Boolean)?.split(/\s+/).map(Number);
  assert.ok(viewBox?.length === 4 && viewBox.every(Number.isFinite), `${slug} must have a numeric viewBox`);
  const [, , width, height] = viewBox;
  const tolerance = 1;
  for (const tag of svg.match(/<(?:text|rect|circle|line)\b[^>]*>/gi) || []) {
    const name = tag.match(/^<(\w+)/i)?.[1].toLowerCase();
    if (name === "text") {
      const x = numericAttribute(tag, "x");
      const y = numericAttribute(tag, "y");
      assert.ok(x >= -tolerance && x <= width + tolerance && y >= -tolerance && y <= height + tolerance, `${slug} text anchor is outside viewBox: ${tag}`);
    } else if (name === "rect") {
      const x = numericAttribute(tag, "x", 0);
      const y = numericAttribute(tag, "y", 0);
      const w = numericAttribute(tag, "width");
      const h = numericAttribute(tag, "height");
      assert.ok(x >= -tolerance && y >= -tolerance && x + w <= width + tolerance && y + h <= height + tolerance, `${slug} rect is outside viewBox: ${tag}`);
      if (/\bfill=/i.test(tag)) assert.ok(!(x === 0 && y === 0 && w >= width && h >= height), `${slug} must not include a full-canvas fill rectangle`);
    } else if (name === "circle") {
      const cx = numericAttribute(tag, "cx");
      const cy = numericAttribute(tag, "cy");
      const r = numericAttribute(tag, "r");
      assert.ok(cx - r >= -tolerance && cy - r >= -tolerance && cx + r <= width + tolerance && cy + r <= height + tolerance, `${slug} circle is outside viewBox: ${tag}`);
    } else {
      for (const [xName, yName] of [["x1", "y1"], ["x2", "y2"]]) {
        const x = numericAttribute(tag, xName);
        const y = numericAttribute(tag, yName);
        assert.ok(x >= -tolerance && x <= width + tolerance && y >= -tolerance && y <= height + tolerance, `${slug} line is outside viewBox: ${tag}`);
      }
    }
  }
  for (const points of svg.matchAll(/<polyline\b[^>]*\bpoints=(?:"([^"]+)"|'([^']+)')/gi)) {
    for (const pair of (points[1] ?? points[2]).trim().split(/\s+/)) {
      const [x, y] = pair.split(",").map(Number);
      assert.ok(x >= -tolerance && x <= width + tolerance && y >= -tolerance && y <= height + tolerance, `${slug} polyline point is outside viewBox: ${pair}`);
    }
  }
}

function humanize(key) {
  const text = key.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function svgAccentColors(svg) {
  return [...new Set(svg.match(/#[0-9A-Fa-f]{6}/g) || [])]
    .map((color) => color.toUpperCase())
    .filter((color) => accentColors.has(color));
}

function circleGeometry(tag) {
  return {
    cx: numericAttribute(tag, "cx"),
    cy: numericAttribute(tag, "cy"),
    radius: numericAttribute(tag, "r"),
    parameters: numericAttribute(tag, "data-parameters"),
  };
}

const stdout = run(process.execPath, [GENERATOR], {
  cwd: ROOT,
  env: {
    ...process.env,
    NODE_PATH: process.env.NODE_PATH || BUNDLED_NODE_MODULES,
    PRESENTATION_CHARTS_OUT: OUT,
  },
});
const statusLine = stdout.trim().split("\n").at(-1);
const status = JSON.parse(statusLine);
assert.equal(status.status, "completed");
assert.equal(status.chart_count, 24);
assert.equal(path.resolve(ROOT, status.output_dir), path.resolve(OUT));

const expectedOutputFiles = expectedSlugs.flatMap((slug) => [`${slug}.png`, `${slug}.svg`]).concat(["README.md", "_qa-contact-sheet.png"]).sort();
assert.deepEqual(fs.readdirSync(OUT).sort(), expectedOutputFiles, "generator must emit exactly the 24 SVG/PNG pairs, README, and contact sheet");

const grammarViolations = [];

for (const slug of expectedSlugs) {
  const svgPath = path.join(OUT, `${slug}.svg`);
  const pngPath = path.join(OUT, `${slug}.png`);
  assert.ok(fs.statSync(svgPath).size > 0, `${slug}.svg must be non-empty`);
  assert.ok(fs.statSync(pngPath).size > 0, `${slug}.png must be non-empty`);

  const svg = fs.readFileSync(svgPath, "utf8");
  parseSvgXml(svg, slug);
  assertSvgBounds(svg, slug);
  assert.match(svg, /^<svg[^>]+xmlns="http:\/\/www\.w3\.org\/2000\/svg"/);
  assert.doesNotMatch(svg, /[\u3400-\u9FFF]/u, `${slug} must use English labels`);

  if (slug === "20-clean-reproducibility") {
    const metricXs = [...svg.matchAll(/<text\b[^>]*\bx="([^"]+)"[^>]*\bfont-size="104"/g)]
      .map((match) => Number(match[1]));
    assert.equal(metricXs.length, 4, "chart 20 must retain four audit metrics");
    assert.ok(
      metricXs[1] - metricXs[0] >= 480 && metricXs[3] - metricXs[2] >= 480,
      "chart 20 metric columns need enough separation for five-second comprehension",
    );
  }

  const violations = [];
  if (/<title\b/i.test(svg)) violations.push("contains <title>");
  if (/<desc\b/i.test(svg)) violations.push("contains <desc>");
  if (/Source:/i.test(svg)) violations.push("contains Source:");
  if (svg.includes(oldChartTitles[slug])) violations.push("contains the old chart title");
  if (!/font-family="SF Pro Display, SF Pro Text, Helvetica Neue, Arial, sans-serif"/.test(svg)) {
    violations.push("does not use the editorial font stack");
  }
  const colors = new Set(svg.match(/#[0-9A-Fa-f]{6}/g) || []);
  for (const color of colors) {
    const normalized = color.toUpperCase();
    if (!approvedColors.has(normalized)) violations.push(`uses unapproved color ${color}`);
  }
  const accents = svgAccentColors(svg);
  if (accents.length > 3) violations.push(`uses ${accents.length} accent colors; three is the global maximum`);
  if (accents.length > 2 && !threeAccentCharts.has(slug)) violations.push(`uses ${accents.length} accent colors without an approved third category`);
  const circleTags = svg.match(/<circle\b[^>]*>/gi) || [];
  if (!circleAllowed.has(slug) && circleTags.length) violations.push("contains a disallowed circle");
  if (circleAllowed.has(slug)) {
    for (const tag of circleTags) {
      if (!/data-role="(?:quantitative-dot|quantitative-bubble|quantitative-legend)"/.test(tag)) violations.push(`contains an unclassified circle ${tag}`);
    }
  }
  if (!circleAllowed.has(slug)) {
    for (const tag of svg.match(/<rect\b[^>]*>/gi) || []) {
      const width = numericAttribute(tag, "width");
      const height = numericAttribute(tag, "height");
      const rx = numericAttribute(tag, "rx", 0);
      const ry = numericAttribute(tag, "ry", rx);
      const shortSide = Math.min(width, height);
      const longSide = Math.max(width, height);
      const nearSquare = longSide / shortSide <= 1.2;
      if (nearSquare && Math.max(rx, ry) >= shortSide / 2) violations.push(`contains a circle-equivalent rounded rect ${tag}`);
    }
  }
  const arcPaths = [...svg.matchAll(/<path\b[^>]*\bd=(?:"([^"]*)"|'([^']*)')/gi)].filter((match) => /[Aa]/.test(match[1] ?? match[2]));
  if (arcPaths.length) violations.push("contains a disallowed SVG arc command");
  for (const token of requiredDirectTokens[slug]) {
    if (!svg.includes(token)) violations.push(`is missing direct token ${token}`);
  }
  if (violations.length) grammarViolations.push(`${slug}: ${violations.join(", ")}`);

  const metadata = sipsMetadata(pngPath);
  assert.equal(metadata.width, 3200, `${slug}.png must be 3200 px wide`);
  assert.equal(metadata.hasAlpha, "yes", `${slug}.png must preserve alpha`);
}

assert.deepEqual(grammarViolations, [], `Editorial grammar violations:\n${grammarViolations.join("\n")}`);

const readme = fs.readFileSync(path.join(OUT, "README.md"), "utf8");
assert.match(readme, /fixed synthetic-input engineering observations, not general benchmarks/i);
assert.match(readme, /5-image \/ 15-question smoke study/i);
assert.match(readme, /LoRA\/QLoRA was not completed/i);
assert.match(readme, /non-causal relevance visualization/i);
assert.match(readme, /\| Slide use \|/);
const readmeAssetRows = readme.split("\n").filter((line) => /^\| \d{2}-/.test(line));
assert.equal(readmeAssetRows.length, 24, "README must contain one manifest row per chart");
for (const row of readmeAssetRows) {
  const columns = row.split("|").map((value) => value.trim());
  assert.ok(columns.at(-2), `README row lacks a slide-use suggestion: ${row}`);
}

const claimEvidence = readJson("outputs/plantvillage/week8_release/week8-rc1/claims.json");
const generatorSource = fs.readFileSync(GENERATOR, "utf8");
const overlap = claimEvidence.claim_results.find((claim) => claim.claim_id === "official_split_overlap")?.value;
assert.ok(overlap, "Week 8 claim evidence must include official_split_overlap");
assert.match(readme, new RegExp(`${overlap} overlapping`));
assert.match(readme, new RegExp(`frozen Week 8 RC snapshot: ${claimEvidence.counts.claims} numerical claims and ${claimEvidence.counts.boundaries} boundary claims`, "i"));
assert.match(generatorSource, /\$\{claimEvidence\.counts\.claims\} numerical claims and \$\{claimEvidence\.counts\.boundaries\} boundary claims/);

const splitSvg = fs.readFileSync(path.join(OUT, "03-split-and-overlap.svg"), "utf8");
const dataAuditReport = fs.readFileSync(path.join(ROOT, "reports/data_audit.md"), "utf8");
const imagePathOverlap = Number(dataAuditReport.match(/train\/test[^\n]*`image_path`[^\n]*?(\d+)/)?.[1]);
assert.ok(Number.isFinite(imagePathOverlap), "audited report must provide the train/test image_path overlap count");
assert.match(splitSvg, /Seed 42/);
assert.match(splitSvg, new RegExp(`${overlap}`));
assert.match(splitSvg, new RegExp(`>${imagePathOverlap}<\/text><text[^>]*>OVERLAPPING PATHS`));
assert.match(generatorSource, /const imagePathOverlapCount = Number\(dataAuditEvidence\.match/);
assert.doesNotMatch(splitSvg, /<circle\b|<path\b[^>]*\bd="[^"]*(?:^|[ ,])A[ ,]/);

const audit = readJson("outputs/plantvillage/audit.json");
const distributionSvg = fs.readFileSync(path.join(OUT, "04-class-distribution.svg"), "utf8");
for (const [rawName, count] of Object.entries(audit.class_counts)) {
  assert.ok(distributionSvg.includes(Number(count).toLocaleString("en-US")), `${rawName} count must be represented`);
  assert.ok(rawName.includes("___"), `${rawName} must contain a condition`);
}

const modelDefs = [["MobileNetV2", "baseline_mobilenet_v2_best_seed42"], ["ResNet18", "baseline_resnet18_seed42"], ["ResNet50", "baseline_resnet50_seed42"], ["EfficientNet-B0", "baseline_efficientnet_b0_seed42"], ["EfficientNetV2-S", "baseline_efficientnet_v2_s_seed42"]];
const qualitySvg = fs.readFileSync(path.join(OUT, "05-model-accuracy-f1.svg"), "utf8");
const efficiencySvg = fs.readFileSync(path.join(OUT, "06-model-efficiency-pareto.svg"), "utf8");
const latencySvg = fs.readFileSync(path.join(OUT, "07-model-latency.svg"), "utf8");
for (const [name, run] of modelDefs) {
  const metrics = readJson(`outputs/plantvillage/${run}/metrics.json`);
  assert.ok(qualitySvg.includes(name) && efficiencySvg.includes(name) && latencySvg.includes(name));
  assert.ok(qualitySvg.includes(`${(metrics.accuracy * 100).toFixed(2)}%`));
  assert.ok(qualitySvg.includes(`${(metrics.macro_f1 * 100).toFixed(2)}%`));
}
assert.match(generatorSource, /function bubbleRadius\(params\)/, "Chart 06 must define one shared bubbleRadius(params) scale");
assert.match(generatorSource, /bubbleRadius\(model\.params\)/, "Chart 06 plotted bubbles must use bubbleRadius(params)");
assert.ok((generatorSource.match(/bubbleRadius\(/g) || []).length >= 3, "Chart 06 legend and plotted bubbles must share bubbleRadius(params)");
const parameterCircles = (efficiencySvg.match(/<circle\b[^>]*\bdata-parameters="[^"]+"[^>]*>/g) || []).map(circleGeometry);
assert.equal(parameterCircles.length, modelDefs.length + 2, "Chart 06 must identify every plotted and legend bubble with its parameter count");
for (const expectedParameters of [5e6, 25e6]) {
  const legendBubble = parameterCircles.find((bubble) => bubble.parameters === expectedParameters);
  assert.ok(legendBubble, `Chart 06 must include the ${expectedParameters} parameter legend bubble`);
  assert.ok(Math.abs(legendBubble.radius - (18 + 28 * Math.sqrt(expectedParameters / 24e6))) < 1e-9, "Chart 06 legend radii must exactly follow the plotted quantitative scale");
}
assert.doesNotMatch(latencySvg, /<circle\b/, "latency bars must not use endpoint dots");

const darkTableSvg = fs.readFileSync(path.join(OUT, "10-ablation-duration.svg"), "utf8");
assert.doesNotMatch(darkTableSvg, /<rect[^>]+fill="#1D1D1F"[^>]+width="1[45]\d{2}"/);
assert.equal((darkTableSvg.match(/stroke="#E8E8ED"/g) || []).length, 10, "table must use ten open ruled rows");

const finalSvg = fs.readFileSync(path.join(OUT, "11-final-improvement.svg"), "utf8");
assert.doesNotMatch(finalSvg, /<circle\b|<title\b|<desc\b|Source:|Baseline to Final Candidate/);
assert.doesNotMatch(finalSvg, /<path\b[^>]*\bd="[^"]*(?:^|[ ,])A[ ,]/);
assert.match(finalSvg, /font-family="SF Pro Display, SF Pro Text, Helvetica Neue, Arial, sans-serif"/);
for (const token of ["ACCURACY", "98.30%", "99.53%", "+1.23 pp", "MACRO F1", "97.43%", "99.41%", "+1.98 pp"]) {
  assert.match(finalSvg, new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
}

const timingSvg = fs.readFileSync(path.join(OUT, "17-demo-timing-observations.svg"), "utf8");
const localTiming = readJson("outputs/plantvillage/week5_demo/local_e2e.json").timings_ms;
const containerTiming = readJson("outputs/plantvillage/week5_demo/container_e2e.json").timings_ms;
assert.match(timingSvg, new RegExp(`${localTiming.total_ms.toFixed(1)} ms`));
assert.match(timingSvg, new RegExp(`${containerTiming.total_ms.toFixed(1)} ms`));
assert.deepEqual(new Set(svgAccentColors(timingSvg)), new Set(["#0A84FF", "#32D7C4", "#FF6B5E"]), "Chart 17 must reserve accents for prediction, Grad-CAM, and other");
assert.match(generatorSource, /const colors = \[E\.track, E\.blue, E\.mint, E\.coral\]/, "Chart 17 preprocessing must use the neutral track color");

const vlmSvg = fs.readFileSync(path.join(OUT, "19-vlm-prompt-comparison.svg"), "utf8");
for (const name of ["Original", "Short", "Choice", "Few-shot choice"]) assert.match(vlmSvg, new RegExp(name));

const gradcamSvg = fs.readFileSync(path.join(OUT, "14-attention-review.svg"), "utf8");

const attention = readJson("outputs/plantvillage/week4_explainability/attention_review.json");
assert.equal(svgAccentColors(gradcamSvg).length, 3, "Chart 14 must use exactly three accents plus a neutral fourth category");
assert.match(generatorSource, /const colors = \[E\.violet, E\.blue, E\.mint, E\.track\]/, "Chart 14 fourth category must use the neutral track color");
for (const [key, value] of Object.entries(attention.summary.attention_region_counts)) {
  assert.match(gradcamSvg, new RegExp(`${humanize(key)} ${value}`));
}
for (const [key, value] of Object.entries(attention.summary.error_type_counts).filter(([key]) => key !== "not_error")) {
  assert.match(gradcamSvg, new RegExp(`${humanize(key)} ${value}`));
}

const calibrationSvg = fs.readFileSync(path.join(OUT, "15-calibration.svg"), "utf8");
const calibrationDots = (calibrationSvg.match(/<circle\b[^>]*data-role="quantitative-dot"[^>]*>/g) || []).map(circleGeometry);
assert.ok(calibrationDots.length > 1, "Chart 15 must include reliability dots");
assert.equal(new Set(calibrationDots.map((dot) => dot.radius)).size, 1, "Chart 15 dots must have one fixed radius");
for (let index = 0; index < calibrationDots.length; index += 1) {
  for (let other = index + 1; other < calibrationDots.length; other += 1) {
    const left = calibrationDots[index], right = calibrationDots[other];
    const distance = Math.hypot(left.cx - right.cx, left.cy - right.cy);
    assert.ok(distance > left.radius + right.radius, `Chart 15 dots ${index} and ${other} must not touch`);
  }
}
assert.ok(svgAccentColors(calibrationSvg).length <= 2, "Chart 15 must use at most two accents");
assert.doesNotMatch(generatorSource, /Math\.sqrt\(bin\.count/, "Chart 15 must not encode undocumented bin counts in dot size");

const vqa = readJson("outputs/plantvillage/week6_vlm/vqa_seed_summary.json");
const vqaSvg = fs.readFileSync(path.join(OUT, "18-vqa-seed-composition.svg"), "utf8");
const questionTypeCount = Object.keys(vqa.question_type_counts).length;
assert.match(vqaSvg, new RegExp(`>${questionTypeCount}<\/text><text[^>]*>QUESTION TYPES`));
assert.match(generatorSource, /Object\.keys\(vqa\.question_type_counts\)\.length/);
for (const [key, value] of Object.entries(vqa.split_counts)) {
  assert.match(vqaSvg, new RegExp(`${humanize(key)} ${value}`));
}
for (const [key, value] of Object.entries(vqa.question_type_counts)) {
  assert.match(vqaSvg, new RegExp(`${humanize(key)} ${value}`));
}

const cleanRepro = readJson("outputs/plantvillage/week8_release/week8-rc1/clean_repro.json");
const pytest = cleanRepro.commands.find((command) => command.name === "pytest");
const cleanTests = pytest.stdout.match(/(\d+) passed/)?.[1];
const cleanSvg = fs.readFileSync(path.join(OUT, "20-clean-reproducibility.svg"), "utf8");
for (const token of [cleanTests, "BROKEN LINKS", `${claimEvidence.counts.broken_links}`, "NUMERICAL CLAIMS", `${claimEvidence.counts.claims}`, "BOUNDARY CLAIMS", `${claimEvidence.counts.boundaries}`]) {
  assert.ok(cleanSvg.includes(token));
}

const finalMetrics = readJson("outputs/plantvillage/week3_ablation/09_combo_candidate_seed42/metrics.json");
const errorAudit = readJson("outputs/plantvillage/week4_explainability/error_analysis.json");
const errorSvg = fs.readFileSync(path.join(OUT, "12-error-audit.svg"), "utf8");
assert.match(errorSvg, new RegExp(`>${errorAudit.summary.error_count}<`));
assert.match(errorSvg, new RegExp(`${(errorAudit.summary.accuracy * 100).toFixed(2)}%`));
assert.match(errorSvg, new RegExp(`>${errorAudit.summary.high_confidence_threshold.toFixed(2)}<`));
assert.doesNotMatch(generatorSource, /const C\s*=|segmentedRing|arcPath|function frame\(/);
const perClassSvg = fs.readFileSync(path.join(OUT, "23-per-class-f1.svg"), "utf8");
for (const metrics of Object.values(finalMetrics.per_class)) {
  assert.match(perClassSvg, new RegExp(`${metrics.f1.toFixed(3)} · n=${metrics.support}`));
}

const timelineSvg = fs.readFileSync(path.join(OUT, "21-eight-week-evidence-timeline.svg"), "utf8");
assert.match(timelineSvg, /<path[^>]+id="timeline-path"|<path[^>]+id='timeline-path'/);
assert.equal((timelineSvg.match(/class="timeline-node"/g) || []).length, 8, "timeline must contain eight sequential nodes");
assert.equal((timelineSvg.match(/id="timeline-path"/g) || []).length, 1, "timeline must use one restrained connecting path");
assert.deepEqual(
  [...timelineSvg.matchAll(/class="timeline-node" data-week="(W\d)"/g)].map((match) => match[1]),
  ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
  "timeline nodes must remain sequential",
);
const timelineMarkers = timelineSvg.match(/<rect\b[^>]*data-role="timeline-marker"[^>]*>/g) || [];
assert.equal(timelineMarkers.length, 8, "timeline must contain eight restrained markers");
for (const marker of timelineMarkers) {
  assert.ok(numericAttribute(marker, "width") <= 24 && numericAttribute(marker, "height") <= 24, `timeline marker is too dominant: ${marker}`);
}
const timelineActions = timelineSvg.match(/<text\b[^>]*data-role="timeline-action"[^>]*>/g) || [];
assert.equal(timelineActions.length, 8, "timeline must contain eight action labels");
for (const action of timelineActions) assert.ok(numericAttribute(action, "font-size") >= 20, `timeline action label is too small: ${action}`);

const matrixSvg = fs.readFileSync(path.join(OUT, "24-full-confusion-matrix.svg"), "utf8");
assert.ok((matrixSvg.match(/fill="#0A84FF"/g) || []).length >= 38, "matrix must encode its full diagonal");
assert.doesNotMatch(matrixSvg, /<circle\b/, "matrix legend and key must use square swatches");
assert.ok(matrixSvg.includes(">37<"), "matrix must include class index 37");

const contactSheet = sipsMetadata(path.join(OUT, "_qa-contact-sheet.png"));
assert.ok(contactSheet.width > 0 && contactSheet.height > 0, "contact sheet must be a readable PNG");

console.log(JSON.stringify({ status: "validated", chart_count: expectedSlugs.length, svg_pairs: 24, png_pairs: 24, all_width_3200: true, all_alpha: true, output_dir: OUT }));
