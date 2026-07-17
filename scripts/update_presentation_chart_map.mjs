#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const outlinePath = path.join(
  repoRoot,
  "docs/presentation/plantdisease_ai_complete_bilingual_outline.md",
);

export const mapping = {
  "Slide 1": { charts: ["01-project-evidence-snapshot"], contexts: ["classifier"] },
  "Slide 2": { charts: ["01-project-evidence-snapshot", "20-clean-reproducibility"], contexts: ["classifier", "clean"] },
  "Slide 3": { charts: ["03-split-and-overlap", "12-error-audit", "15-calibration"], contexts: ["classifier"] },
  "Slide 4": { charts: ["21-eight-week-evidence-timeline", "01-project-evidence-snapshot"], contexts: ["classifier"] },
  "Slide 5": { charts: ["21-eight-week-evidence-timeline"], contexts: [] },
  "Slide 6": { charts: ["02-dataset-composition", "04-class-distribution"], contexts: [] },
  "Slide 7": { charts: ["04-class-distribution", "02-dataset-composition"], contexts: [] },
  "Slide 8": { charts: ["03-split-and-overlap"], contexts: ["classifier"] },
  "Slide 9": { charts: ["02-dataset-composition", "18-vqa-seed-composition"], contexts: ["vlm"] },
  "Slide 10": { charts: ["20-clean-reproducibility", "03-split-and-overlap"], contexts: ["clean", "classifier"] },
  "Slide 11": { charts: ["05-model-accuracy-f1", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Slide 12": { charts: ["05-model-accuracy-f1"], contexts: ["classifier"] },
  "Slide 13": { charts: ["05-model-accuracy-f1", "06-model-efficiency-pareto", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Slide 14": { charts: ["06-model-efficiency-pareto", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Slide 15": { charts: ["08-ablation-macro-f1", "10-ablation-duration"], contexts: ["classifier"] },
  "Slide 16": { charts: ["09-ablation-delta", "08-ablation-macro-f1"], contexts: ["classifier"] },
  "Slide 17": { charts: ["09-ablation-delta", "10-ablation-duration"], contexts: ["classifier"] },
  "Slide 18": { charts: ["11-final-improvement"], contexts: ["classifier"] },
  "Slide 19": { charts: ["12-error-audit"], contexts: ["classifier"] },
  "Slide 20": { charts: ["13-top-confusions", "24-full-confusion-matrix"], contexts: ["classifier"] },
  "Slide 21": { charts: ["15-calibration"], contexts: ["classifier"] },
  "Slide 22": { charts: ["14-attention-review"], contexts: ["classifier", "gradcam"] },
  "Slide 23": { charts: ["16-gradcam-reproducibility", "14-attention-review"], contexts: ["classifier", "gradcam"] },
  "Slide 24": { charts: ["17-demo-timing-observations", "20-clean-reproducibility"], contexts: ["timing", "clean"] },
  "Slide 25": { charts: ["12-error-audit", "17-demo-timing-observations"], contexts: ["classifier", "timing"] },
  "Slide 26": { charts: ["22-apple-container-facts", "17-demo-timing-observations"], contexts: ["timing"] },
  "Slide 27": { charts: ["18-vqa-seed-composition", "21-eight-week-evidence-timeline"], contexts: ["vlm"] },
  "Slide 28": { charts: ["19-vlm-prompt-comparison"], contexts: ["vlm"] },
  "Slide 29": { charts: ["19-vlm-prompt-comparison"], contexts: ["vlm"] },
  "Slide 30": { charts: ["20-clean-reproducibility"], contexts: ["clean"] },
  "Slide 31": { charts: ["01-project-evidence-snapshot", "20-clean-reproducibility"], contexts: ["classifier", "clean"] },
  "Slide 32": { charts: ["03-split-and-overlap", "19-vlm-prompt-comparison", "22-apple-container-facts"], contexts: ["classifier", "vlm"] },
  "Slide 33": { charts: ["01-project-evidence-snapshot", "11-final-improvement"], contexts: ["classifier"] },
  "Appendix A1": { charts: ["04-class-distribution", "02-dataset-composition"], contexts: [] },
  "Appendix A2": { charts: ["02-dataset-composition", "03-split-and-overlap", "04-class-distribution"], contexts: ["classifier"] },
  "Appendix A3": { charts: ["11-final-improvement", "10-ablation-duration"], contexts: ["classifier"] },
  "Appendix A4": { charts: ["05-model-accuracy-f1", "06-model-efficiency-pareto", "07-model-latency"], contexts: ["classifier", "timing"] },
  "Appendix A5": { charts: ["06-model-efficiency-pareto", "07-model-latency", "17-demo-timing-observations"], contexts: ["timing"] },
  "Appendix A6": { charts: ["08-ablation-macro-f1", "09-ablation-delta", "10-ablation-duration"], contexts: ["classifier"] },
  "Appendix A7": { charts: ["23-per-class-f1", "13-top-confusions", "24-full-confusion-matrix"], contexts: ["classifier"] },
  "Appendix A8": { charts: ["15-calibration", "14-attention-review", "16-gradcam-reproducibility"], contexts: ["classifier", "gradcam"] },
  "Appendix A9": { charts: ["11-final-improvement", "12-error-audit"], contexts: ["classifier"] },
  "Appendix A10": { charts: ["19-vlm-prompt-comparison", "18-vqa-seed-composition"], contexts: ["vlm"] },
  "Appendix A11": { charts: ["20-clean-reproducibility"], contexts: ["clean"] },
  "Appendix A12": { charts: ["20-clean-reproducibility", "03-split-and-overlap", "19-vlm-prompt-comparison"], contexts: ["clean", "classifier", "vlm"] },
};

export const contextLines = {
  classifier: "Seed 42 · official split · 227 overlapping `leaf_id` values.",
  timing: "Fixed-example engineering observation; not a latency benchmark.",
  vlm: "5 images / 15 questions smoke study; no completed LoRA/QLoRA.",
  gradcam: "Non-causal relevance visualization.",
  clean: "Frozen RC snapshot; the current worktree audit may contain later claims.",
};

const startMarker = "<!-- GENERATED-CHART-REFS:START -->";
const endMarker = "<!-- GENERATED-CHART-REFS:END -->";
const sectionHeadingPattern = /^## (Slide \d+|Appendix A\d+)｜[^\n]*$/gm;
const generatedBlockPattern = new RegExp(
  `\\n*${startMarker}[\\s\\S]*?${endMarker}\\n*`,
  "g",
);

function renderBlock({ charts, contexts }) {
  const chartReferences = charts
    .map(
      (slug) =>
        `- \`${slug}\`: [PNG](charts/english-transparent/${slug}.png) · [SVG](charts/english-transparent/${slug}.svg)`,
    )
    .join("\n");
  const qualifiers = contexts.map((context) => `- ${contextLines[context]}`).join("\n");

  return [
    startMarker,
    "**生成图表参考 / Generated chart reference**",
    "",
    chartReferences,
    "",
    "**图表限定 / Chart context**",
    "",
    qualifiers,
    endMarker,
  ].join("\n");
}

function insertionIndex(section) {
  const evidenceHeading = /\n\*\*[^\n]*(?:Evidence|evidence|证据)[^\n]*\*\*/.exec(section);
  if (evidenceHeading) return evidenceHeading.index + 1;

  const separatorIndex = section.lastIndexOf("\n---\n");
  return separatorIndex >= 0 ? separatorIndex + 1 : section.length;
}

function injectBlocks(markdown) {
  const withoutGeneratedBlocks = markdown.replace(generatedBlockPattern, "\n\n");
  const matches = [...withoutGeneratedBlocks.matchAll(sectionHeadingPattern)];
  const missing = Object.keys(mapping).filter(
    (sectionId) => !matches.some((match) => match[1] === sectionId),
  );
  if (missing.length > 0) {
    throw new Error(`Outline is missing mapped sections: ${missing.join(", ")}`);
  }

  let updated = withoutGeneratedBlocks;
  for (let index = matches.length - 1; index >= 0; index -= 1) {
    const match = matches[index];
    const entry = mapping[match[1]];
    if (!entry) continue;
    const end = matches[index + 1]?.index ?? withoutGeneratedBlocks.length;
    const section = withoutGeneratedBlocks.slice(match.index, end);
    const at = match.index + insertionIndex(section);
    const block = `${renderBlock(entry)}\n\n`;
    updated = `${updated.slice(0, at)}${block}${updated.slice(at)}`;
  }
  return updated;
}

function updateMasterIndex(markdown) {
  const before =
    "| Complete English chart kit / 完整英文图表包 | [24-chart SVG + transparent PNG index](charts/english-transparent/README.md) | 2, 5–8, 11–23, 26–28, 30–31, A1, A4–A8, A11–A12 |";
  const after =
    "| Complete English chart kit / 完整英文图表包 | [24-chart SVG + transparent PNG index](charts/english-transparent/README.md) | Slides 1–33; Appendices A1–A12 |";
  if (markdown.includes(after)) return markdown;
  if (!markdown.includes(before)) {
    throw new Error("Visual Asset Master Index chart-kit row did not match the expected source text.");
  }
  return markdown.replace(before, after);
}

function main() {
  const original = fs.readFileSync(outlinePath, "utf8");
  const updated = updateMasterIndex(injectBlocks(original));
  fs.writeFileSync(outlinePath, updated, "utf8");
  console.log(`Updated ${Object.keys(mapping).length} slide/appendix chart-reference blocks.`);
}

if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))
) {
  main();
}
