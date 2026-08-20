# -*- coding: utf-8 -*-
"""LIVE_GEMINI_SEMANTIC_SMOKE: Kiểm thử E2E trực tiếp từ raw natural-language prompt -> Gemini AI thật -> SemanticProgram -> Validator -> Interpreter -> Playwright Renderer."""
import os
import json
import sys
import dotenv
from pathlib import Path
from typing import Any
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Load environment
backend_dir = Path(__file__).resolve().parent.parent
dotenv.load_dotenv(backend_dir / ".env")

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ai.gemini import load_skill
from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.validator import validate_semantic_program
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import compile_semantic_program_to_envelope

ARTIFACT_DIR = Path(r"C:\Users\Bunny\.gemini\antigravity-ide\brain\1b410171-c038-4e7f-ae93-ef8434b82ce0")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

LIVE_PROMPTS = [
    {
        "id": "live_p01_vowel_count",
        "title": "Đếm số nguyên âm trong xâu 'algorithm'",
        "user_prompt": "Mô phỏng thuật toán đếm số lượng ký tự nguyên âm (a, e, i, o, u) trong xâu ký tự ['a', 'l', 'g', 'o', 'r', 'i', 't', 'h', 'm'] bằng cách duyệt từng ký tự qua for_each, kiểm tra map/bảng tra {'a': 1, 'e': 1, 'i': 1, 'o': 1, 'u': 1}, và tăng biến vowel_count.",
    },
    {
        "id": "live_p02_second_largest",
        "title": "Tìm số lớn thứ nhì trong mảng [15, 42, 8, 99, 63]",
        "user_prompt": "Mô phỏng thuật toán quét qua mảng số nguyên [15, 42, 8, 99, 63] bằng for_range để tìm ra first_max và second_max.",
    },
    {
        "id": "live_p03_decimal_to_binary_stack",
        "title": "Đổi số nguyên 29 sang hệ nhị phân bằng Ngăn xếp",
        "user_prompt": "Mô phỏng thuật toán chuyển đổi số nguyên dương n=29 sang hệ nhị phân bằng while loop chia 2 lấy dư push vào stack 's', sau đó while pop stack push vào mảng binary_digits.",
    },
    {
        "id": "live_p04_palindrome_two_pointers",
        "title": "Kiểm tra xâu đối xứng 'racecar' bằng Hai con trỏ",
        "user_prompt": "Mô phỏng thuật toán Hai con trỏ left=0 và right=length-1 trên mảng ký tự ['r', 'a', 'c', 'e', 'c', 'a', 'r'] với while loop so sánh chars[left] và chars[right] để xác định is_pal (bool).",
    },
    {
        "id": "live_p05_graph_bfs_queue",
        "title": "Duyệt đồ thị BFS xuất phát từ đỉnh 1 bằng Hàng đợi",
        "user_prompt": "Mô phỏng thuật toán duyệt BFS từ đỉnh '1' trên graph {'1': ['2', '3'], '2': ['4'], '3': ['4', '5'], '4': [], '5': []} bằng queue 'q', tập 'visited', và mảng 'order'.",
    },
]

COMPACT_SCHEMA_GUIDE = """
BẮT BUỘC: Bạn CHỈ TRẢ VỀ DUY NHẤT một JSON Object SemanticProgramSpec hợp lệ tuân thủ chính xác cấu trúc sau:
{
  "spec_version": "1.0",
  "title": "Tên bài toán ngắn gọn",
  "description": "Mô tả bài toán",
  "pedagogical_intent": "Ý đồ sư phạm trực quan",
  "memory_declarations": [
    {"name": "tên_biến", "type": "array|stack|queue|map|set|matrix|tree_node|graph|int|str|bool", "element_type": "int|str|bool", "initial_value": ...}
  ],
  "statements": [
    // Các câu lệnh thuần ngữ nghĩa (KHÔNG dùng lệnh visual):
    // 1. assign: {"kind": "assign", "target_var": "x", "expr": ...}
    // 2. write_index: {"kind": "write_index", "container": "arr", "index": ..., "val": ...}
    // 3. push: {"kind": "push", "container": "s", "val": ...}
    // 4. pop: {"kind": "pop", "container": "s", "dest_var": "x"}
    // 5. enqueue: {"kind": "enqueue", "container": "q", "val": ...}
    // 6. dequeue: {"kind": "dequeue", "container": "q", "dest_var": "x"}
    // 7. set_insert: {"kind": "set_insert", "container": "visited", "val": ...}
    // 8. if: {"kind": "if", "condition": ..., "then_body": [...], "else_body": [...]}
    // 9. while: {"kind": "while", "condition": ..., "max_iterations": 200, "body": [...]}
    // 10. for_range: {"kind": "for_range", "loop_var": "i", "start": ..., "end": ..., "step": 1, "body": [...]}
    // 11. for_each: {"kind": "for_each", "item_var": "ch", "container_or_expr": "text" | {"kind": "neighbors", "graph": "g", "node": ...}, "body": [...]}
    // 12. break: {"kind": "break"}
    // 13. return: {"kind": "return", "val": ...}
  ],
  "visual_bindings": {
    "containers": [
      {"semantic_id": "tên_container", "primitive": "array_strip|stack_view|queue_view|table_grid|tree_element", "label": "Nhãn"}
    ],
    "pointers": [
      {"pointer_id": "ptr_i", "var_ref": "tên_biến_chỉ_số", "target_container": "tên_container", "label": "i"}
    ],
    "value_boxes": [
      {"box_id": "box_1", "var_ref": "tên_biến", "label": "Nhãn hộp"}
    ]
  }
}

Quy cách biểu thức (ValueExpr & ConditionExpr):
- Literal: {"kind": "literal", "value": ...}
- Var: {"kind": "var", "name": "tên_biến"}
- Index: {"kind": "index", "container": "tên_mảng", "index": ValueExpr}
- Arith: {"kind": "arith", "op": "+|-|*|//|%", "left": ValueExpr, "right": ValueExpr}
- Length: {"kind": "length", "container": "tên_container"}
- MapGet: {"kind": "map_get", "container": "map_name", "key": ValueExpr, "default": ValueExpr}
- Neighbors: {"kind": "neighbors", "graph": "graph_name", "node": ValueExpr}
- Compare: {"kind": "compare", "op": "==|!=|<|<=|>|>=", "left": ValueExpr, "right": ValueExpr}
- Logic: {"kind": "logic", "op": "and|or", "left": ConditionExpr, "right": ConditionExpr}
- Not: {"kind": "not", "expr": ConditionExpr}
- IsEmpty: {"kind": "is_empty", "container": "tên_container"}
- Contains: {"kind": "contains", "container": "tên_container", "item": ValueExpr}
"""


def call_gemini_sync(
    api_key: str,
    system_prompt: str,
    user_text: str,
    temperature: float = 0.1,
) -> str:
    """Gọi Gemini REST API đồng bộ bằng httpx.Client với responseMimeType=application/json."""
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={api_key}"
    )
    generation_config: dict = {
        "temperature": temperature,
        "responseMimeType": "application/json",
    }

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "generationConfig": generation_config,
    }

    with httpx.Client(timeout=60.0) as client:
        res = client.post(url, json=payload)
        if res.status_code != 200:
            raise RuntimeError(f"Gemini API trả về lỗi HTTP {res.status_code}: {res.text}")
        data = res.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Cấu trúc response Gemini không hợp lệ: {data}") from e


def run_live_smoke():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("LỖI: Chưa có GEMINI_API_KEY trong backend/.env hoặc biến môi trường!", flush=True)
        return 1

    print("==================================================================", flush=True)
    print(f" BẮT ĐẦU LIVE GEMINI SEMANTIC PROGRAM E2E CERTIFICATION (Model: {MODEL})", flush=True)
    print("==================================================================", flush=True)

    base_skill = load_skill("semantic_program")
    system_prompt = f"{base_skill}\n\n{COMPACT_SCHEMA_GUIDE}"

    envelopes_out = {}
    audit_results = []

    interpreter = SemanticProgramInterpreter(max_steps=300)

    for idx, item in enumerate(LIVE_PROMPTS, 1):
        p_id = item["id"]
        title = item["title"]
        prompt = item["user_prompt"]

        print(f"\n[{idx}/5] LIVE PROMPT: {p_id}", flush=True)
        print(f"  Title: {title}", flush=True)
        print(f"  Raw Prompt: \"{prompt}\"", flush=True)

        # 1. Gọi API Gemini thật
        print("  -> Đang gọi Gemini API trực tiếp...", flush=True)
        try:
            raw_response = call_gemini_sync(
                api_key=api_key,
                system_prompt=system_prompt,
                user_text=prompt,
                temperature=0.1,
            )
            print(f"  ✓ Nhận phản hồi thô từ Gemini ({len(raw_response)} bytes)", flush=True)
        except Exception as e:
            print(f"  ❌ Lỗi khi gọi Gemini: {e}", flush=True)
            audit_results.append({
                "id": p_id,
                "title": title,
                "status": "API_CALL_FAILED",
                "error": str(e),
            })
            continue

        # 2. Parse JSON thành SemanticProgramSpec
        try:
            data = json.loads(raw_response)
            spec = SemanticProgramSpec.model_validate(data)
            print(f"  ✓ Parse JSON thành SemanticProgramSpec: '{spec.title}'", flush=True)
        except Exception as e:
            print(f"  ❌ Lỗi parse JSON/Pydantic: {e}", flush=True)
            print(f"  Phản hồi thô: {raw_response[:300]}...", flush=True)
            audit_results.append({
                "id": p_id,
                "title": title,
                "status": "PYDANTIC_PARSE_FAILED",
                "raw_response": raw_response[:300],
                "error": str(e),
            })
            continue

        # 3. Thẩm định tĩnh bằng Validator
        val_res = validate_semantic_program(spec)
        if not val_res.ok:
            print(f"  ❌ Thẩm định tĩnh thất bại: {val_res.error}", flush=True)
            audit_results.append({
                "id": p_id,
                "title": title,
                "status": "VALIDATOR_REJECTED",
                "error": val_res.error,
            })
            continue
        print("  ✓ Static Validator: HỢP LỆ 100%", flush=True)

        # 4. Thực thi tất định trên AST bằng Interpreter
        try:
            exec_res = interpreter.execute(spec)
            print(f"  ✓ AST Interpreter: Hoàn thành {exec_res.total_steps} bước, status='{exec_res.status}'", flush=True)
            print(f"  ✓ Bộ nhớ cuối cùng: {exec_res.final_memory}", flush=True)
        except Exception as e:
            print(f"  ❌ Lỗi thực thi Interpreter: {e}", flush=True)
            audit_results.append({
                "id": p_id,
                "title": title,
                "status": "INTERPRETER_FAILED",
                "error": str(e),
            })
            continue

        # 5. Biên dịch thành SimulationEnvelope
        try:
            envelope = compile_semantic_program_to_envelope(spec)
            envelopes_out[p_id] = envelope
            step_count = len(envelope['config']['processes'][0]['steps'])
            print(f"  ✓ Pipeline Adapter: Biên dịch thành SimulationEnvelope ({step_count} frames)", flush=True)
        except Exception as e:
            print(f"  ❌ Lỗi biên dịch Envelope: {e}", flush=True)
            audit_results.append({
                "id": p_id,
                "title": title,
                "status": "ENVELOPE_COMPILE_FAILED",
                "error": str(e),
            })
            continue

        audit_results.append({
            "id": p_id,
            "title": title,
            "spec_title": spec.title,
            "status": "LIVE_GEMINI_CERTIFIED_OK",
            "total_steps": exec_res.total_steps,
            "final_memory": exec_res.final_memory,
            "first_narration": exec_res.trace[0].tier1_narration if exec_res.trace else "",
            "last_narration": exec_res.trace[-1].tier1_narration if exec_res.trace else "",
            "raw_response_preview": raw_response[:200] + "...",
        })

    # Lưu envelopes cho Playwright renderer
    out_fixtures_file = backend_dir.parent / "frontend" / "public" / "fixtures" / "live_gemini_unseen_candidates.json"
    out_fixtures_file.parent.mkdir(parents=True, exist_ok=True)
    out_fixtures_file.write_text(json.dumps(envelopes_out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nĐã xuất {len(envelopes_out)} Live Envelopes ra: {out_fixtures_file}", flush=True)

    # Lưu audit log
    out_audit_file = ARTIFACT_DIR / "live_gemini_semantic_audit.json"
    out_audit_file.write_text(json.dumps(audit_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Đã xuất kết quả kiểm toán AI ra: {out_audit_file}", flush=True)

    return 0

if __name__ == "__main__":
    exit_code = run_live_smoke()
    sys.exit(exit_code)
