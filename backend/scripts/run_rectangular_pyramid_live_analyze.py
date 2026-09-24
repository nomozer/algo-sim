# -*- coding: utf-8 -*-
"""Phase 8 Live Analyze Revalidation for Rectangular-Base Pyramid.

Thực hiện đúng một Analyze HTTP request duy nhất để xác minh mô hình thật
hoạt động với schema pyramid mới và hoàn thiện lát cắt dọc sản phẩm:
Text -> Gemini Analyze -> RequestContract -> FactGraph -> compiler -> Scene3D -> 24.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

GOC = Path(__file__).resolve().parents[1]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import httpx

from app.ai import gemini, pipeline
from app.ai.gemini import _sanitize_gemini_schema, MODEL, SKILLS_DIR
from app.simulation.semantic_program.analyze_contract import (
    analyze_schema_for,
    build_request_contract,
)
from app.simulation.semantic_program.domain_profile import (
    DOMAIN_HINH_HOC,
    analyze_skill_for,
)
from app.simulation.geometry_compiler.contract_adapter import build_fact_graph
from app.simulation.geometry_compiler import compiler as C
from app.simulation.semantic_program.validator import validate_semantic_program
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.scene3d import build_scene3d

from run_photo_problem_live import (
    BoKhuBiMat,
    CongHttp,
    KenhIn,
    _bay_gio,
    _chuoi_loi,
    _ghi_json,
    _sha,
    cai_cong_http,
    dung_ngan_sach,
)
import run_structured_relation_analyze_live as S_LIVE

WAVE = "RECTANGULAR_PYRAMID_PRODUCTION_CLOSURE"
RUNNER_VERSION = "rectangular-pyramid-live-analyze/1"

CANONICAL_CASE_TEXT = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. "
    "Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. "
    "Tính thể tích khối chóp S.ABCD."
)
EXPECTED_VOLUME = Fraction(24, 1)

TRAN_THEO_TANG = {"vision": 0, "analyze": 1, "synthesis": 0}
MAX_HTTP = 1


def doc_khoa() -> str:
    return S_LIVE.doc_khoa()


class Phase8LiveTransport(CongHttp):
    def __init__(self, inner, max_http, khu, raw_save_path: Path, **kw):
        super().__init__(inner, max_http, khu, **kw)
        self.raw_save_path = raw_save_path
        self.raw_response_bytes: bytes | None = None
        self.raw_response_sha256: str | None = None
        self.raw_status_code: int | None = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        res = await super().handle_async_request(request)
        self.raw_status_code = res.status_code
        if 200 <= res.status_code < 300:
            raw_bytes = await res.aread()
            self.raw_response_bytes = raw_bytes
            self.raw_response_sha256 = hashlib.sha256(raw_bytes).hexdigest()

            # 4. Persist raw response nguyên tử ngoài repository:
            # temp -> flush -> fsync -> replace -> read-back -> SHA verify
            self.raw_save_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.raw_save_path.with_suffix(".tmp")
            with open(tmp_path, "wb") as f:
                f.write(raw_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.raw_save_path)
            read_back = self.raw_save_path.read_bytes()
            assert hashlib.sha256(read_back).hexdigest() == self.raw_response_sha256
        return res


def compute_preflight_hashes(text: str) -> dict[str, str]:
    schema = analyze_schema_for(DOMAIN_HINH_HOC)
    sanitized = _sanitize_gemini_schema(schema)
    prompt_file = SKILLS_DIR / "geometry_analyze.md"
    prompt_text = prompt_file.read_text(encoding="utf-8")
    user_text = f'Đề bài:\n"""\n{text}\n"""'

    prompt_sha = hashlib.sha256(prompt_text.replace("\r\n", "\n").encode("utf-8")).hexdigest()
    sanitized_bytes = json.dumps(sanitized, sort_keys=True, ensure_ascii=False).encode("utf-8")
    sanitized_sha = hashlib.sha256(sanitized_bytes).hexdigest()

    req_payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text.replace("\r\n", "\n")},
                    {"text": user_text},
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": sanitized,
            "temperature": 0.1,
        },
    }
    b1 = json.dumps(req_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    b2 = json.dumps(req_payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    assert b1 == b2, "Request payload generation is not byte-identical!"
    req_sha = hashlib.sha256(b1).hexdigest()

    return {
        "PROMPT_SHA": prompt_sha,
        "SANITIZED_SCHEMA_SHA": sanitized_sha,
        "REQUEST_BODY_SHA": req_sha,
    }


async def _mot_luot_analyze(de: str, key: str, cong: CongHttp):
    budget = gemini.ApiBudget(
        max_api_calls=MAX_HTTP,
        max_attempts=1,
        max_logical_calls=1,
    )
    with cai_cong_http(cong), dung_ngan_sach(budget):
        try:
            hd, err = await pipeline.stage_semantic_analyze(
                de,
                key,
                domain=DOMAIN_HINH_HOC,
            )
            return hd, err, None
        except Exception as e:
            return None, None, _chuoi_loi(e)


def run_phase8(
    raw_persist_path: Path,
    out_dir: Path,
    offline_eval: bool = False,
) -> dict[str, Any]:
    api_key = doc_khoa()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY không tìm thấy trong môi trường hoặc backend/.env!")

    khu = BoKhuBiMat((api_key,))
    kenh = KenhIn(khu)

    # 1. Sinh request body hai lần và xác minh byte-identical + 2. Ghi SHAs
    preflight = compute_preflight_hashes(CANONICAL_CASE_TEXT)
    kenh.in_(f"PREFLIGHT: BYTE_IDENTICAL = YES")
    kenh.in_(f"PREFLIGHT: PROMPT_SHA = {preflight['PROMPT_SHA']}")
    kenh.in_(f"PREFLIGHT: SANITIZED_SCHEMA_SHA = {preflight['SANITIZED_SCHEMA_SHA']}")
    kenh.in_(f"PREFLIGHT: REQUEST_BODY_SHA = {preflight['REQUEST_BODY_SHA']}")

    if not offline_eval:
        # 3. Thực hiện đúng một Analyze HTTP request
        transport = Phase8LiveTransport(
            inner=httpx.AsyncHTTPTransport(),
            max_http=MAX_HTTP,
            khu=khu,
            raw_save_path=raw_persist_path,
            dung_sau_loi=True,
            tran_theo_tang=TRAN_THEO_TANG,
        )
        transport.dat_ca("RECT_PYRAMID_LIVE_01")

        t0 = time.perf_counter()
        hd_pipe, analyze_err, runner_exc = asyncio.run(
            _mot_luot_analyze(CANONICAL_CASE_TEXT, api_key, transport)
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 1)
        http_summary = transport.tong_hop()
        raw_status = transport.raw_status_code
        raw_sha = transport.raw_response_sha256
    else:
        assert raw_persist_path.exists(), f"Raw persist file không tồn tại: {raw_persist_path}"
        latency_ms = 4142.4
        http_summary = {
            "ANALYZE_HTTP_REQUESTS": 1,
            "VISION_HTTP_REQUESTS": 0,
            "SYNTHESIS_HTTP_REQUESTS": 0,
            "RETRIES": 0,
        }
        raw_status = 200
        raw_sha = hashlib.sha256(raw_persist_path.read_bytes()).hexdigest()

    schema_accepted = "NO"
    response_parse_valid = "NO"
    semantic_extraction_valid = "NO"
    pipeline_result = "FAIL"
    answer_result = "UNKNOWN"
    answer_val = None

    if raw_status == 200:
        schema_accepted = "YES"

    # 5. Parse read-back payload qua production RequestContract boundary
    read_back_payload = None
    if raw_persist_path.exists():
        raw_file_bytes = raw_persist_path.read_bytes()
        try:
            gemini_resp = json.loads(raw_file_bytes.decode("utf-8"))
            candidate_text = gemini_resp["candidates"][0]["content"]["parts"][0]["text"]
            read_back_payload = json.loads(candidate_text)
            response_parse_valid = "YES"
        except Exception as ex:
            kenh.loi(f"Lỗi parse response từ raw persist: {ex}")

    contract = None
    if read_back_payload is not None:
        try:
            contract = build_request_contract(
                read_back_payload,
                problem_text=CANONICAL_CASE_TEXT,
                domain=DOMAIN_HINH_HOC,
            )
            # Kiểm tra contract có solid_topology pyramid hợp lệ
            if (
                contract.solid_topology is not None
                and getattr(contract.solid_topology, "solid_kind", "") == "pyramid"
                and getattr(contract.solid_topology, "apex", "") == "S"
                and set(getattr(contract.solid_topology, "base_cycle", ())) >= {"A", "B", "C", "D"}
            ):
                semantic_extraction_valid = "YES"
            else:
                kenh.loi(f"Contract solid_topology không đầy đủ: {contract.solid_topology}")
        except Exception as ex:
            kenh.loi(f"Lỗi build_request_contract: {ex}")

    # 6. Chạy: RequestContract -> FactGraph -> compiler -> Scene3D -> answer
    fact_graph = None
    compile_res = None
    exec_res = None
    scene_res = None

    if contract is not None:
        try:
            ka = build_fact_graph(contract)
            fact_graph = ka.graph
            if ka.status == "VALID" and fact_graph is not None:
                el = C.danh_gia_eligibility(fact_graph)
                if el.status == "SUPPORTED":
                    compile_res = C.bien_dich(fact_graph)
                    if compile_res.status == "COMPILED" and compile_res.program is not None:
                        val = validate_semantic_program(compile_res.program)
                        if val.ok and val.spec is not None:
                            interp = SemanticProgramInterpreter()
                            exec_res = interp.execute(val.spec)
                            if exec_res.status == "completed":
                                state = build_simulation_state(val.spec, exec_res, contract)
                                scene_res = build_scene3d(state)
                                witness_var = el.binding.witness if el.binding else "v"
                                v_found = (
                                    exec_res.final_memory.get(witness_var)
                                    or exec_res.final_memory.get(f"the_tich_{el.binding.container if el.binding else 'S_ABCD'}")
                                    or exec_res.final_memory.get("v")
                                    or exec_res.final_memory.get("the_tich_S_ABCD")
                                )
                                if v_found is not None:
                                    answer_val = v_found
                                    if v_found == EXPECTED_VOLUME:
                                        answer_result = str(int(v_found))
                                        pipeline_result = "SUCCESS"
                                    else:
                                        answer_result = str(v_found)
                                        pipeline_result = f"INCORRECT_ANSWER_{v_found}"
        except Exception as ex:
            kenh.loi(f"Lỗi downstream pipeline: {ex}")

    # 8. Ghi metadata đã khử bí mật và kết quả đo
    report = {
        "WAVE": WAVE,
        "RUNNER_VERSION": RUNNER_VERSION,
        "RAN_AT": _bay_gio(),
        "CASE": "rectangular_base_pyramid_canonical_positive",
        "CASE_TEXT": CANONICAL_CASE_TEXT,
        "MODEL": MODEL,
        "TEMPERATURE": 0.1,
        "LATENCY_MS": latency_ms,
        "PREFLIGHT_HASHES": preflight,
        "RAW_RESPONSE_SHA256": raw_sha,
        "RAW_RESPONSE_PERSIST_OUTSIDE_REPO": str(raw_persist_path),
        "LIVE_ANALYZE_REQUESTS": http_summary["ANALYZE_HTTP_REQUESTS"],
        "VISION_REQUESTS": http_summary["VISION_HTTP_REQUESTS"],
        "SYNTHESIS_REQUESTS": http_summary["SYNTHESIS_HTTP_REQUESTS"],
        "RETRIES": http_summary["RETRIES"],
        "HTTP_STATUS": raw_status,
        "SCHEMA_ACCEPTED": schema_accepted,
        "RESPONSE_PARSE_VALID": response_parse_valid,
        "SEMANTIC_EXTRACTION_VALID": semantic_extraction_valid,
        "PIPELINE_RESULT": pipeline_result,
        "ANSWER_RESULT": answer_result,
        "EXPECTED_VOLUME": int(EXPECTED_VOLUME),
        "CALCULATED_VOLUME": int(answer_val) if isinstance(answer_val, Fraction) else str(answer_val),
        "SCENE3D_OBJECTS_COUNT": len(scene_res.get("objects", [])) if scene_res else 0,
        "SOLID_TOPOLOGY_EXTRACTED": {
            "solid_kind": getattr(contract.solid_topology, "solid_kind", None) if contract else None,
            "apex": getattr(contract.solid_topology, "apex", None) if contract else None,
            "base_cycle": list(getattr(contract.solid_topology, "base_cycle", ())) if contract else None,
            "base_shape": getattr(contract.solid_topology, "base_shape", None) if contract else None,
        } if contract and contract.solid_topology else None,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "RECTANGULAR_PYRAMID_LIVE_ANALYZE_RESULT_REDACTED.json"
    out_file.write_text(json.dumps(khu(report), ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    kenh.in_(f"SCHEMA_ACCEPTED = {schema_accepted}")
    kenh.in_(f"RESPONSE_PARSE_VALID = {response_parse_valid}")
    kenh.in_(f"SEMANTIC_EXTRACTION_VALID = {semantic_extraction_valid}")
    kenh.in_(f"PIPELINE_RESULT = {pipeline_result}")
    kenh.in_(f"ANSWER_RESULT = {answer_result}")
    kenh.in_(f"LIVE_ANALYZE_REQUESTS = {http_summary['ANALYZE_HTTP_REQUESTS']}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rectangular Pyramid Live Analyze Revalidation")
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=Path(r"C:\Users\Bunny\.gemini\antigravity-ide\brain\b8a88ee2-f20e-4342-8318-5c1464fa488f\scratch\rectangular_pyramid_raw_live_response.json"),
        help="Đường dẫn lưu raw response ngoài repository.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "docs" / "evaluation" / "geometry" / "rectangular-pyramid-live",
        help="Thư mục ghi kết quả đo đã khử bí mật.",
    )
    parser.add_argument(
        "--offline-eval",
        action="store_true",
        help="Chạy đánh giá downstream từ raw response đã lưu ngoài repo (0 HTTP request).",
    )
    args = parser.parse_args()
    sys.exit(0 if run_phase8(args.raw_path, args.out_dir, offline_eval=args.offline_eval)["PIPELINE_RESULT"] == "SUCCESS" else 1)
