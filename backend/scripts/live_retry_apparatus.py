# -*- coding: utf-8 -*-
"""LIVE RETRY APPARATUS & PERSISTENCE ENGINE.

Implements the hardened state machine and durable persistence contract
for the SECOND_FAMILY_LIVE_RETRY wave:
PLANNED → RESERVED → TRANSPORT_COMPLETED → RAW_PERSISTED → PARSED → SCORED → PIPELINE_COMPLETED.

Enforces:
- Atomic write (temp file → flush → fsync → os.replace → read-back verify).
- Zero raw output committed to repository.
- Zero API key / Authorization header leaks in journal or metadata.
- Fail-closed on hash mismatch, truncation, or write failure.
- Single-request transport budget (0 resends, 0 retries).
- Production entry points for length evaluation (R1 fix) and compiler (R2 fix).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

# State Machine States
STATE_PLANNED = "PLANNED"
STATE_RESERVED = "RESERVED"
STATE_TRANSPORT_COMPLETED = "TRANSPORT_COMPLETED"
STATE_RAW_PERSISTED = "RAW_PERSISTED"
STATE_PARSED = "PARSED"
STATE_SCORED = "SCORED"
STATE_PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
STATE_MEASUREMENT_ERROR = "MEASUREMENT_ERROR"

VALID_STATES = (
    STATE_PLANNED,
    STATE_RESERVED,
    STATE_TRANSPORT_COMPLETED,
    STATE_RAW_PERSISTED,
    STATE_PARSED,
    STATE_SCORED,
    STATE_PIPELINE_COMPLETED,
    STATE_MEASUREMENT_ERROR,
)

# Secret sanitization pattern
SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE),
    re.compile(r"key=[0-9A-Za-z-_]{20,}", re.IGNORECASE),
]


def sanitize_metadata(data: Any) -> Any:
    """Recursively scrub secrets from metadata dictionaries/strings."""
    if isinstance(data, str):
        cleaned = data
        for pat in SECRET_PATTERNS:
            cleaned = pat.sub("[REDACTED_SECRET]", cleaned)
        return cleaned
    if isinstance(data, dict):
        cleaned_dict = {}
        for k, v in data.items():
            if any(term in k.lower() for term in ("api_key", "authorization", "secret", "token")):
                cleaned_dict[k] = "[REDACTED_KEY_FIELD]"
            else:
                cleaned_dict[k] = sanitize_metadata(v)
        return cleaned_dict
    if isinstance(data, (list, tuple)):
        return [sanitize_metadata(x) for x in data]
    return data


@dataclass
class JournalEntry:
    case_id: str
    state: str
    budget_reserved: int
    requests_sent: int
    raw_response_path: str | None
    raw_response_sha256: str | None
    raw_response_byte_count: int | None
    error: str | None = None


class ApparatusPersistenceError(Exception):
    """Raised when atomic write, read-back, or persistence invariant fails."""


class LiveRetryApparatus:
    """Hardened execution apparatus for live revalidation trials."""

    def __init__(self, execution_dir: Path, case_id: str = "PRISM_SCHEMA_LIVE_P01"):
        self.execution_dir = Path(execution_dir).resolve()
        self.execution_dir.mkdir(parents=True, exist_ok=True)
        self.case_id = case_id
        self.journal_path = self.execution_dir / f"{case_id}_journal.json"
        self.raw_response_path = self.execution_dir / f"{case_id}_raw_response.json"
        self.state = STATE_PLANNED
        self.budget_reserved = 0
        self.requests_sent = 0
        self.raw_bytes: bytes | None = None
        self.raw_sha256: str | None = None

    def _sync_journal(self, error: str | None = None) -> None:
        """Write current journal state atomically with secret sanitization."""
        entry = JournalEntry(
            case_id=self.case_id,
            state=self.state,
            budget_reserved=self.budget_reserved,
            requests_sent=self.requests_sent,
            raw_response_path=str(self.raw_response_path) if self.raw_response_path.exists() else None,
            raw_response_sha256=self.raw_sha256,
            raw_response_byte_count=len(self.raw_bytes) if self.raw_bytes else None,
            error=error,
        )
        safe_data = sanitize_metadata(asdict(entry))
        tmp = tempfile.NamedTemporaryFile("w", dir=self.execution_dir, delete=False, encoding="utf-8")
        try:
            tmp.write(json.dumps(safe_data, indent=2, ensure_ascii=False) + "\n")
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, self.journal_path)
        except Exception as e:
            try:
                tmp.close()
            except Exception:
                pass
            if os.path.exists(tmp.name):
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
            raise ApparatusPersistenceError(f"Failed to write journal atomically: {e}") from e

    def reserve_budget(self, max_requests: int = 1) -> None:
        """Reserve single-request budget; fail-closed if already reserved or sent."""
        if self.budget_reserved > 0 or self.requests_sent > 0 or self.state != STATE_PLANNED:
            raise ApparatusPersistenceError(
                f"Budget violation: cannot reserve budget in state {self.state} "
                f"(reserved={self.budget_reserved}, sent={self.requests_sent})"
            )
        self.budget_reserved = max_requests
        self.state = STATE_RESERVED
        self._sync_journal()

    def record_transport_response(self, raw_content: str | bytes, preview_only: bool = False) -> str:
        """Atomically persist raw response bytes BEFORE any parsing or evaluation.
        
        Rejects preview-only content and verifies hash via immediate read-back.
        """
        if self.state != STATE_RESERVED:
            raise ApparatusPersistenceError(f"Cannot record transport response in state {self.state}")
        if self.requests_sent >= self.budget_reserved:
            raise ApparatusPersistenceError("Request budget exhausted; cannot record response")
        
        if preview_only:
            self.state = STATE_MEASUREMENT_ERROR
            err = "Preview content rejected: raw persistence requires full candidate response bytes"
            self._sync_journal(error=err)
            raise ApparatusPersistenceError(err)

        if isinstance(raw_content, str):
            data_bytes = raw_content.encode("utf-8")
        else:
            data_bytes = raw_content

        if not data_bytes:
            self.state = STATE_MEASUREMENT_ERROR
            err = "Empty raw response bytes received"
            self._sync_journal(error=err)
            raise ApparatusPersistenceError(err)

        self.requests_sent += 1
        self.state = STATE_TRANSPORT_COMPLETED
        self._sync_journal()

        computed_sha = hashlib.sha256(data_bytes).hexdigest()

        # Atomic write: temp file in same directory -> flush -> fsync -> os.replace
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile("wb", dir=self.execution_dir, delete=False)
            tmp.write(data_bytes)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, self.raw_response_path)
        except Exception as e:
            if tmp is not None:
                try:
                    tmp.close()
                except Exception:
                    pass
                if os.path.exists(tmp.name):
                    try:
                        os.unlink(tmp.name)
                    except Exception:
                        pass
            self.state = STATE_MEASUREMENT_ERROR
            err = f"Atomic write failed: {e}"
            self._sync_journal(error=err)
            raise ApparatusPersistenceError(err) from e



        # Read-back verification
        try:
            read_bytes = self.raw_response_path.read_bytes()
            read_sha = hashlib.sha256(read_bytes).hexdigest()
            if read_sha != computed_sha or len(read_bytes) != len(data_bytes):
                self.state = STATE_MEASUREMENT_ERROR
                err = f"Read-back hash mismatch: read {read_sha} != expected {computed_sha}"
                self._sync_journal(error=err)
                raise ApparatusPersistenceError(err)
        except Exception as e:
            self.state = STATE_MEASUREMENT_ERROR
            err = f"Read-back verification failed: {e}"
            self._sync_journal(error=err)
            raise ApparatusPersistenceError(err) from e

        self.raw_bytes = read_bytes
        self.raw_sha256 = read_sha
        self.state = STATE_RAW_PERSISTED
        self._sync_journal()
        return read_sha

    def parse_from_durable_storage(self, parser_func: Callable[[str], Any]) -> Any:
        """Parse response ONLY from durable disk storage, never from in-memory transient state."""
        if self.state != STATE_RAW_PERSISTED:
            raise ApparatusPersistenceError(f"Cannot parse: raw persistence not reached (state={self.state})")
        
        if not self.raw_response_path.is_file():
            self.state = STATE_MEASUREMENT_ERROR
            err = f"Durable raw response file missing: {self.raw_response_path}"
            self._sync_journal(error=err)
            raise ApparatusPersistenceError(err)

        content = self.raw_response_path.read_text(encoding="utf-8")
        current_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if current_sha != self.raw_sha256:
            self.state = STATE_MEASUREMENT_ERROR
            err = f"Storage corrupted before parse: {current_sha} != {self.raw_sha256}"
            self._sync_journal(error=err)
            raise ApparatusPersistenceError(err)

        try:
            parsed = parser_func(content)
            self.state = STATE_PARSED
            self._sync_journal()
            return parsed
        except Exception as e:
            self.state = STATE_MEASUREMENT_ERROR
            err = f"Parser failure: {e}"
            self._sync_journal(error=err)
            raise

    def score_semantics(self, contract: Any, scorer_func: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        """Score semantic extraction using the corrected evaluator (R1 fix)."""
        if self.state != STATE_PARSED:
            raise ApparatusPersistenceError(f"Cannot score: state must be PARSED (current={self.state})")
        
        scores = scorer_func(contract)
        self.state = STATE_SCORED
        self._sync_journal()
        return scores

    def execute_pipeline(self, contract: Any, harness_func: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        """Execute downstream pipeline using production entry point (R2 fix)."""
        if self.state != STATE_SCORED:
            raise ApparatusPersistenceError(f"Cannot execute pipeline: state must be SCORED (current={self.state})")
        
        result = harness_func(contract)
        self.state = STATE_PIPELINE_COMPLETED
        self._sync_journal()
        return result
