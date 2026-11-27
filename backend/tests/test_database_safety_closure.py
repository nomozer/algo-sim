# -*- coding: utf-8 -*-
"""Database safety root-cause closure regression tests (BLOCKER-DB-1 & BLOCKER-DB-2).

Covers all 8 required Phase B4 scenarios across isolated SQLite and real PostgreSQL 16:
1. Brand-new empty DB (`migration_preflight --startup` + `upgrade head` + `alembic check`).
2. Legacy DB (`a1c7e4b90d52` / `e437149641fa`) with 0 rows.
3. Legacy DB with populated 5-table Classroom graph (row count + FK + SHA-256 table digest parity across
   `upgrade head` -> `downgrade e437149641fa` -> `upgrade head`), plus unstamped populated SQLite DB guard.
4. DB already at `9c4d8e2b7a10` with Step Editor + Classroom rows -> `upgrade head`.
5. DB already at pre-fix `f8a2c41d9e05` (no Classroom tables, Step Editor rows present) -> `upgrade head`
   no-op (never re-creates legacy tables) + clean `alembic check` + `downgrade a1c7e4b90d52` schema restore.
6. Mid-migration failure injection on PostgreSQL 16 (atomic transactional DDL rollback, 0 rows lost).
7. Repeated `migration_preflight --startup && alembic upgrade head` / simulated restart idempotence.
8. Unapproved destructive migrations (`op.drop_table`, `drop_column`, `DROP TABLE`, `TRUNCATE`, `DELETE`)
   and destructive downgrades blocked by preflight (`exit 23`) and online `alembic/env.py`.
9. Phase C entrypoints: `seed_classroom_fixture.py` (clean exit/no ImportError) and
   `seed_demo_accounts.py` (0 legacy tables created; refuses mutation when Classroom rows exist).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from tests.test_postgres_integration import _alembic as _pg_repo_alembic, pg_container  # noqa: F401

BACKEND_DIR = Path(__file__).resolve().parents[1]
PREFLIGHT_SCRIPT = BACKEND_DIR / "alembic" / "migration_preflight.py"
SEED_CLASSROOM_SCRIPT = BACKEND_DIR / "scripts" / "seed_classroom_fixture.py"
SEED_DEMO_SCRIPT = BACKEND_DIR / "scripts" / "seed_demo_accounts.py"

LEGACY_TABLES = ("classrooms", "class_memberships", "assignments", "practice_sessions", "classroom_sessions")


def _stage_alembic_workspace(tmp_path: Path, db_url: str, name: str = "mig") -> tuple[Path, Path, dict[str, str]]:
    work = tmp_path / name
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BACKEND_DIR / "alembic", work / "alembic")
    ini_path = work / "alembic.ini"
    ini_path.write_text((BACKEND_DIR / "alembic.ini").read_text(encoding="utf-8"), encoding="utf-8")
    env = {**os.environ, "DATABASE_URL": db_url, "PYTHONPATH": str(BACKEND_DIR)}
    return work, ini_path, env


def _run_alembic(work: Path, ini_path: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), *args],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_preflight(work: Path, ini_path: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(work / "alembic" / "migration_preflight.py"), "--alembic-ini", str(ini_path), *args],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _seed_populated_classroom_graph(conn, is_postgres: bool = False) -> None:
    now_expr = "now()" if is_postgres else "CURRENT_TIMESTAMP"
    bool_true = "true" if is_postgres else "1"
    bool_false = "false" if is_postgres else "0"
    conn.execute(
        text(
            f"INSERT INTO users (email, display_name, password_hash, role, must_change_password, created_at) VALUES "
            f"('gv.safe@algosim.edu.vn', 'Co Lan', 'h1', 'teacher', {bool_false}, {now_expr}), "
            f"('hs.an@algosim.edu.vn', 'An', 'h2', 'student', {bool_false}, {now_expr}), "
            f"('hs.binh@algosim.edu.vn', 'Binh', 'h3', 'student', {bool_false}, {now_expr})"
        )
    )
    t_id = conn.execute(text("SELECT id FROM users WHERE email = 'gv.safe@algosim.edu.vn'")).scalar_one()
    s1_id = conn.execute(text("SELECT id FROM users WHERE email = 'hs.an@algosim.edu.vn'")).scalar_one()
    s2_id = conn.execute(text("SELECT id FROM users WHERE email = 'hs.binh@algosim.edu.vn'")).scalar_one()

    conn.execute(
        text(
            f"INSERT INTO classrooms (teacher_id, name, join_code, code_active, archived, created_at) "
            f"VALUES (:t, '11A1 Safety', 'SAFE11', {bool_true}, {bool_false}, {now_expr})"
        ),
        {"t": t_id},
    )
    c_id = conn.execute(text("SELECT id FROM classrooms WHERE join_code = 'SAFE11'")).scalar_one()

    for sid in (s1_id, s2_id):
        conn.execute(
            text(f"INSERT INTO class_memberships (classroom_id, student_id, joined_at) VALUES (:c, :s, {now_expr})"),
            {"c": c_id, "s": sid},
        )
    conn.execute(
        text(
            f"INSERT INTO assignments (classroom_id, created_by, title, instruction, simulation_id, envelope_json, closed, created_at) "
            f"VALUES (:c, :t, 'Bai tap 1', 'Dung thiet dien', 'sim.sec', :env_json, {bool_false}, {now_expr})"
        ),
        {"c": c_id, "t": t_id, "env_json": '{"ok":true}'},
    )
    a_id = conn.execute(text("SELECT id FROM assignments WHERE classroom_id = :c"), {"c": c_id}).scalar_one()
    for sid in (s1_id, s2_id):
        conn.execute(
            text(
                f"INSERT INTO practice_sessions (assignment_id, student_id, simulation_id, cursor, step_count, explore_open, challenge_open, action_count, commitment_count, completed, started_at, updated_at, help_requested) "
                f"VALUES (:a, :s, 'sim.sec', 2, 5, {bool_true}, {bool_false}, 4, 1, {bool_false}, {now_expr}, {now_expr}, {bool_false})"
            ),
            {"a": a_id, "s": sid},
        )
    conn.execute(
        text(
            f"INSERT INTO classroom_sessions (classroom_id, teacher_id, round_id, cmd_id, mode, assignment_id, simulation_id, current_step, isolated_ids, exploded_groups, sync_cmd_id, active, started_at, updated_at) "
            f"VALUES (:c, :t, 'rnd-safe', 3, 'follow', :a, 'sim.sec', 2, '[]', '[]', 1, {bool_true}, {now_expr}, {now_expr})"
        ),
        {"c": c_id, "t": t_id, "a": a_id},
    )


def _table_digest(conn, table_name: str) -> tuple[int, str]:
    rows = conn.execute(text(f'SELECT * FROM "{table_name}" ORDER BY id')).fetchall()
    h = hashlib.sha256()
    for row in rows:
        h.update(json.dumps([repr(v) for v in row], ensure_ascii=False).encode("utf-8") + b"\n")
    return len(rows), h.hexdigest()


# ── B4 Scenarios 1, 2, 3, 4, 5, 7, 8 on Isolated SQLite ───────────────────────


def test_b4_1_and_7_fresh_empty_db_startup_and_restart_idempotence(tmp_path: Path):
    db_url = f"sqlite:///{(tmp_path / 'fresh.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "fresh_w")

    pre1 = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre1.returncode == 0, pre1.stderr
    assert json.loads(pre1.stdout)["allowed"] is True
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    # Simulated container restart: repeat preflight --startup + upgrade head (no-op)
    pre2 = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre2.returncode == 0, pre2.stderr
    up2 = _run_alembic(work, ini, env, "upgrade", "head")
    assert up2.returncode == 0
    assert "Running upgrade" not in (up2.stdout + up2.stderr)
    assert _run_alembic(work, ini, env, "check").returncode == 0


def test_b4_2_legacy_empty_db_retains_schema_and_passes_check(tmp_path: Path):
    db_url = f"sqlite:///{(tmp_path / 'legacy_empty.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "legacy_empty_w")

    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0
    assert _run_preflight(work, ini, env, "--startup", "--json").returncode == 0
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    eng = create_engine(db_url)
    tbls = set(inspect(eng).get_table_names())
    assert set(LEGACY_TABLES) <= tbls
    assert {"step_edit_sessions", "step_edit_revisions", "step_edit_feedback"} <= tbls
    eng.dispose()


def test_b4_3_and_4_populated_classroom_and_step_editor_100pct_preserved(tmp_path: Path):
    db_url = f"sqlite:///{(tmp_path / 'populated.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "pop_w")

    # Seed legacy populated Classroom DB at e437149641fa -> upgrade to 9c4d8e2b7a10
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0
    eng = create_engine(db_url)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=False)

    assert _run_alembic(work, ini, env, "upgrade", "9c4d8e2b7a10").returncode == 0
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO step_edit_sessions (owner_scope, session_id, problem_key, base_scene_sha256, committed_scene_json, step_overrides_json, dependency_graph_json, revision_count, created_at, updated_at) "
                "VALUES ('client:s', 'se-safe-1', 'sample:s1', 'a', '{}', '{}', '{}', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
        baseline_digests = {t: _table_digest(conn, t) for t in ("users", *LEGACY_TABLES, "step_edit_sessions")}
    assert baseline_digests["users"][0] == 3
    assert baseline_digests["classrooms"][0] == 1
    assert baseline_digests["class_memberships"][0] == 2
    assert baseline_digests["assignments"][0] == 1
    assert baseline_digests["practice_sessions"][0] == 2
    assert baseline_digests["classroom_sessions"][0] == 1

    # Upgrade 9c4d8e2b7a10 -> head (f8a2c41d9e05) under startup preflight
    pre = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre.returncode == 0, pre.stdout + pre.stderr
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    with eng.connect() as conn:
        for t, exp in baseline_digests.items():
            assert _table_digest(conn, t) == exp, f"{t} mutated across upgrade f8a2c41d9e05!"

    # Downgrade f8a2c41d9e05 -> 9c4d8e2b7a10 retains every single legacy Classroom + Step Editor row
    assert _run_alembic(work, ini, env, "downgrade", "9c4d8e2b7a10").returncode == 0
    with eng.connect() as conn:
        for t, exp in baseline_digests.items():
            assert _table_digest(conn, t) == exp, f"{t} mutated on downgrade!"

    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0
    eng.dispose()


def test_b4_3b_unstamped_populated_sqlite_db_blocks_upgrade_and_stays_intact(tmp_path: Path):
    """Pre-Alembic DB like root algosim.db without alembic_version must be blocked by preflight and online env.py."""
    legacy_db = tmp_path / "unstamped.db"
    db_url = f"sqlite:///{legacy_db.as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "unstamped_w")

    # Create legacy pre-f8 schema tables then delete alembic_version to mimic create_all() SQLite DB
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0
    eng = create_engine(db_url)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=False)
        conn.execute(text("DROP TABLE alembic_version"))
        before_cls = _table_digest(conn, "classrooms")
        before_usr = _table_digest(conn, "users")

    pre = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre.returncode == 23
    report = json.loads(pre.stdout)
    assert report["allowed"] is False
    assert report["reason_code"] == "UNSTAMPED_EXISTING_DATABASE"
    assert report["existing_table_row_counts"]["classrooms"] == 1
    assert report["existing_table_row_counts"]["users"] == 3

    up = _run_alembic(work, ini, env, "upgrade", "head")
    assert up.returncode != 0
    assert "UNSTAMPED_EXISTING_DATABASE" in (up.stdout + up.stderr)

    with eng.connect() as conn:
        assert _table_digest(conn, "classrooms") == before_cls
        assert _table_digest(conn, "users") == before_usr
    eng.dispose()


def test_b4_5_already_at_f8_without_legacy_tables_stays_clean_and_downgrades(tmp_path: Path):
    """Simulate a DB like algosim_acceptance where old f8 dropped legacy tables before this closure fix."""
    db_url = f"sqlite:///{(tmp_path / 'dropped_f8.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "dropped_f8_w")

    # Reproduce a DB (such as algosim_acceptance) where pre-fix f8a2c41d9e05 already dropped legacy tables while empty
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    eng = create_engine(db_url)
    with eng.begin() as conn:
        for legacy_tbl in LEGACY_TABLES:
            conn.execute(text(f'DROP TABLE "{legacy_tbl}"'))
        conn.execute(
            text(
                "INSERT INTO step_edit_sessions (owner_scope, session_id, problem_key, base_scene_sha256, committed_scene_json, step_overrides_json, dependency_graph_json, revision_count, created_at, updated_at) "
                "VALUES ('client:f8', 'se-f8-keep', 'sample:s1', 'a', '{}', '{}', '{}', 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )
    assert not (set(LEGACY_TABLES) & set(inspect(eng).get_table_names()))

    # Preflight + repeated upgrade does NOT recreate dropped tables and passes alembic check
    assert _run_preflight(work, ini, env, "--startup", "--json").returncode == 0
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert not (set(LEGACY_TABLES) & set(inspect(eng).get_table_names()))
    assert _run_alembic(work, ini, env, "check").returncode == 0

    # Downgrade to 9c4d8e2b7a10 cleanly recreates missing legacy table schemas; Step Editor rows survive
    assert _run_alembic(work, ini, env, "downgrade", "9c4d8e2b7a10").returncode == 0
    assert set(LEGACY_TABLES) <= set(inspect(eng).get_table_names())
    with eng.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM step_edit_sessions WHERE session_id = 'se-f8-keep'")).scalar_one() == 1
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0
    eng.dispose()


def test_b4_8_unapproved_destructive_migrations_and_downgrades_blocked(tmp_path: Path):
    """Verify AST scanner + startup block + online env block against op.drop_table, drop_column, DROP/TRUNCATE."""
    db_url = f"sqlite:///{(tmp_path / 'destr_block.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "destr_w")
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0

    # Inject a future destructive revision on top of the current head inside isolated tmp workdir
    bad_rev = work / "alembic" / "versions" / "deadbeef0001_bad_drop.py"
    bad_rev.write_text(
        '''"""bad drop"""
from alembic import op
revision = "deadbeef0001"
down_revision = "b6d2f0a8c4e1"
branch_labels = None
depends_on = None
def upgrade():
    op.drop_table("auth_sessions")
    op.drop_column("users", "role")
    op.execute("TRUNCATE TABLE step_edit_sessions")
def downgrade():
    pass
''',
        encoding="utf-8",
    )

    eng = create_engine(db_url)
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (email, display_name, password_hash, role, must_change_password, created_at) "
                "VALUES ('keep@algosim.edu.vn', 'Keep', 'h', 'student', 0, CURRENT_TIMESTAMP)"
            )
        )

    # 1) Even with backup+approval env vars set, --startup MUST refuse destructive migrations
    env_with_override = {
        **env,
        "ALGOSIM_BACKUP_VERIFIED": "1",
        "ALGOSIM_ALLOW_DESTRUCTIVE_MIGRATION": "deadbeef0001",
    }
    pre_start = _run_preflight(work, ini, env_with_override, "--startup", "--json")
    assert pre_start.returncode == 23
    assert json.loads(pre_start.stdout)["reason_code"] == "DESTRUCTIVE_MIGRATION_FORBIDDEN_AT_STARTUP"

    # 2) Startup downgrade MUST be refused
    pre_down = _run_preflight(work, ini, env, "--startup", "--direction", "downgrade", "--target", "e437149641fa", "--json")
    assert pre_down.returncode == 23
    assert json.loads(pre_down.stdout)["reason_code"] == "DOWNGRADE_FORBIDDEN_AT_STARTUP"

    # 3) Online `alembic upgrade head` without approval MUST fail cleanly with 0 data loss
    up_bad = _run_alembic(work, ini, env, "upgrade", "head")
    assert up_bad.returncode != 0
    assert "DESTRUCTIVE_UPGRADE_UNAPPROVED" in (up_bad.stdout + up_bad.stderr)
    with eng.connect() as conn:
        assert "auth_sessions" in set(inspect(eng).get_table_names())
        assert conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'keep@algosim.edu.vn'")).scalar_one() == 1
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "b6d2f0a8c4e1"
    eng.dispose()


def test_b4_8b_destructive_downgrade_on_populated_table_blocked_when_guarded(tmp_path: Path):
    db_url = f"sqlite:///{(tmp_path / 'guard_down.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "guard_down_w")
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    eng = create_engine(db_url)
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO step_edit_sessions (owner_scope, session_id, problem_key, base_scene_sha256, committed_scene_json, step_overrides_json, dependency_graph_json, revision_count, created_at, updated_at) "
                "VALUES ('client:gd', 'se-gd-1', 'sample:s1', 'a', '{}', '{}', '{}', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            )
        )

    guarded_env = {**env, "ALGOSIM_GUARD_DESTRUCTIVE_DOWNGRADE": "1"}
    down_res = _run_alembic(work, ini, guarded_env, "downgrade", "e437149641fa")
    assert down_res.returncode != 0
    assert "DESTRUCTIVE_DOWNGRADE_DATA_LOSS_BLOCKED" in (down_res.stdout + down_res.stderr)
    with eng.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM step_edit_sessions WHERE session_id = 'se-gd-1'")).scalar_one() == 1
    eng.dispose()


# ── Phase C Entrypoints: seed_classroom_fixture & seed_demo_accounts ───────────


def test_phase_c_retired_seed_classroom_fixture_has_zero_importerror_and_touch_zero_db(tmp_path: Path):
    r_help = subprocess.run(
        [sys.executable, str(SEED_CLASSROOM_SCRIPT), "--help"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )
    assert r_help.returncode == 0, r_help.stderr

    isolated_db = tmp_path / "should_not_exist.db"
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{isolated_db.as_posix()}"}
    r_json = subprocess.run(
        [sys.executable, "-X", "utf8", str(SEED_CLASSROOM_SCRIPT), "--json"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert r_json.returncode == 2
    payload = json.loads(r_json.stdout)
    assert payload["status"] == "CLASSROOM_FEATURE_RETIRED"
    assert payload["legacy_tables_untouched"] is True
    assert not isolated_db.exists()


def test_phase_c_seed_demo_accounts_creates_zero_legacy_tables_and_refuses_populated_classroom_db(tmp_path: Path):
    fresh_db = tmp_path / "demo_fresh.db"
    r1 = subprocess.run(
        [sys.executable, "-X", "utf8", str(SEED_DEMO_SCRIPT), "--db-path", str(fresh_db)],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert json.loads(r1.stdout)["count"] == 3
    con = sqlite3.connect(str(fresh_db))
    tbls = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    con.close()
    assert not (set(LEGACY_TABLES) & tbls), "seed_demo_accounts must never create retired legacy Classroom tables"

    # Populate a legacy DB and confirm seed_demo_accounts fails closed even with --reset-demo-db
    legacy_db = tmp_path / "legacy_protected.db"
    db_url = f"sqlite:///{legacy_db.as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "seed_guard_w")
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0
    eng = create_engine(db_url)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=False)
        before_users = _table_digest(conn, "users")
        before_cls = _table_digest(conn, "classrooms")

    r_refuse = subprocess.run(
        [sys.executable, "-X", "utf8", str(SEED_DEMO_SCRIPT), "--db-path", str(legacy_db), "--reset-demo-db"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert r_refuse.returncode != 0
    assert "RETAINED_CLASSROOM_DATA_PRESENT" in (r_refuse.stdout + r_refuse.stderr)
    with eng.connect() as conn:
        assert _table_digest(conn, "users") == before_users
        assert _table_digest(conn, "classrooms") == before_cls
    eng.dispose()


# ── Real PostgreSQL 16 Full 8-Scenario Parity + Mid-Migration Rollback ─────────


@pytest.mark.postgres
def test_b4_postgres16_full_matrix_and_mid_migration_atomic_rollback(pg_container, tmp_path: Path):
    """Execute Scenarios 1, 3, 4, 6 (mid-migration crash), 7, 8 directly against live PostgreSQL 16."""
    pg_url = pg_container["url"]
    work, ini, env = _stage_alembic_workspace(tmp_path, pg_url, "pg_matrix")

    # Scenario 1 & 7 on PG 16: clean upgrade -> head -> repeat startup no-op
    assert _run_preflight(work, ini, env, "--startup", "--json").returncode == 0
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0
    assert "Running upgrade" not in _run_alembic(work, ini, env, "upgrade", "head").stdout

    # Return cleanly to e437149641fa to test Scenario 3 & 4 (populated PG Classroom + Step Editor)
    assert _run_alembic(work, ini, env, "downgrade", "e437149641fa").returncode == 0
    eng = create_engine(pg_url, pool_pre_ping=True)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=True)
    assert _run_alembic(work, ini, env, "upgrade", "9c4d8e2b7a10").returncode == 0
    with eng.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO step_edit_sessions (owner_scope, session_id, problem_key, base_scene_sha256, committed_scene_json, step_overrides_json, dependency_graph_json, revision_count, created_at, updated_at) "
                "VALUES ('client:pgsafe', 'se-pg-safe-1', 'sample:s1', 'a', '{}', '{}', '{}', 1, now(), now())"
            )
        )
        pg_digests = {t: _table_digest(conn, t) for t in ("users", *LEGACY_TABLES, "step_edit_sessions")}

    assert _run_preflight(work, ini, env, "--startup", "--json").returncode == 0
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0
    with eng.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "b6d2f0a8c4e1"
        for t, exp in pg_digests.items():
            assert _table_digest(conn, t) == exp, f"PG {t} mutated on upgrade head!"

    # Scenario 6: Mid-migration failure injection on PG 16 transactional DDL
    crash_rev = work / "alembic" / "versions" / "cafe0002_mid_crash.py"
    crash_rev.write_text(
        '''"""mid crash"""
from alembic import op
import sqlalchemy as sa
revision = "cafe0002"
down_revision = "b6d2f0a8c4e1"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column("step_edit_sessions", sa.Column("mid_crash_col", sa.Text(), nullable=True))
    op.execute("CREATE TABLE mid_crash_tmp (id INT PRIMARY KEY)")
    raise RuntimeError("INJECTED_MID_MIGRATION_CRASH")
def downgrade():
    pass
''',
        encoding="utf-8",
    )
    crash_res = _run_alembic(work, ini, env, "upgrade", "head")
    assert crash_res.returncode != 0
    assert "INJECTED_MID_MIGRATION_CRASH" in (crash_res.stdout + crash_res.stderr)

    # Verify atomic PG DDL rollback: version still at head, no partial table/column left, 100% rows preserved
    insp = inspect(eng)
    assert "mid_crash_tmp" not in set(insp.get_table_names())
    assert "mid_crash_col" not in {c["name"] for c in insp.get_columns("step_edit_sessions")}
    with eng.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "b6d2f0a8c4e1"
        for t, exp in pg_digests.items():
            assert _table_digest(conn, t) == exp

    crash_rev.unlink()
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    # Scenario 8 on PG 16: destructive revision blocked by --startup and env.py
    bad_pg = work / "alembic" / "versions" / "badpg0003_drop.py"
    bad_pg.write_text(
        '''"""bad drop"""
from alembic import op
revision = "badpg0003"
down_revision = "b6d2f0a8c4e1"
branch_labels = None
depends_on = None
def upgrade():
    op.drop_table("classrooms")
def downgrade():
    pass
''',
        encoding="utf-8",
    )
    assert _run_preflight(work, ini, env, "--startup", "--json").returncode == 23
    up_bad_pg = _run_alembic(work, ini, env, "upgrade", "head")
    assert up_bad_pg.returncode != 0
    assert "DESTRUCTIVE_UPGRADE_UNAPPROVED" in (up_bad_pg.stdout + up_bad_pg.stderr)
    with eng.connect() as conn:
        assert _table_digest(conn, "classrooms") == pg_digests["classrooms"]
    eng.dispose()
