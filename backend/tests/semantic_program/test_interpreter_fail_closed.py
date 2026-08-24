# -*- coding: utf-8 -*-
"""Interpreter phải FAIL-CLOSED ở mọi vi phạm biên. **0 API call.**

VÌ SAO: audit 2026-08-24 tìm thấy interpreter im lặng cho qua MỌI vi phạm biên
của container:

    pop / dequeue trên rỗng  → no-op, KHÔNG ghi bước, không lỗi
    peek trên rỗng           → None
    index ngoài biên         → None

Hệ quả không phải "một bước bị thiếu". Nó là: **một chương trình sai sinh ra
trace trông hợp lý**. Học sinh xem một mô phỏng có bước biến mất mà không ai
nói cho biết là đang thiếu — cùng họ với lỗi đã sinh ra bất biến #31.

TIỀN LỆ ĐÚNG NGAY TRONG KHO NÀY: M13-SOUNDNESS đã sửa đúng lớp lỗi này cho
`generic_engine` — *"numeric silent-zero… KHÔNG còn seed/fallback 0"*, thay
bằng `GenericEvaluationError` fail-closed, 4 mã lỗi. `semantic_program/
interpreter.py` là **chủ sở hữu thứ hai** và đã tái tạo lại chính lỗi ấy cho
container. `CURRENT_STATE` đã ghi nhận mẫu "cùng lỗi ở chủ sở hữu thứ hai" một
lần rồi.

LUẬT: không no-op im lặng · không trả `None` khi đó là lỗi ngữ nghĩa · không tự
bịa giá trị mặc định. Vi phạm ⇒ `SemanticExecutionError`, và route dịch nó
thành `servable=False`.

RANH GIỚI — `map_get` có `default` TƯỜNG MINH thì KHÔNG phải lỗi: ở đó chương
trình đã tự khai điều mình muốn. Chỉ khoá những chỗ giá trị mặc định bị hệ
**âm thầm** bịa ra.
"""
from __future__ import annotations

import pytest

from app.simulation.semantic_program.contract import SemanticProgramSpec
from app.simulation.semantic_program.interpreter import (
    SemanticExecutionError,
    SemanticProgramInterpreter,
)


def _spec(memory: list[dict], statements: list[dict]) -> SemanticProgramSpec:
    return SemanticProgramSpec.model_validate({
        "spec_version": "1.0",
        "title": "Chương trình kiểm biên",
        "description": "Chương trình tối thiểu để kiểm hành vi ở biên.",
        "pedagogical_intent": "Chỉ dùng cho test, không phục vụ học sinh.",
        "memory_declarations": memory,
        "statements": statements,
        "visual_bindings": {"containers": [], "pointers": [], "value_boxes": []},
    })


def _chay(memory: list[dict], statements: list[dict]):
    return SemanticProgramInterpreter().execute(_spec(memory, statements))


_STACK_RONG = [{"name": "s", "type": "stack", "element_type": "int", "initial_value": []}]
_QUEUE_RONG = [{"name": "q", "type": "queue", "element_type": "int", "initial_value": []}]
_MANG = [{"name": "a", "type": "array", "element_type": "int", "initial_value": [1, 2]},
         {"name": "x", "type": "int", "initial_value": 0}]


# ── 1. pop trên rỗng ───────────────────────────────────────────────────────
def test_pop_tren_stack_rong_phai_NEM_LOI():
    """Trước bản vá: no-op im lặng, trace thiếu một bước, không ai biết."""
    with pytest.raises(SemanticExecutionError) as e:
        _chay(_STACK_RONG, [{"kind": "pop", "container": "s", "dest_var": "t"}])
    assert "s" in str(e.value)


# ── 2. dequeue trên rỗng ───────────────────────────────────────────────────
def test_dequeue_tren_queue_rong_phai_NEM_LOI():
    with pytest.raises(SemanticExecutionError):
        _chay(_QUEUE_RONG, [{"kind": "dequeue", "container": "q", "dest_var": "t"}])


# ── 3. peek trên rỗng ──────────────────────────────────────────────────────
def test_peek_tren_stack_rong_phai_NEM_LOI():
    """Trả `None` thì phép so sánh sau đó lặng lẽ sai, không lặng lẽ dừng."""
    with pytest.raises(SemanticExecutionError):
        _chay(_STACK_RONG + [{"name": "t", "type": "int", "initial_value": 0}],
              [{"kind": "assign", "target_var": "t",
                "expr": {"kind": "peek", "container": "s"}}])


# ── 4. chỉ số ngoài biên ───────────────────────────────────────────────────
def test_index_ngoai_bien_phai_NEM_LOI():
    with pytest.raises(SemanticExecutionError) as e:
        _chay(_MANG, [{"kind": "assign", "target_var": "x",
                       "expr": {"kind": "index", "container": "a",
                                "index": {"kind": "literal", "value": 99}}}])
    assert "99" in str(e.value) or "a" in str(e.value)


def test_index_am_phai_NEM_LOI():
    """Python cho `a[-1]`; IR thì không — âm là lỗi, không phải 'phần tử cuối'."""
    with pytest.raises(SemanticExecutionError):
        _chay(_MANG, [{"kind": "assign", "target_var": "x",
                       "expr": {"kind": "index", "container": "a",
                                "index": {"kind": "literal", "value": -1}}}])


# ── 5. ghi vào chỉ số ngoài biên ───────────────────────────────────────────
def test_write_index_ngoai_bien_phai_NEM_LOI():
    with pytest.raises(SemanticExecutionError):
        _chay(_MANG, [{"kind": "write_index", "container": "a",
                       "index": {"kind": "literal", "value": 99},
                       "val": {"kind": "literal", "value": 7}}])


# ── 6. tham chiếu container không tồn tại ──────────────────────────────────
def test_container_khong_ton_tai_bi_VALIDATOR_bat_truoc():
    """Bắt TĨNH là đúng tầng hơn — lỗi nêu ra trước khi tốn một bước chạy nào."""
    with pytest.raises(ValueError, match="KHONG_CO"):
        _chay(_MANG, [{"kind": "assign", "target_var": "x",
                       "expr": {"kind": "length", "container": "KHONG_CO"}}])


def test_interpreter_VAN_chan_container_la_khi_bo_qua_validator():
    """Phòng thủ chiều sâu: `_lay_container` không được tin vào khâu trước.

    `memory.get(ten, [])` — dạng cũ — biến một tên viết sai thành một dãy rỗng
    hợp lệ, và chương trình chạy tiếp trên hư không. Ở đây gọi thẳng
    `_eval_value`, không qua `execute()`, nên validator không che cho.
    """
    from app.simulation.semantic_program.contract import LengthExpr

    it = SemanticProgramInterpreter()
    it.memory = {"a": [1, 2]}
    with pytest.raises(SemanticExecutionError) as e:
        it._eval_value(LengthExpr(container="KHONG_CO"))
    assert e.value.code == "UNDECLARED_CONTAINER"
    assert "KHONG_CO" in str(e.value)


# ── Ranh giới: những thứ KHÔNG được biến thành lỗi ─────────────────────────
def test_pop_tren_stack_CO_phan_tu_van_chay_binh_thuong():
    kq = _chay(
        [{"name": "s", "type": "stack", "element_type": "int", "initial_value": [1, 2]},
         {"name": "t", "type": "int", "initial_value": 0}],
        [{"kind": "pop", "container": "s", "dest_var": "t"}],
    )
    assert kq.final_memory["t"] == 2
    assert kq.final_memory["s"] == [1]


def test_map_get_co_default_TUONG_MINH_thi_KHONG_phai_loi():
    """Chương trình tự khai giá trị muốn nhận ⇒ không phải hệ bịa ra."""
    kq = _chay(
        [{"name": "m", "type": "map", "key_type": "str", "val_type": "int",
          "initial_value": {}},
         {"name": "x", "type": "int", "initial_value": 0}],
        [{"kind": "assign", "target_var": "x",
          "expr": {"kind": "map_get", "container": "m",
                   "key": {"kind": "literal", "value": "k"},
                   "default": {"kind": "literal", "value": 42}}}],
    )
    assert kq.final_memory["x"] == 42


def test_is_empty_tren_rong_KHONG_phai_loi():
    """Hỏi 'có rỗng không' trên một dãy rỗng là câu hỏi hợp lệ."""
    kq = _chay(_STACK_RONG + [{"name": "b", "type": "bool", "initial_value": False}],
               [{"kind": "if",
                 "condition": {"kind": "is_empty", "container": "s"},
                 "then_body": [{"kind": "assign", "target_var": "b",
                                "expr": {"kind": "literal", "value": True}}],
                 "else_body": []}])
    assert kq.final_memory["b"] is True
