#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { mapping } from "./update_presentation_chart_map.mjs";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "..");
const outlinePath = path.join(
  repoRoot,
  "docs/presentation/plantdisease_ai_complete_bilingual_outline.md",
);
const chartDir = path.join(
  repoRoot,
  "docs/presentation/charts/english-transparent",
);

const expected = [
  ...Array.from({ length: 33 }, (_, index) => `Slide ${index + 1}`),
  ...Array.from({ length: 12 }, (_, index) => `Appendix A${index + 1}`),
];

const startMarker = "<!-- GENERATED-CHART-REFS:START -->";
const endMarker = "<!-- GENERATED-CHART-REFS:END -->";
const contextHeading = "**图表限定 / Chart context**";
const sectionHeadingPattern = /^## (Slide \d+|Appendix A\d+)｜[^\n]*$/gm;

const requiredContextLines = {
  classifier: "Seed 42 · official split · 227 overlapping `leaf_id` values.",
  timing: "Fixed-example engineering observation; not a latency benchmark.",
  vlm: "5 images / 15 questions smoke study; no completed LoRA/QLoRA.",
  gradcam: "Non-causal relevance visualization.",
  clean: "Frozen RC snapshot; the current worktree audit may contain later claims.",
};

const requiredContextsByChart = {
  "01-project-evidence-snapshot": ["classifier"],
  "03-split-and-overlap": ["classifier"],
  "05-model-accuracy-f1": ["classifier"],
  "06-model-efficiency-pareto": ["timing"],
  "07-model-latency": ["timing"],
  "08-ablation-macro-f1": ["classifier"],
  "09-ablation-delta": ["classifier"],
  "11-final-improvement": ["classifier"],
  "12-error-audit": ["classifier"],
  "13-top-confusions": ["classifier"],
  "14-attention-review": ["classifier", "gradcam"],
  "15-calibration": ["classifier"],
  "16-gradcam-reproducibility": ["gradcam"],
  "17-demo-timing-observations": ["timing"],
  "18-vqa-seed-composition": ["vlm"],
  "19-vlm-prompt-comparison": ["vlm"],
  "20-clean-reproducibility": ["clean"],
  "23-per-class-f1": ["classifier"],
  "24-full-confusion-matrix": ["classifier"],
};

function count(text, needle) {
  return text.split(needle).length - 1;
}

function extractSections(markdown) {
  const matches = [...markdown.matchAll(sectionHeadingPattern)];
  const sections = new Map();
  for (let index = 0; index < matches.length; index += 1) {
    const match = matches[index];
    const end = matches[index + 1]?.index ?? markdown.length;
    sections.set(match[1], markdown.slice(match.index, end));
  }
  return sections;
}

function main() {
  const markdown = fs.readFileSync(outlinePath, "utf8");
  const sections = extractSections(markdown);
  const failures = [];
  const sectionIds = [...markdown.matchAll(sectionHeadingPattern)].map(
    (match) => match[1],
  );

  if (JSON.stringify(Object.keys(mapping)) !== JSON.stringify(expected)) {
    failures.push("updater mapping keys do not exactly match the approved 45-section order");
  }
  if (sectionIds.length !== expected.length) {
    failures.push(
      `expected ${expected.length} mapped section headings, found ${sectionIds.length}`,
    );
  }

  if (count(markdown, startMarker) !== expected.length) {
    failures.push(
      `expected ${expected.length} start markers, found ${count(markdown, startMarker)}`,
    );
  }
  if (count(markdown, endMarker) !== expected.length) {
    failures.push(
      `expected ${expected.length} end markers, found ${count(markdown, endMarker)}`,
    );
  }

  for (const sectionId of expected) {
    const occurrences = sectionIds.filter((candidate) => candidate === sectionId).length;
    if (occurrences !== 1) {
      failures.push(`${sectionId}: expected one section heading, found ${occurrences}`);
    }
    const section = sections.get(sectionId);
    if (!section) {
      failures.push(`${sectionId}: section heading is missing`);
      continue;
    }

    if (count(section, startMarker) !== 1 || count(section, endMarker) !== 1) {
      failures.push(`${sectionId}: expected exactly one generated marker pair`);
      continue;
    }

    const block = section.slice(
      section.indexOf(startMarker),
      section.indexOf(endMarker) + endMarker.length,
    );
    const evidenceHeading = /\n\*\*[^\n]*(?:Evidence|evidence|证据)[^\n]*\*\*/.exec(
      section,
    );
    if (evidenceHeading) {
      const between = section.slice(
        section.indexOf(endMarker) + endMarker.length,
        evidenceHeading.index + 1,
      );
      if (between.trim() !== "") {
        failures.push(`${sectionId}: generated block is not immediately before evidence`);
      }
    }
    if (!block.includes(contextHeading)) {
      failures.push(`${sectionId}: required bilingual chart-context heading is missing`);
    }

    const pngMatches = [
      ...block.matchAll(
        /\[PNG\]\(charts\/english-transparent\/([a-z0-9-]+)\.png\)/g,
      ),
    ];
    if (pngMatches.length === 0) {
      failures.push(`${sectionId}: no generated PNG reference found`);
      continue;
    }

    const actualSlugs = pngMatches.map((match) => match[1]);
    const expectedSlugs = mapping[sectionId].charts;
    if (JSON.stringify(actualSlugs) !== JSON.stringify(expectedSlugs)) {
      failures.push(
        `${sectionId}: chart mapping differs; expected ${expectedSlugs.join(", ")}, found ${actualSlugs.join(", ")}`,
      );
    }

    const contextBody = block
      .slice(block.indexOf(contextHeading) + contextHeading.length)
      .replace(endMarker, "")
      .trim();
    const actualContexts = contextBody
      ? contextBody.split("\n").map((line) => line.replace(/^- /, ""))
      : [];
    const expectedContexts = mapping[sectionId].contexts.map(
      (context) => requiredContextLines[context],
    );
    if (JSON.stringify(actualContexts) !== JSON.stringify(expectedContexts)) {
      failures.push(
        `${sectionId}: context lines differ; expected ${expectedContexts.length}, found ${actualContexts.length}`,
      );
    }

    const requiredContextKeys = new Set(
      actualSlugs.flatMap((slug) => requiredContextsByChart[slug] ?? []),
    );
    for (const contextKey of requiredContextKeys) {
      const requiredLine = requiredContextLines[contextKey];
      if (!actualContexts.includes(requiredLine)) {
        failures.push(
          `${sectionId}: ${actualSlugs.join(", ")} requires ${contextKey} context`,
        );
      }
    }

    for (const [, slug] of pngMatches) {
      const svgReference = `[SVG](charts/english-transparent/${slug}.svg)`;
      if (!block.includes(svgReference)) {
        failures.push(`${sectionId}: ${slug}.png has no sibling SVG reference`);
      }
      for (const extension of ["png", "svg"]) {
        const assetPath = path.join(chartDir, `${slug}.${extension}`);
        if (!fs.existsSync(assetPath)) {
          failures.push(`${sectionId}: referenced file does not exist: ${slug}.${extension}`);
        }
      }
    }
  }

  const unexpected = [...sections.keys()].filter(
    (sectionId) => !expected.includes(sectionId),
  );
  if (unexpected.length > 0) {
    failures.push(`unexpected slide sections: ${unexpected.join(", ")}`);
  }

  if (failures.length > 0) {
    console.error(`Slide-map validation failed (${failures.length} issue(s)):`);
    for (const failure of failures) console.error(`- ${failure}`);
    process.exitCode = 1;
    return;
  }

  console.log(
    "Slide-map validation passed: 45/45 sections mapped, 0 duplicate marker blocks, 0 missing PNG/SVG pairs, 0 broken chart links.",
  );
}

main();
