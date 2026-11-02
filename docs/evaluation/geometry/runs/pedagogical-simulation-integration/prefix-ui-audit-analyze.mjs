import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
const [, , src, out] = process.argv;
const raw = readFileSync(src);
const a = JSON.parse(raw);
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const val = (s) => (s.includes("=") ? s.slice(s.lastIndexOf("=") + 1) : s).trim();
const cases = a.results.map((r) => {
  const ans = [...new Set([...(r.mode_b_results || []).map(val), ...Object.values(r.answers || {}).map(val)])];
  const leaks = [];
  for (const v of ans) {
    const re = new RegExp(`(?:=|bằng|là)\\s*${esc(v)}(?![\\d.,/√π⁄²³])`, "u");
    for (const [s, t] of Object.entries(r.stages)) if (re.test(t)) leaks.push(`${s}:${v}`);
  }
  return {
    case_id: r.case_id, category: r.category, initial_step: r.initial_step, final_step: r.final_step, autoplay: r.autoplay,
    stage_observations: (r.observations || []).length + (r.observations_final || []).length,
    de_panel_is_submitted_text: (r.de_panel || "").trim() === r.problem_text.trim(), de_panel_text: (r.de_panel || "").trim(),
    mode_b_requested_results: r.mode_b_results || [], student_mode_answer_statements: leaks, error: r.error || null,
  };
});
const sum = (f) => cases.reduce((n, c) => n + f(c), 0);
const doc = {
  schema: "pedagogical-prefix-ui-audit/1",
  classification: "REAL_BROWSER_AND_UVICORN_STAGING_REPLAY_PRE_FIX",
  source_commit: "5abf8c20",
  live_provider_calls: 0,
  analyze_calls: a.analyzeCalls,
  page_or_console_errors: a.errors.length,
  cases_total: cases.length,
  stages: ["load", "steps (every Bước sau)", "steps_panel", "show_all", "quantities (every quantity inspector)",
    "tree_inspector (every component inspector)"],
  answer_statement_rule: "(=|bằng|là) <rendered Mode B value or oracle value> not followed by a digit, fraction, radical or π",
  raw_dom_dump_sha256: createHash("sha256").update(raw).digest("hex"),
  raw_dom_dump: "NOT_COMMITTED (session scratchpad)",
  summary: {
    answer_statements_in_student_mode: sum((c) => c.student_mode_answer_statements.length),
    autoplay: sum((c) => (c.autoplay ? 1 : 0)),
    opened_at_step_1: sum((c) => (/^Bước 1\//.test(c.initial_step || "") ? 1 : 0)),
    stage_observations: sum((c) => c.stage_observations),
    de_panel_is_submitted_text: sum((c) => (c.de_panel_is_submitted_text ? 1 : 0)),
    mode_b_shows_results: sum((c) => (c.mode_b_requested_results.length > 0 ? 1 : 0)),
  },
  cases,
};
writeFileSync(out, `${JSON.stringify(doc, null, 1)}\n`);
console.log(JSON.stringify(doc.summary));
