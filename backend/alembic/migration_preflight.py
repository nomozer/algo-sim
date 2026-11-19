# -*- coding: utf-8 -*-
"""Alembic schema-evolution preflight and destructive-operation guard.

Prevents silent, unapproved, or startup-triggered destructive schema migrations
(`DROP TABLE`, `DROP COLUMN`, `TRUNCATE`, `DELETE FROM`) and protects
unstamped populated databases (such as legacy SQLite/Postgres deployments
holding Classroom or account records) from unsafe automatic `alembic upgrade`.

IMPORTANT: Keep this file in `backend/alembic/` WITHOUT an `__init__.py` so it
never shadows the external `alembic` PyPI package on `sys.path`.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import sqlalchemy as sa
from alembic.config import Config
from alembic.script import ScriptDirectory

LEGACY_CLASSROOM_TABLES: tuple[str, ...] = (
    "classroom_sessions",
    "practice_sessions",
    "assignments",
    "class_memberships",
    "classrooms",
)
RETAINED_LEGACY_CLASSROOM_TABLES: frozenset[str] = frozenset(LEGACY_CLASSROOM_TABLES)

BLOCK_EXIT_CODE = 23

_DESTRUCTIVE_SQL_RX = re.compile(
    r"(?i)\b(DROP\s+TABLE|TRUNCATE(?:\s+TABLE)?|ALTER\s+TABLE\s+[`\"\w.]+\s+DROP\s+COLUMN|DELETE\s+FROM)\b(?:\s+(?:IF\s+EXISTS\s+)?)?[`\"\[]?([A-Za-z_][A-Za-z0-9_]*)"
)


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_attr_name(node: ast.Call) -> tuple[str | None, str | None]:
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        return func.value.id, func.attr
    return None, None


def _table_kw_or_arg(node: ast.Call, pos: int = 0) -> str | None:
    if len(node.args) > pos:
        val = _const_str(node.args[pos])
        if val:
            return val
    for kw in node.keywords:
        if kw.arg == "table_name":
            val = _const_str(kw.value)
            if val:
                return val
    return None


def _resolve_batch_tables(fn_node: ast.FunctionDef) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for sub in ast.walk(fn_node):
        if isinstance(sub, ast.With):
            for item in sub.items:
                ctx = item.context_expr
                var = item.optional_vars
                if isinstance(ctx, ast.Call) and isinstance(var, ast.Name):
                    obj, method = _call_attr_name(ctx)
                    if obj == "op" and method == "batch_alter_table":
                        tbl = _table_kw_or_arg(ctx, 0)
                        if tbl:
                            aliases[var.id] = tbl
    return aliases


def scan_revision_ast(py_path: Path, fn_name: str = "upgrade") -> list[dict[str, Any]]:
    """Inspect a revision module AST for potentially destructive operations in `fn_name`."""
    source = py_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(py_path))
    target_fn: ast.FunctionDef | None = None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            target_fn = node
            break
    if target_fn is None:
        return []

    batch_tables = _resolve_batch_tables(target_fn)
    findings: list[dict[str, Any]] = []

    for node in ast.walk(target_fn):
        if not isinstance(node, ast.Call):
            continue
        obj, method = _call_attr_name(node)
        if not method:
            continue

        if method == "drop_table" and obj in ("op", "batch_op", *batch_tables):
            tbl = _table_kw_or_arg(node, 0) or batch_tables.get(obj or "", "<unknown>")
            findings.append(
                {
                    "operation": "drop_table",
                    "table": tbl,
                    "column": None,
                    "line": getattr(node, "lineno", None),
                }
            )
        elif method == "drop_column" and obj in ("op", "batch_op", *batch_tables):
            if obj == "op":
                tbl = _table_kw_or_arg(node, 0) or "<unknown>"
                col = _const_str(node.args[1] if len(node.args) > 1 else None)
                if col is None:
                    for kw in node.keywords:
                        if kw.arg == "column_name":
                            col = _const_str(kw.value)
            else:
                tbl = batch_tables.get(obj or "", "<unknown>")
                col = _const_str(node.args[0] if node.args else None)
                if col is None:
                    for kw in node.keywords:
                        if kw.arg == "column_name":
                            col = _const_str(kw.value)
            findings.append(
                {
                    "operation": "drop_column",
                    "table": tbl,
                    "column": col,
                    "line": getattr(node, "lineno", None),
                }
            )
        elif method == "execute" and obj in ("op", "bind", "connection", "conn"):
            sql_text = _const_str(node.args[0] if node.args else None)
            if sql_text is None and node.args:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Call):
                    sql_text = _const_str(arg0.args[0] if arg0.args else None)
            if sql_text:
                for m in _DESTRUCTIVE_SQL_RX.finditer(sql_text):
                    findings.append(
                        {
                            "operation": "raw_sql_" + re.sub(r"\s+", "_", m.group(1).strip().lower()),
                            "table": m.group(2),
                            "column": None,
                            "line": getattr(node, "lineno", None),
                        }
                    )
    return findings


def _col_name_from_ast(call: ast.Call) -> str | None:
    if call.args:
        nm = _const_str(call.args[0])
        if nm:
            return nm
    for kw in call.keywords:
        if kw.arg == "name":
            nm = _const_str(kw.value)
            if nm:
                return nm
    return None


def scan_revision_creates(py_path: Path, fn_name: str = "upgrade") -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """Extract unconditional top-level `create_table` and `add_column` declarations from `fn_name`."""
    source = py_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(py_path))
    target_fn = next(
        (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == fn_name),
        None,
    )
    if target_fn is None:
        return {}, []

    created_tables: dict[str, list[str]] = {}
    added_columns: list[tuple[str, str]] = []

    for stmt in target_fn.body:
        if isinstance(stmt, ast.If):
            continue
        batch_aliases = _resolve_batch_tables(ast.FunctionDef(name="_s", args=target_fn.args, body=[stmt], decorator_list=[]))
        for sub in ast.walk(stmt):
            if not isinstance(sub, ast.Call):
                continue
            obj, method = _call_attr_name(sub)
            if not method:
                continue
            if obj == "op" and method == "create_table":
                tbl = _table_kw_or_arg(sub, 0)
                if tbl:
                    cols: list[str] = []
                    for arg in sub.args[1:]:
                        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute) and arg.func.attr == "Column":
                            cn = _col_name_from_ast(arg)
                            if cn:
                                cols.append(cn)
                    created_tables[tbl] = cols
            elif method == "add_column" and obj in ("op", "batch_op", *batch_aliases):
                if obj == "op" and len(sub.args) >= 2 and isinstance(sub.args[1], ast.Call):
                    tbl = _table_kw_or_arg(sub, 0)
                    cn = _col_name_from_ast(sub.args[1])
                    if tbl and cn:
                        added_columns.append((tbl, cn))
                elif obj != "op" and sub.args and isinstance(sub.args[0], ast.Call):
                    tbl = batch_aliases.get(obj or "")
                    cn = _col_name_from_ast(sub.args[0])
                    if tbl and cn:
                        added_columns.append((tbl, cn))

    return created_tables, added_columns


def _count_table_rows(connection: sa.Connection, existing_tables: set[str], table_name: str) -> int | None:
    if table_name not in existing_tables:
        return None
    quoted = connection.dialect.identifier_preparer.quote(table_name)
    return int(connection.execute(sa.text(f"SELECT COUNT(*) FROM {quoted}")).scalar_one())


def _parse_allowed_revisions(raw: str) -> set[str]:
    return {item.strip() for item in (raw or "").split(",") if item.strip()}


def evaluate_migration_safety(
    connection: sa.Connection,
    alembic_cfg: Config,
    *,
    direction: str = "upgrade",
    target_rev: str = "head",
    startup_mode: bool = False,
    guard_destructive_downgrade: bool = False,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Evaluate whether the requested Alembic transition is data-safe and authorized."""
    env_map = os.environ if env is None else env
    effective_startup = bool(startup_mode or env_map.get("ALGOSIM_STARTUP_MODE", "") == "1")
    effective_guard_down = bool(
        guard_destructive_downgrade or env_map.get("ALGOSIM_GUARD_DESTRUCTIVE_DOWNGRADE", "") == "1"
    )
    backup_verified = env_map.get("ALGOSIM_BACKUP_VERIFIED", "") == "1"
    approved_revs = _parse_allowed_revisions(env_map.get("ALGOSIM_ALLOW_DESTRUCTIVE_MIGRATION", ""))

    script_dir = ScriptDirectory.from_config(alembic_cfg)
    heads = list(script_dir.get_heads())
    all_revs = {rev.revision for rev in script_dir.walk_revisions()}

    insp = sa.inspect(connection)
    user_tables = sorted(t for t in insp.get_table_names() if t != "sqlite_sequence")
    non_alembic_tables = [t for t in user_tables if t != "alembic_version"]
    existing_set = set(user_tables)

    db_revs: list[str] = []
    if "alembic_version" in existing_set:
        db_revs = [str(r[0]) for r in connection.execute(sa.text("SELECT version_num FROM alembic_version")).fetchall()]

    base_report: dict[str, Any] = {
        "dialect": connection.dialect.name,
        "direction": direction,
        "target_rev": target_rev,
        "startup_mode": effective_startup,
        "db_revisions": db_revs,
        "script_heads": heads,
        "user_tables_count": len(non_alembic_tables),
        "destructive_operations": [],
        "retained_legacy_tables_present": sorted(t for t in RETAINED_LEGACY_CLASSROOM_TABLES if t in existing_set),
    }

    if direction == "downgrade" and effective_startup:
        return {
            **base_report,
            "allowed": False,
            "reason_code": "DOWNGRADE_FORBIDDEN_AT_STARTUP",
            "message": "Schema downgrade is forbidden while ALGOSIM_STARTUP_MODE=1 is active.",
        }

    if len(heads) != 1:
        return {
            **base_report,
            "allowed": False,
            "reason_code": "MULTIPLE_SCRIPT_HEADS" if len(heads) > 1 else "NO_SCRIPT_HEADS",
            "message": f"Expected exactly 1 Alembic head revision, found {heads}.",
        }

    if len(db_revs) > 1:
        return {
            **base_report,
            "allowed": False,
            "reason_code": "MULTIPLE_DB_REVISIONS",
            "message": f"Database contains multiple alembic_version rows: {db_revs}.",
        }

    # Pre-Alembic populated database protection (e.g. dev/prod DBs created via SQLAlchemy create_all)
    if not db_revs and non_alembic_tables:
        counts = {t: _count_table_rows(connection, existing_set, t) for t in non_alembic_tables}
        return {
            **base_report,
            "allowed": False,
            "reason_code": "UNSTAMPED_EXISTING_DATABASE",
            "existing_table_row_counts": counts,
            "message": (
                "Existing non-empty schema has no alembic_version stamp. Refusing automatic "
                "alembic upgrade/stamp; back up database, inspect schema parity against migrations, "
                "and migrate under explicit operator control."
            ),
        }

    if "alembic_version" in existing_set and not db_revs and not non_alembic_tables:
        return {
            **base_report,
            "allowed": False,
            "reason_code": "EMPTY_ALEMBIC_VERSION_TABLE",
            "message": (
                "Database contains an empty alembic_version table with no revision row and no application tables. "
                "Inspect partial/aborted migration state before continuing."
            ),
        }

    current_rev = db_revs[0] if db_revs else None
    if current_rev is not None and current_rev not in all_revs:
        return {
            **base_report,
            "allowed": False,
            "reason_code": "UNKNOWN_DB_REVISION",
            "message": f"Database revision {current_rev!r} is not present in source Alembic script chain.",
        }

    if direction == "upgrade":
        steps = script_dir._upgrade_revs(target_rev, current_rev)
        fn_name = "upgrade"
    elif direction == "downgrade":
        steps = script_dir._downgrade_revs(target_rev, current_rev)
        fn_name = "downgrade"
    else:
        return {
            **base_report,
            "allowed": False,
            "reason_code": "INVALID_MIGRATION_DIRECTION",
            "message": f"Unsupported migration direction: {direction!r}.",
        }

    planned_revs = [step.revision.revision for step in steps]
    destructive_ops: list[dict[str, Any]] = []
    for step in steps:
        rev_script = step.revision
        hits = scan_revision_ast(Path(rev_script.path), fn_name=fn_name)
        for hit in hits:
            row_cnt = _count_table_rows(connection, existing_set, hit["table"])
            destructive_ops.append(
                {
                    "revision": rev_script.revision,
                    "script": Path(rev_script.path).name,
                    "direction": direction,
                    "live_row_count": row_cnt,
                    **hit,
                }
            )

    base_report["planned_revisions"] = planned_revs
    base_report["destructive_operations"] = destructive_ops

    if not destructive_ops:
        if direction == "upgrade":
            colliding_tables: list[str] = []
            colliding_columns: list[str] = []
            live_cols_cache: dict[str, set[str]] = {}
            for step in steps:
                ct_map, ac_list = scan_revision_creates(Path(step.revision.path), fn_name="upgrade")
                for tbl in ct_map:
                    if tbl in existing_set:
                        colliding_tables.append(tbl)
                for tbl, col in ac_list:
                    if tbl in existing_set:
                        if tbl not in live_cols_cache:
                            live_cols_cache[tbl] = {c["name"] for c in insp.get_columns(tbl)}
                        if col in live_cols_cache[tbl]:
                            colliding_columns.append(f"{tbl}.{col}")
            if colliding_tables or colliding_columns:
                return {
                    **base_report,
                    "allowed": False,
                    "reason_code": "PARTIAL_MIGRATION_PRE_EXISTING_OBJECT",
                    "colliding_tables": sorted(set(colliding_tables)),
                    "colliding_columns": sorted(set(colliding_columns)),
                    "message": (
                        "Pending non-destructive migration conflicts with pre-existing database tables/columns "
                        "(partial or interrupted prior migration state). Inspect and reconcile before executing DDL."
                    ),
                }

            if current_rev is not None:
                history_revs = list(reversed(list(script_dir.walk_revisions(base="base", head=current_rev))))
                expected_cols: dict[str, set[str]] = {}
                for hrev in history_revs:
                    h_path = Path(hrev.path)
                    ct_map, ac_list = scan_revision_creates(h_path, fn_name="upgrade")
                    for tbl, cols in ct_map.items():
                        expected_cols[tbl] = set(cols)
                    for tbl, col in ac_list:
                        expected_cols.setdefault(tbl, set()).add(col)
                    for hit in scan_revision_ast(h_path, fn_name="upgrade"):
                        if hit["operation"] == "drop_table":
                            expected_cols.pop(hit["table"], None)
                        elif hit["operation"] == "drop_column" and hit["column"] and hit["table"] in expected_cols:
                            expected_cols[hit["table"]].discard(hit["column"])

                f8_reached = any(r.revision == "f8a2c41d9e05" for r in history_revs)
                missing_tables: list[str] = []
                missing_columns: dict[str, list[str]] = {}
                unexpected_columns: dict[str, list[str]] = {}
                for tbl, exp_set in sorted(expected_cols.items()):
                    if tbl in RETAINED_LEGACY_CLASSROOM_TABLES and f8_reached and tbl not in existing_set:
                        continue
                    if tbl not in existing_set:
                        missing_tables.append(tbl)
                        continue
                    live_set = live_cols_cache.get(tbl)
                    if live_set is None:
                        live_set = {c["name"] for c in insp.get_columns(tbl)}
                        live_cols_cache[tbl] = live_set
                    miss_c = sorted(exp_set - live_set)
                    extra_c = sorted(live_set - exp_set)
                    if miss_c:
                        missing_columns[tbl] = miss_c
                    if extra_c:
                        unexpected_columns[tbl] = extra_c

                if missing_tables or missing_columns or unexpected_columns:
                    return {
                        **base_report,
                        "allowed": False,
                        "reason_code": "SCHEMA_DRIFT_DETECTED",
                        "drift_details": {
                            "missing_tables": missing_tables,
                            "missing_columns": missing_columns,
                            "unexpected_columns": unexpected_columns,
                        },
                        "message": (
                            f"Live schema drifted from Alembic history through revision {current_rev!r}: "
                            "missing tables/columns or unexpected columns detected."
                        ),
                    }

        return {
            **base_report,
            "allowed": True,
            "reason_code": "SAFE_NO_DESTRUCTIVE_OPERATIONS",
            "message": "Migration preflight passed cleanly with zero destructive operations.",
        }

    dest_rev_ids = {op_item["revision"] for op_item in destructive_ops}

    if direction == "upgrade":
        if effective_startup:
            return {
                **base_report,
                "allowed": False,
                "reason_code": "DESTRUCTIVE_MIGRATION_FORBIDDEN_AT_STARTUP",
                "message": (
                    f"Blocked destructive upgrade revision(s) {sorted(dest_rev_ids)} during container/app startup. "
                    "Automatic `alembic upgrade head` must never execute DROP/TRUNCATE/DELETE operations."
                ),
            }
        if not (backup_verified and dest_rev_ids <= approved_revs):
            return {
                **base_report,
                "allowed": False,
                "reason_code": "DESTRUCTIVE_UPGRADE_UNAPPROVED",
                "message": (
                    f"Blocked unapproved destructive upgrade revision(s) {sorted(dest_rev_ids)}. "
                    "Verify an independent backup restore and set ALGOSIM_BACKUP_VERIFIED=1 plus "
                    "ALGOSIM_ALLOW_DESTRUCTIVE_MIGRATION with approved revision IDs."
                ),
            }
        return {
            **base_report,
            "allowed": True,
            "reason_code": "DESTRUCTIVE_UPGRADE_APPROVED_WITH_BACKUP",
            "message": f"Destructive upgrade authorized for verified backup + approved revision(s) {sorted(dest_rev_ids)}.",
        }

    # direction == "downgrade"
    populated_legacy_hits = [
        op_item
        for op_item in destructive_ops
        if op_item["table"] in RETAINED_LEGACY_CLASSROOM_TABLES and (op_item["live_row_count"] or 0) > 0
    ]
    populated_any_hits = [op_item for op_item in destructive_ops if (op_item["live_row_count"] or 0) > 0]

    needs_approval = populated_legacy_hits or (effective_guard_down and populated_any_hits)
    if needs_approval and not (backup_verified and dest_rev_ids <= approved_revs):
        return {
            **base_report,
            "allowed": False,
            "reason_code": "DESTRUCTIVE_DOWNGRADE_DATA_LOSS_BLOCKED",
            "message": (
                f"Blocked destructive downgrade revision(s) {sorted(dest_rev_ids)} that would drop populated "
                "table(s). Verify backup restore and approve explicitly before proceeding."
            ),
        }

    return {
        **base_report,
        "allowed": True,
        "reason_code": "DOWNGRADE_SAFE_OR_APPROVED",
        "message": "Downgrade preflight passed.",
    }


def _default_alembic_cfg(alembic_ini: Path | None = None) -> Config:
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = alembic_ini or (backend_dir / "alembic.ini")
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(Path(__file__).resolve().parent))
    return cfg


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="migration_preflight.py",
        description="Verify Alembic migration safety before executing schema evolution.",
    )
    parser.add_argument("--alembic-ini", type=Path, default=None, help="Path to alembic.ini")
    parser.add_argument("--direction", choices=("upgrade", "downgrade"), default="upgrade")
    parser.add_argument("--target", default="head", help="Target Alembic revision (default: head)")
    parser.add_argument("--startup", action="store_true", help="Enforce strict application-startup policy")
    parser.add_argument(
        "--guard-downgrade",
        action="store_true",
        help="Block downgrades dropping any populated table without verified backup approval",
    )
    parser.add_argument("--json", action="store_true", help="Emit structured JSON report")
    args = parser.parse_args(argv)

    backend_dir = Path(__file__).resolve().parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    from app.persistence.db import DATABASE_URL, engine  # noqa: E402

    cfg = _default_alembic_cfg(args.alembic_ini)
    cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    with engine.connect() as conn:
        report = evaluate_migration_safety(
            conn,
            cfg,
            direction=args.direction,
            target_rev=args.target,
            startup_mode=args.startup,
            guard_destructive_downgrade=args.guard_downgrade,
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if report["allowed"] else "BLOCKED"
        print(f"MIGRATION_PREFLIGHT={status} reason={report['reason_code']} :: {report['message']}")

    return 0 if report["allowed"] else BLOCK_EXIT_CODE


if __name__ == "__main__":
    raise SystemExit(main())
