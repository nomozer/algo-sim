#!/usr/bin/env node
/**
 * Retired CLI guard for the former Live Classroom acceptance script.
 *
 * Under V1 Option B (Classroom / Live Session permanently retired from HTTP and UI),
 * this script fails closed with exit code 2 (CLASSROOM_FEATURE_RETIRED) while
 * leaving all database state and frozen evaluation artifacts untouched.
 */

const PAYLOAD = {
  status: "CLASSROOM_FEATURE_RETIRED",
  decision: "Option B",
  reason: "Classroom and Live Session HTTP routes and UI views are permanently retired in V1.",
  preserved_legacy_tables: [
    "classrooms",
    "class_memberships",
    "assignments",
    "practice_sessions",
    "classroom_sessions",
  ],
  historical_evidence_note:
    "Frozen historical classroom acceptance artifacts under docs/evaluation/geometry/ remain read-only.",
  exit_code: 2,
};

function printHelp() {
  process.stdout.write(
    [
      "Usage: node frontend/scripts/accept-live-classroom.mjs [--json] [--help]",
      "",
      "Retired under V1 Option B: Classroom and Live Session features are removed from V1 runtime.",
      "  --json   Print structured JSON status and exit with code 2 (CLASSROOM_FEATURE_RETIRED).",
      "  --help   Show this help message and exit with code 0.",
      "",
    ].join("\n"),
  );
}

function main(argv) {
  if (argv.includes("--help") || argv.includes("-h")) {
    printHelp();
    process.exit(0);
  }
  if (argv.includes("--json")) {
    process.stdout.write(`${JSON.stringify(PAYLOAD, null, 2)}\n`);
    process.exit(2);
  }
  process.stderr.write(
    `[CLASSROOM_FEATURE_RETIRED] ${PAYLOAD.reason} Returning exit code 2 without modifying DB or docs.\n`,
  );
  process.exit(2);
}

main(process.argv.slice(2));
