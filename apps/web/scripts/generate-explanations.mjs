#!/usr/bin/env node

/**
 * Reads controlled_vocabularies.v2.json and generates
 * apps/web/src/lib/explanations.ts — the single derived file
 * that the frontend uses for all tooltip / label descriptions.
 *
 * Run:  node scripts/generate-explanations.mjs
 * Or:   npm run generate:explanations
 */

import { readFileSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const VOCAB_PATH = resolve(__dirname, "../../../schemas/canonical/controlled_vocabularies.v2.json");
const OUT_PATH = resolve(__dirname, "../src/lib/explanations.ts");

const vocab = JSON.parse(readFileSync(VOCAB_PATH, "utf-8"));

const lines = [
  "// AUTO-GENERATED from schemas/canonical/controlled_vocabularies.v2.json",
  "// Do not edit by hand — run: npm run generate:explanations",
  "",
];

function emitRecord(exportName, keyType, described) {
  lines.push(`export const ${exportName}: Record<${keyType}, string> = {`);
  for (const [key, entry] of Object.entries(described)) {
    const escaped = entry.description.replace(/"/g, '\\"');
    lines.push(`  ${JSON.stringify(key)}: "${escaped}",`);
  }
  lines.push("};");
  lines.push("");
}

function emitLabelRecord(exportName, keyType, described) {
  lines.push(`export const ${exportName}: Record<${keyType}, string> = {`);
  for (const [key, entry] of Object.entries(described)) {
    lines.push(`  ${JSON.stringify(key)}: ${JSON.stringify(entry.label)},`);
  }
  lines.push("};");
  lines.push("");
}

// Vocabularies with enum types defined in types.ts
emitRecord("ITEM_TYPE_DESCRIPTIONS", "string", vocab.item_types.described);
emitRecord("STATUS_DESCRIPTIONS", "string", vocab.item_statuses.described);
emitRecord("MATURITY_DESCRIPTIONS", "string", vocab.maturity_stages.described);
emitRecord("SOURCE_TYPE_DESCRIPTIONS", "string", vocab.source_types.described);
emitRecord("CLAIM_POLARITY_DESCRIPTIONS", "string", vocab.claim_polarities.described);
emitRecord("CITATION_ROLE_DESCRIPTIONS", "string", vocab.citation_roles.described);
emitRecord("BIO_SYSTEM_DESCRIPTIONS", "string", vocab.biological_system_levels.described);
emitRecord("OBSERVATION_TYPE_DESCRIPTIONS", "string", vocab.observation_types.described);
emitRecord("SUCCESS_OUTCOME_DESCRIPTIONS", "string", vocab.success_outcomes.described);
emitRecord("WORKFLOW_FAMILY_DESCRIPTIONS", "string", vocab.workflow_families.described);
emitRecord("STEP_TYPE_DESCRIPTIONS", "string", vocab.workflow_step_types.described);
emitRecord("METRIC_DESCRIPTIONS", "string", vocab.common_metric_names.described);
emitRecord("MECHANISM_DESCRIPTIONS", "string", vocab.mechanism_families.described);
emitRecord("TECHNIQUE_DESCRIPTIONS", "string", vocab.technique_families.described);
emitRecord("TARGET_PROCESS_DESCRIPTIONS", "string", vocab.target_processes.described);
emitRecord("MODALITY_DESCRIPTIONS", "string", vocab.modalities.described);

// Score definitions and validation rollup (not standard enum vocabs)
emitRecord("SCORE_DESCRIPTIONS", "string", vocab.score_definitions.described);
emitRecord("VALIDATION_ROLLUP_DESCRIPTIONS", "string", vocab.validation_rollup_fields.described);
emitRecord("PROBLEM_LINK_DESCRIPTIONS", "string", vocab.problem_link_breakdown_keys.described);

writeFileSync(OUT_PATH, lines.join("\n") + "\n", "utf-8");

console.log(`✓ Generated ${OUT_PATH}`);
