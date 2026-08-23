# -*- coding: utf-8 -*-
"""DESIGN_COVERAGE_REVIEW: Ma trận 18 bài toán thuật toán Tin học THPT.

Toàn bộ 18 bài toán được biểu diễn 100% bằng SemanticProgramSpec thuần túy:
- KHÔNG dùng toán tử đặc thù (target_specific_operators = 0).
- KHÔNG trộn lẫn visual commands (MOVE_POINTER, HIGHLIGHT) vào code thuật toán.
- KHÔNG tiền tính toán (No precomputed shortcuts).
"""
from app.simulation.semantic_program.contract import (
    SemanticProgramSpec,
    MemoryDeclaration,
    VisualBindings,
    VisualContainerBinding,
    VisualPointerBinding,
    VisualValueBoxBinding,
    AssignStmt,
    WriteIndexStmt,
    MapSetStmt,
    SwapStmt,
    PushStmt,
    PopStmt,
    EnqueueStmt,
    DequeueStmt,
    SetInsertStmt,
    SetRemoveStmt,
    IfStmt,
    WhileStmt,
    ForRangeStmt,
    ForEachStmt,
    BreakStmt,
    ReturnStmt,
    LiteralExpr,
    VarRefExpr,
    IndexRefExpr,
    FieldRefExpr,
    BinaryArithExpr,
    UnaryArithExpr,
    LengthExpr,
    PeekExpr,
    MapGetExpr,
    NeighborsExpr,
    CompareCond,
    LogicCond,
    NotCond,
    IsEmptyCond,
    ContainsCond,
    IsNullCond,
)

# ── 1. Kiểm tra chuỗi ngoặc hợp lệ bằng Ngăn xếp ─────────────────────────
P01_STACK_BRACKET = SemanticProgramSpec(
    title="Kiểm tra chuỗi ngoặc hợp lệ bằng Ngăn xếp",
    description="Duyệt từng ký tự, gặp mở thì push, gặp đóng thì kiểm tra đỉnh stack và pop.",
    pedagogical_intent="Học sinh quan sát cách Ngăn xếp lưu trữ các dấu mở ngoặc và khử cặp khi gặp dấu đóng tương ứng.",
    memory_declarations=[
        MemoryDeclaration(name="bracket_strip", type="array", element_type="str", initial_value=["{", "[", "(", ")", "]", "}"]),
        MemoryDeclaration(name="stack", type="stack", element_type="str", initial_value=[]),
        MemoryDeclaration(name="pairs", type="map", key_type="str", val_type="str", initial_value={"(": ")", "[": "]", "{": "}"}),
        MemoryDeclaration(name="result", type="str", initial_value="HỢP LỆ"),
    ],
    statements=[
        ForEachStmt(
            item_var="c",
            container_or_expr="bracket_strip",
            body=[
                IfStmt(
                    condition=ContainsCond(container="pairs", item=VarRefExpr(name="c")),
                    then_body=[
                        PushStmt(container="stack", val=VarRefExpr(name="c")),
                    ],
                    else_body=[
                        IfStmt(
                            condition=LogicCond(
                                op="and",
                                left=NotCond(expr=IsEmptyCond(container="stack")),
                                right=CompareCond(
                                    op="==",
                                    left=MapGetExpr(container="pairs", key=PeekExpr(container="stack")),
                                    right=VarRefExpr(name="c"),
                                ),
                            ),
                            then_body=[
                                PopStmt(container="stack"),
                            ],
                            else_body=[
                                AssignStmt(target_var="result", expr=LiteralExpr(value="KHÔNG HỢP LỆ")),
                                BreakStmt(),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        IfStmt(
            condition=NotCond(expr=IsEmptyCond(container="stack")),
            then_body=[
                AssignStmt(target_var="result", expr=LiteralExpr(value="KHÔNG HỢP LỆ")),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="bracket_strip", primitive="array_strip", label="Chuỗi ngoặc đầu vào"),
            VisualContainerBinding(semantic_id="stack", primitive="stack_view", label="Ngăn xếp"),
            # THÊM 2026-08-23. `pairs` là bảng ghép ngoặc: nó KHÔNG biến động
            # nên luật (1) của `learner_surface` không đòi, nhưng nó có
            # `initial_value` không rỗng nên `grounding_gate` buộc phải ghim
            # `source_fact_id` — và cái gì đã khai là dữ liệu đề thì luật (2)
            # đòi phải thấy được. Hai luật ấy khớp nhau, chỉ thiếu ĐƯỜNG: `map`
            # không có primitive nào cho tới khi `map_view` ra đời cùng ngày.
            # Hiện nó ra cũng đúng sư phạm hơn: học sinh thấy bảng đang được tra.
            VisualContainerBinding(semantic_id="pairs", primitive="map_view", label="Bảng ghép ngoặc"),
        ],
        pointers=[
            # BỎ 2026-08-20 (bất biến #34): con trỏ buộc vào BIẾN KÝ TỰ của
            # `for_each` — không có chỉ số nên không bao giờ neo được vào ô nào,
            # và nó chính là con trỏ trôi đè lên chữ ở spec §0(b).
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="result_box", var_ref="result", label="Kết quả"),
        ],
    ),
)

# ── 2. Tìm phần tử lớn nhất (Linear Search / Max) ─────────────────────────
P02_FIND_MAX = SemanticProgramSpec(
    title="Tìm phần tử lớn nhất trong dãy số",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[12, 45, 67, 23, 89, 34]),
        MemoryDeclaration(name="max_val", type="int", initial_value=0),
        MemoryDeclaration(name="max_idx", type="int", initial_value=0),
    ],
    statements=[
        AssignStmt(target_var="max_val", expr=IndexRefExpr(container="arr", index=LiteralExpr(value=0))),
        AssignStmt(target_var="max_idx", expr=LiteralExpr(value=0)),
        ForRangeStmt(
            loop_var="i",
            start=LiteralExpr(value=1),
            end=LengthExpr(container="arr"),
            body=[
                IfStmt(
                    condition=CompareCond(
                        op=">",
                        left=IndexRefExpr(container="arr", index=VarRefExpr(name="i")),
                        right=VarRefExpr(name="max_val"),
                    ),
                    then_body=[
                        AssignStmt(target_var="max_val", expr=IndexRefExpr(container="arr", index=VarRefExpr(name="i"))),
                        AssignStmt(target_var="max_idx", expr=VarRefExpr(name="i")),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Dãy số"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_i", var_ref="i", target_container="arr", label="i"),
            VisualPointerBinding(pointer_id="ptr_max", var_ref="max_idx", target_container="arr", label="max"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="max_box", var_ref="max_val", label="Giá trị lớn nhất"),
        ],
    ),
)

# ── 3. Tìm kiếm nhị phân (Binary Search) ──────────────────────────────────
P03_BINARY_SEARCH = SemanticProgramSpec(
    title="Tìm kiếm nhị phân trên dãy đã sắp thứ tự",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[2, 5, 8, 12, 16, 23, 38, 56, 72, 91]),
        MemoryDeclaration(name="target", type="int", initial_value=23),
        MemoryDeclaration(name="left", type="int", initial_value=0),
        MemoryDeclaration(name="right", type="int", initial_value=9),
        MemoryDeclaration(name="mid", type="int", initial_value=0),
        MemoryDeclaration(name="found_idx", type="int", initial_value=-1),
    ],
    statements=[
        AssignStmt(
            target_var="right",
            expr=BinaryArithExpr(op="-", left=LengthExpr(container="arr"), right=LiteralExpr(value=1)),
        ),
        WhileStmt(
            condition=CompareCond(op="<=", left=VarRefExpr(name="left"), right=VarRefExpr(name="right")),
            body=[
                AssignStmt(
                    target_var="mid",
                    expr=BinaryArithExpr(
                        op="//",
                        left=BinaryArithExpr(op="+", left=VarRefExpr(name="left"), right=VarRefExpr(name="right")),
                        right=LiteralExpr(value=2),
                    ),
                ),
                IfStmt(
                    condition=CompareCond(
                        op="==",
                        left=IndexRefExpr(container="arr", index=VarRefExpr(name="mid")),
                        right=VarRefExpr(name="target"),
                    ),
                    then_body=[
                        AssignStmt(target_var="found_idx", expr=VarRefExpr(name="mid")),
                        BreakStmt(),
                    ],
                    else_body=[
                        IfStmt(
                            condition=CompareCond(
                                op="<",
                                left=IndexRefExpr(container="arr", index=VarRefExpr(name="mid")),
                                right=VarRefExpr(name="target"),
                            ),
                            then_body=[
                                AssignStmt(
                                    target_var="left",
                                    expr=BinaryArithExpr(op="+", left=VarRefExpr(name="mid"), right=LiteralExpr(value=1)),
                                ),
                            ],
                            else_body=[
                                AssignStmt(
                                    target_var="right",
                                    expr=BinaryArithExpr(op="-", left=VarRefExpr(name="mid"), right=LiteralExpr(value=1)),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Dãy số đã sắp thứ tự"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_l", var_ref="left", target_container="arr", label="left"),
            VisualPointerBinding(pointer_id="ptr_r", var_ref="right", target_container="arr", label="right"),
            VisualPointerBinding(pointer_id="ptr_m", var_ref="mid", target_container="arr", label="mid"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="target_box", var_ref="target", label="Khóa cần tìm"),
            VisualValueBoxBinding(box_id="found_box", var_ref="found_idx", label="Vị trí tìm thấy"),
        ],
    ),
)

# ── 4. Sắp xếp nổi bọt (Bubble Sort) ─────────────────────────────────────
P04_BUBBLE_SORT = SemanticProgramSpec(
    title="Sắp xếp nổi bọt (Bubble Sort)",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[5, 1, 4, 2, 8]),
        MemoryDeclaration(name="n", type="int", initial_value=5),
        MemoryDeclaration(name="swapped", type="bool", initial_value=False),
    ],
    statements=[
        AssignStmt(target_var="n", expr=LengthExpr(container="arr")),
        ForRangeStmt(
            loop_var="i",
            start=LiteralExpr(value=0),
            end=BinaryArithExpr(op="-", left=VarRefExpr(name="n"), right=LiteralExpr(value=1)),
            body=[
                AssignStmt(target_var="swapped", expr=LiteralExpr(value=False)),
                ForRangeStmt(
                    loop_var="j",
                    start=LiteralExpr(value=0),
                    end=BinaryArithExpr(
                        op="-",
                        left=BinaryArithExpr(op="-", left=VarRefExpr(name="n"), right=LiteralExpr(value=1)),
                        right=VarRefExpr(name="i"),
                    ),
                    body=[
                        IfStmt(
                            condition=CompareCond(
                                op=">",
                                left=IndexRefExpr(container="arr", index=VarRefExpr(name="j")),
                                right=IndexRefExpr(
                                    container="arr",
                                    index=BinaryArithExpr(op="+", left=VarRefExpr(name="j"), right=LiteralExpr(value=1)),
                                ),
                            ),
                            then_body=[
                                SwapStmt(
                                    container="arr",
                                    idx_a=VarRefExpr(name="j"),
                                    idx_b=BinaryArithExpr(op="+", left=VarRefExpr(name="j"), right=LiteralExpr(value=1)),
                                ),
                                AssignStmt(target_var="swapped", expr=LiteralExpr(value=True)),
                            ],
                        ),
                    ],
                ),
                IfStmt(
                    condition=NotCond(expr=CompareCond(op="==", left=VarRefExpr(name="swapped"), right=LiteralExpr(value=True))),
                    then_body=[BreakStmt()],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Dãy số"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_j", var_ref="j", target_container="arr", label="j"),
        ],
    ),
)

# ── 5. Sắp xếp chọn (Selection Sort) ─────────────────────────────────────
P05_SELECTION_SORT = SemanticProgramSpec(
    title="Sắp xếp chọn (Selection Sort)",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[64, 25, 12, 22, 11]),
        MemoryDeclaration(name="n", type="int", initial_value=5),
        MemoryDeclaration(name="min_idx", type="int", initial_value=0),
    ],
    statements=[
        AssignStmt(target_var="n", expr=LengthExpr(container="arr")),
        ForRangeStmt(
            loop_var="i",
            start=LiteralExpr(value=0),
            end=BinaryArithExpr(op="-", left=VarRefExpr(name="n"), right=LiteralExpr(value=1)),
            body=[
                AssignStmt(target_var="min_idx", expr=VarRefExpr(name="i")),
                ForRangeStmt(
                    loop_var="j",
                    start=BinaryArithExpr(op="+", left=VarRefExpr(name="i"), right=LiteralExpr(value=1)),
                    end=VarRefExpr(name="n"),
                    body=[
                        IfStmt(
                            condition=CompareCond(
                                op="<",
                                left=IndexRefExpr(container="arr", index=VarRefExpr(name="j")),
                                right=IndexRefExpr(container="arr", index=VarRefExpr(name="min_idx")),
                            ),
                            then_body=[
                                AssignStmt(target_var="min_idx", expr=VarRefExpr(name="j")),
                            ],
                        ),
                    ],
                ),
                IfStmt(
                    condition=CompareCond(op="!=", left=VarRefExpr(name="min_idx"), right=VarRefExpr(name="i")),
                    then_body=[
                        SwapStmt(container="arr", idx_a=VarRefExpr(name="i"), idx_b=VarRefExpr(name="min_idx")),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Dãy số"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_i", var_ref="i", target_container="arr", label="i"),
            VisualPointerBinding(pointer_id="ptr_min", var_ref="min_idx", target_container="arr", label="min"),
            VisualPointerBinding(pointer_id="ptr_j", var_ref="j", target_container="arr", label="j"),
        ],
    ),
)

# ── 6. Sắp xếp chèn (Insertion Sort) ─────────────────────────────────────
P06_INSERTION_SORT = SemanticProgramSpec(
    title="Sắp xếp chèn (Insertion Sort)",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[12, 11, 13, 5, 6]),
        MemoryDeclaration(name="n", type="int", initial_value=5),
        MemoryDeclaration(name="key", type="int", initial_value=0),
        MemoryDeclaration(name="j", type="int", initial_value=0),
    ],
    statements=[
        AssignStmt(target_var="n", expr=LengthExpr(container="arr")),
        ForRangeStmt(
            loop_var="i",
            start=LiteralExpr(value=1),
            end=VarRefExpr(name="n"),
            body=[
                AssignStmt(target_var="key", expr=IndexRefExpr(container="arr", index=VarRefExpr(name="i"))),
                AssignStmt(
                    target_var="j",
                    expr=BinaryArithExpr(op="-", left=VarRefExpr(name="i"), right=LiteralExpr(value=1)),
                ),
                WhileStmt(
                    condition=LogicCond(
                        op="and",
                        left=CompareCond(op=">=", left=VarRefExpr(name="j"), right=LiteralExpr(value=0)),
                        right=CompareCond(
                            op=">",
                            left=IndexRefExpr(container="arr", index=VarRefExpr(name="j")),
                            right=VarRefExpr(name="key"),
                        ),
                    ),
                    body=[
                        WriteIndexStmt(
                            container="arr",
                            index=BinaryArithExpr(op="+", left=VarRefExpr(name="j"), right=LiteralExpr(value=1)),
                            val=IndexRefExpr(container="arr", index=VarRefExpr(name="j")),
                        ),
                        AssignStmt(
                            target_var="j",
                            expr=BinaryArithExpr(op="-", left=VarRefExpr(name="j"), right=LiteralExpr(value=1)),
                        ),
                    ],
                ),
                WriteIndexStmt(
                    container="arr",
                    index=BinaryArithExpr(op="+", left=VarRefExpr(name="j"), right=LiteralExpr(value=1)),
                    val=VarRefExpr(name="key"),
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Dãy số"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_i", var_ref="i", target_container="arr", label="i"),
            VisualPointerBinding(pointer_id="ptr_j", var_ref="j", target_container="arr", label="j"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="key_box", var_ref="key", label="Phần tử chèn (key)"),
        ],
    ),
)

# ── 7. Hai con trỏ: Two Sum trên mảng đã sắp ──────────────────────────────
P07_TWO_SUM_SORTED = SemanticProgramSpec(
    title="Hai con trỏ: Tìm cặp số có tổng bằng K trên mảng đã sắp",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[1, 2, 3, 4, 6, 8, 11]),
        MemoryDeclaration(name="target", type="int", initial_value=10),
        MemoryDeclaration(name="left", type="int", initial_value=0),
        MemoryDeclaration(name="right", type="int", initial_value=6),
        MemoryDeclaration(name="curr_sum", type="int", initial_value=0),
        MemoryDeclaration(name="found", type="bool", initial_value=False),
    ],
    statements=[
        AssignStmt(
            target_var="right",
            expr=BinaryArithExpr(op="-", left=LengthExpr(container="arr"), right=LiteralExpr(value=1)),
        ),
        WhileStmt(
            condition=CompareCond(op="<", left=VarRefExpr(name="left"), right=VarRefExpr(name="right")),
            body=[
                AssignStmt(
                    target_var="curr_sum",
                    expr=BinaryArithExpr(
                        op="+",
                        left=IndexRefExpr(container="arr", index=VarRefExpr(name="left")),
                        right=IndexRefExpr(container="arr", index=VarRefExpr(name="right")),
                    ),
                ),
                IfStmt(
                    condition=CompareCond(op="==", left=VarRefExpr(name="curr_sum"), right=VarRefExpr(name="target")),
                    then_body=[
                        AssignStmt(target_var="found", expr=LiteralExpr(value=True)),
                        BreakStmt(),
                    ],
                    else_body=[
                        IfStmt(
                            condition=CompareCond(op="<", left=VarRefExpr(name="curr_sum"), right=VarRefExpr(name="target")),
                            then_body=[
                                AssignStmt(
                                    target_var="left",
                                    expr=BinaryArithExpr(op="+", left=VarRefExpr(name="left"), right=LiteralExpr(value=1)),
                                ),
                            ],
                            else_body=[
                                AssignStmt(
                                    target_var="right",
                                    expr=BinaryArithExpr(op="-", left=VarRefExpr(name="right"), right=LiteralExpr(value=1)),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Dãy số"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_l", var_ref="left", target_container="arr", label="left"),
            VisualPointerBinding(pointer_id="ptr_r", var_ref="right", target_container="arr", label="right"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="sum_box", var_ref="curr_sum", label="Tổng hiện thời"),
            VisualValueBoxBinding(box_id="found_box", var_ref="found", label="Tìm thấy"),
        ],
    ),
)

# ── 8. Hai con trỏ: Kiểm tra chuỗi đối xứng (Palindrome) ──────────────────
P08_PALINDROME = SemanticProgramSpec(
    title="Hai con trỏ: Kiểm tra chuỗi đối xứng (Palindrome)",
    memory_declarations=[
        MemoryDeclaration(name="chars", type="array", element_type="str", initial_value=["r", "a", "d", "a", "r"]),
        MemoryDeclaration(name="left", type="int", initial_value=0),
        MemoryDeclaration(name="right", type="int", initial_value=4),
        MemoryDeclaration(name="is_pal", type="bool", initial_value=True),
    ],
    statements=[
        AssignStmt(
            target_var="right",
            expr=BinaryArithExpr(op="-", left=LengthExpr(container="chars"), right=LiteralExpr(value=1)),
        ),
        WhileStmt(
            condition=CompareCond(op="<", left=VarRefExpr(name="left"), right=VarRefExpr(name="right")),
            body=[
                IfStmt(
                    condition=CompareCond(
                        op="!=",
                        left=IndexRefExpr(container="chars", index=VarRefExpr(name="left")),
                        right=IndexRefExpr(container="chars", index=VarRefExpr(name="right")),
                    ),
                    then_body=[
                        AssignStmt(target_var="is_pal", expr=LiteralExpr(value=False)),
                        BreakStmt(),
                    ],
                ),
                AssignStmt(
                    target_var="left",
                    expr=BinaryArithExpr(op="+", left=VarRefExpr(name="left"), right=LiteralExpr(value=1)),
                ),
                AssignStmt(
                    target_var="right",
                    expr=BinaryArithExpr(op="-", left=VarRefExpr(name="right"), right=LiteralExpr(value=1)),
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="chars", primitive="array_strip", label="Xâu ký tự"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_l", var_ref="left", target_container="chars", label="left"),
            VisualPointerBinding(pointer_id="ptr_r", var_ref="right", target_container="chars", label="right"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="pal_box", var_ref="is_pal", label="Đối xứng?"),
        ],
    ),
)

# ── 9. Duyệt đồ thị theo chiều rộng (Graph BFS) ───────────────────────────
P09_GRAPH_BFS = SemanticProgramSpec(
    title="Duyệt đồ thị theo chiều rộng (BFS) bằng Hàng đợi",
    memory_declarations=[
        MemoryDeclaration(
            name="g",
            type="graph",
            initial_value={"1": ["2", "3"], "2": ["4"], "3": ["4", "5"], "4": [], "5": []},
        ),
        MemoryDeclaration(name="q", type="queue", element_type="str", initial_value=[]),
        MemoryDeclaration(name="visited", type="set", element_type="str", initial_value=[]),
        MemoryDeclaration(name="order", type="array", element_type="str", initial_value=[]),
    ],
    statements=[
        EnqueueStmt(container="q", val=LiteralExpr(value="1")),
        SetInsertStmt(container="visited", val=LiteralExpr(value="1")),
        WhileStmt(
            condition=NotCond(expr=IsEmptyCond(container="q")),
            body=[
                DequeueStmt(container="q", dest_var="u"),
                PushStmt(container="order", val=VarRefExpr(name="u")),
                ForEachStmt(
                    item_var="v",
                    container_or_expr=NeighborsExpr(graph="g", node=VarRefExpr(name="u")),
                    body=[
                        IfStmt(
                            condition=NotCond(expr=ContainsCond(container="visited", item=VarRefExpr(name="v"))),
                            then_body=[
                                SetInsertStmt(container="visited", val=VarRefExpr(name="v")),
                                EnqueueStmt(container="q", val=VarRefExpr(name="v")),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            # 2026-08-21 — ĐỒ THỊ nay vẽ được. Trước đó bài BFS chỉ thấy hàng
            # đợi và thứ tự duyệt: cơ chế trung tâm (đi qua đỉnh nào, theo thứ
            # tự nào) không xuất hiện trên màn hình. Trạng thái đỉnh KHAI BÁO
            # bằng tên biến — renderer đọc, không tự chạy lại BFS.
            VisualContainerBinding(
                semantic_id="g", primitive="graph_view", label="Đồ thị",
                visited_ref="visited", current_ref="u",
            ),
            VisualContainerBinding(semantic_id="q", primitive="queue_view", label="Hàng đợi BFS"),
            VisualContainerBinding(semantic_id="order", primitive="array_strip", label="Thứ tự duyệt"),
        ],
    ),
)

# ── 10. Đảo ngược chuỗi bằng Ngăn xếp ─────────────────────────────────────
P10_REVERSE_STRING_STACK = SemanticProgramSpec(
    title="Đảo ngược chuỗi ký tự bằng Ngăn xếp",
    memory_declarations=[
        MemoryDeclaration(name="input_chars", type="array", element_type="str", initial_value=["H", "E", "L", "L", "O"]),
        MemoryDeclaration(name="s", type="stack", element_type="str", initial_value=[]),
        MemoryDeclaration(name="output_chars", type="array", element_type="str", initial_value=[]),
    ],
    statements=[
        ForEachStmt(
            item_var="c",
            container_or_expr="input_chars",
            body=[
                PushStmt(container="s", val=VarRefExpr(name="c")),
            ],
        ),
        WhileStmt(
            condition=NotCond(expr=IsEmptyCond(container="s")),
            body=[
                PopStmt(container="s", dest_var="top_c"),
                PushStmt(container="output_chars", val=VarRefExpr(name="top_c")),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="input_chars", primitive="array_strip", label="Chuỗi ban đầu"),
            VisualContainerBinding(semantic_id="s", primitive="stack_view", label="Ngăn xếp"),
            VisualContainerBinding(semantic_id="output_chars", primitive="array_strip", label="Chuỗi đảo ngược"),
        ],
    ),
)

# ── 11. Duyệt cây nhị phân tiền thứ tự (Preorder NLR) ─────────────────────
P11_TREE_PREORDER = SemanticProgramSpec(
    title="Duyệt cây nhị phân theo thứ tự trước (Preorder NLR)",
    memory_declarations=[
        MemoryDeclaration(
            name="tree_root",
            type="tree_node",
            initial_value={"val": "A", "left": {"val": "B", "left": None, "right": None}, "right": {"val": "C", "left": None, "right": None}},
        ),
        MemoryDeclaration(name="s", type="stack", element_type="tree_node", initial_value=[]),
        MemoryDeclaration(name="order", type="array", element_type="str", initial_value=[]),
    ],
    statements=[
        PushStmt(container="s", val=VarRefExpr(name="tree_root")),
        WhileStmt(
            condition=NotCond(expr=IsEmptyCond(container="s")),
            body=[
                PopStmt(container="s", dest_var="curr"),
                PushStmt(container="order", val=FieldRefExpr(target=VarRefExpr(name="curr"), field="val")),
                IfStmt(
                    condition=NotCond(expr=IsNullCond(expr=FieldRefExpr(target=VarRefExpr(name="curr"), field="right"))),
                    then_body=[
                        PushStmt(container="s", val=FieldRefExpr(target=VarRefExpr(name="curr"), field="right")),
                    ],
                ),
                IfStmt(
                    condition=NotCond(expr=IsNullCond(expr=FieldRefExpr(target=VarRefExpr(name="curr"), field="left"))),
                    then_body=[
                        PushStmt(container="s", val=FieldRefExpr(target=VarRefExpr(name="curr"), field="left")),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="tree_root", primitive="tree_element", label="Cây nhị phân"),
            VisualContainerBinding(semantic_id="s", primitive="stack_view", label="Ngăn xếp duyệt"),
            VisualContainerBinding(semantic_id="order", primitive="array_strip", label="Kết quả duyệt Preorder"),
        ],
    ),
)

# ── 12. Duyệt cây nhị phân trung thứ tự (Inorder LNR) ─────────────────────
P12_TREE_INORDER = SemanticProgramSpec(
    title="Duyệt cây nhị phân theo thứ tự giữa (Inorder LNR)",
    memory_declarations=[
        MemoryDeclaration(
            name="tree_root",
            type="tree_node",
            initial_value={"val": "B", "left": {"val": "A", "left": None, "right": None}, "right": {"val": "C", "left": None, "right": None}},
        ),
        MemoryDeclaration(name="s", type="stack", element_type="tree_node", initial_value=[]),
        MemoryDeclaration(name="order", type="array", element_type="str", initial_value=[]),
    ],
    statements=[
        AssignStmt(target_var="curr", expr=VarRefExpr(name="tree_root")),
        WhileStmt(
            condition=LogicCond(
                op="or",
                left=NotCond(expr=IsNullCond(expr=VarRefExpr(name="curr"))),
                right=NotCond(expr=IsEmptyCond(container="s")),
            ),
            body=[
                WhileStmt(
                    condition=NotCond(expr=IsNullCond(expr=VarRefExpr(name="curr"))),
                    body=[
                        PushStmt(container="s", val=VarRefExpr(name="curr")),
                        AssignStmt(target_var="curr", expr=FieldRefExpr(target=VarRefExpr(name="curr"), field="left")),
                    ],
                ),
                PopStmt(container="s", dest_var="node"),
                PushStmt(container="order", val=FieldRefExpr(target=VarRefExpr(name="node"), field="val")),
                AssignStmt(target_var="curr", expr=FieldRefExpr(target=VarRefExpr(name="node"), field="right")),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="tree_root", primitive="tree_element", label="Cây nhị phân"),
            VisualContainerBinding(semantic_id="s", primitive="stack_view", label="Ngăn xếp duyệt"),
            VisualContainerBinding(semantic_id="order", primitive="array_strip", label="Kết quả duyệt Inorder"),
        ],
    ),
)

# ── 13. Đổi cơ số 10 sang nhị phân 2 ─────────────────────────────────────
P13_DECIMAL_TO_BINARY = SemanticProgramSpec(
    title="Chuyển đổi số nguyên dương hệ 10 sang hệ nhị phân",
    memory_declarations=[
        MemoryDeclaration(name="n", type="int", initial_value=13),
        MemoryDeclaration(name="s", type="stack", element_type="int", initial_value=[]),
        MemoryDeclaration(name="binary_digits", type="array", element_type="int", initial_value=[]),
    ],
    statements=[
        WhileStmt(
            condition=CompareCond(op=">", left=VarRefExpr(name="n"), right=LiteralExpr(value=0)),
            body=[
                PushStmt(
                    container="s",
                    val=BinaryArithExpr(op="%", left=VarRefExpr(name="n"), right=LiteralExpr(value=2)),
                ),
                AssignStmt(
                    target_var="n",
                    expr=BinaryArithExpr(op="//", left=VarRefExpr(name="n"), right=LiteralExpr(value=2)),
                ),
            ],
        ),
        WhileStmt(
            condition=NotCond(expr=IsEmptyCond(container="s")),
            body=[
                PopStmt(container="s", dest_var="bit"),
                PushStmt(container="binary_digits", val=VarRefExpr(name="bit")),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="s", primitive="stack_view", label="Ngăn xếp lưu số dư"),
            VisualContainerBinding(semantic_id="binary_digits", primitive="array_strip", label="Dãy bit nhị phân"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="n_box", var_ref="n", label="Số n hiện thời"),
        ],
    ),
)

# ── 14. Thao tác Bit: Kiểm tra bit thứ K ──────────────────────────────────
P14_BITWISE_CHECK = SemanticProgramSpec(
    title="Kiểm tra bit thứ K của một số nguyên",
    memory_declarations=[
        MemoryDeclaration(name="num", type="int", initial_value=21),
        MemoryDeclaration(name="k", type="int", initial_value=2),
        MemoryDeclaration(name="bit_val", type="int", initial_value=0),
        MemoryDeclaration(name="bit_is_set", type="bool", initial_value=False),
    ],
    statements=[
        # val = (num // (2**k)) % 2
        AssignStmt(
            target_var="bit_val",
            expr=BinaryArithExpr(
                op="%",
                left=BinaryArithExpr(op="//", left=VarRefExpr(name="num"), right=LiteralExpr(value=4)), # 2^2 = 4
                right=LiteralExpr(value=2),
            ),
        ),
        IfStmt(
            condition=CompareCond(op="==", left=VarRefExpr(name="bit_val"), right=LiteralExpr(value=1)),
            then_body=[
                AssignStmt(target_var="bit_is_set", expr=LiteralExpr(value=True)),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        value_boxes=[
            VisualValueBoxBinding(box_id="num_box", var_ref="num", label="Số nguyên"),
            VisualValueBoxBinding(box_id="k_box", var_ref="k", label="Vị trí bit k"),
            VisualValueBoxBinding(box_id="res_box", var_ref="bit_is_set", label="Bit bật?"),
        ],
    ),
)

# ── 15. Duyệt ma trận 2 chiều ─────────────────────────────────────────────
P15_MATRIX_TRAVERSAL = SemanticProgramSpec(
    title="Duyệt và tính tổng ma trận 2 chiều",
    memory_declarations=[
        MemoryDeclaration(
            name="grid",
            type="matrix",
            element_type="int",
            initial_value=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        ),
        MemoryDeclaration(name="rows", type="int", initial_value=3),
        MemoryDeclaration(name="cols", type="int", initial_value=3),
        MemoryDeclaration(name="total_sum", type="int", initial_value=0),
    ],
    statements=[
        ForRangeStmt(
            loop_var="r",
            start=LiteralExpr(value=0),
            end=VarRefExpr(name="rows"),
            body=[
                ForRangeStmt(
                    loop_var="c",
                    start=LiteralExpr(value=0),
                    end=VarRefExpr(name="cols"),
                    body=[
                        AssignStmt(
                            target_var="total_sum",
                            expr=BinaryArithExpr(
                                op="+",
                                left=VarRefExpr(name="total_sum"),
                                right=IndexRefExpr(
                                    container="grid",
                                    index=VarRefExpr(name="r"),
                                    second_index=VarRefExpr(name="c"),
                                ),
                            ),
                        ),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="grid", primitive="table_grid", label="Ma trận bảng số"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="sum_box", var_ref="total_sum", label="Tổng tích lũy"),
        ],
    ),
)

# ── 16. Máy trạng thái hữu hạn (DFA Identifier Lexer) ─────────────────────
P16_DFA_LEXER = SemanticProgramSpec(
    title="Máy trạng thái hữu hạn: Nhận diện tên định danh (Identifier)",
    memory_declarations=[
        MemoryDeclaration(name="chars", type="array", element_type="str", initial_value=["v", "a", "r", "1"]),
        MemoryDeclaration(name="state", type="str", initial_value="START"),
        MemoryDeclaration(
            name="trans",
            type="map",
            key_type="str",
            val_type="str",
            initial_value={"START:v": "ID", "ID:a": "ID", "ID:r": "ID", "ID:1": "ID"},
        ),
        MemoryDeclaration(name="is_valid", type="bool", initial_value=False),
    ],
    statements=[
        ForEachStmt(
            item_var="ch",
            container_or_expr="chars",
            body=[
                AssignStmt(
                    target_var="state",
                    expr=MapGetExpr(
                        container="trans",
                        key=BinaryArithExpr(
                            op="+",
                            left=BinaryArithExpr(
                                op="+",
                                left=VarRefExpr(name="state"),
                                right=LiteralExpr(value=":"),
                            ),
                            right=VarRefExpr(name="ch"),
                        ),
                        default=LiteralExpr(value="ERROR"),
                    ),
                ),
                IfStmt(
                    condition=CompareCond(op="==", left=VarRefExpr(name="state"), right=LiteralExpr(value="ERROR")),
                    then_body=[BreakStmt()],
                ),
            ],
        ),
        IfStmt(
            condition=CompareCond(op="==", left=VarRefExpr(name="state"), right=LiteralExpr(value="ID")),
            then_body=[
                AssignStmt(target_var="is_valid", expr=LiteralExpr(value=True)),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="chars", primitive="array_strip", label="Chuỗi đầu vào"),
        ],
        pointers=[
            # BỎ 2026-08-20 (bất biến #34): con trỏ buộc vào BIẾN KÝ TỰ của
            # `for_each` — không có chỉ số nên không bao giờ neo được vào ô nào,
            # và nó chính là con trỏ trôi đè lên chữ ở spec §0(b).
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="state_box", var_ref="state", label="Trạng thái DFA"),
            VisualValueBoxBinding(box_id="valid_box", var_ref="is_valid", label="Tên định danh hợp lệ?"),
        ],
    ),
)

# ── 17. Mảng cộng dồn (Prefix Sum Array) ──────────────────────────────────
P17_PREFIX_SUM = SemanticProgramSpec(
    title="Mảng cộng dồn (Prefix Sum Array)",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[2, 4, 1, 7, 3]),
        MemoryDeclaration(name="pref", type="array", element_type="int", initial_value=[0, 0, 0, 0, 0]),
        MemoryDeclaration(name="n", type="int", initial_value=5),
    ],
    statements=[
        WriteIndexStmt(
            container="pref",
            index=LiteralExpr(value=0),
            val=IndexRefExpr(container="arr", index=LiteralExpr(value=0)),
        ),
        ForRangeStmt(
            loop_var="i",
            start=LiteralExpr(value=1),
            end=VarRefExpr(name="n"),
            body=[
                WriteIndexStmt(
                    container="pref",
                    index=VarRefExpr(name="i"),
                    val=BinaryArithExpr(
                        op="+",
                        left=IndexRefExpr(
                            container="pref",
                            index=BinaryArithExpr(op="-", left=VarRefExpr(name="i"), right=LiteralExpr(value=1)),
                        ),
                        right=IndexRefExpr(container="arr", index=VarRefExpr(name="i")),
                    ),
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Mảng gốc A"),
            VisualContainerBinding(semantic_id="pref", primitive="array_strip", label="Mảng cộng dồn Prefix"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_i", var_ref="i", target_container="arr", label="i"),
        ],
    ),
)

# ── 18. Bảng đếm tần suất ký tự ──────────────────────────────────────────
P18_FREQUENCY_COUNT = SemanticProgramSpec(
    title="Bảng đếm tần suất ký tự",
    memory_declarations=[
        MemoryDeclaration(name="text", type="array", element_type="str", initial_value=["a", "b", "a", "c", "a", "b"]),
        MemoryDeclaration(name="freq", type="map", key_type="str", val_type="int", initial_value={}),
        MemoryDeclaration(name="count", type="int", initial_value=0),
    ],
    statements=[
        ForEachStmt(
            item_var="ch",
            container_or_expr="text",
            body=[
                AssignStmt(
                    target_var="count",
                    expr=BinaryArithExpr(
                        op="+",
                        left=MapGetExpr(container="freq", key=VarRefExpr(name="ch"), default=LiteralExpr(value=0)),
                        right=LiteralExpr(value=1),
                    ),
                ),
                MapSetStmt(
                    container="freq",
                    key=VarRefExpr(name="ch"),
                    val=VarRefExpr(name="count"),
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="text", primitive="array_strip", label="Dãy ký tự đầu vào"),
            # THÊM 2026-08-23. Trước đó `freq` — chính BẢNG TẦN SUẤT mà bài mang
            # tên — không có binding nào: mô phỏng hiện chuỗi vào và một số đếm,
            # còn bảng thì không bao giờ xuất hiện. Bỏ trống không phải do quên
            # mà vì `map` chưa có primitive nào biểu diễn được; `learner_surface`
            # phơi ra cả hai điều đó cùng lúc.
            VisualContainerBinding(semantic_id="freq", primitive="map_view", label="Bảng tần suất"),
        ],
        pointers=[
            # BỎ 2026-08-20 (bất biến #34): con trỏ buộc vào BIẾN KÝ TỰ của
            # `for_each` — không có chỉ số nên không bao giờ neo được vào ô nào,
            # và nó chính là con trỏ trôi đè lên chữ ở spec §0(b).
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="cnt_box", var_ref="count", label="Tần suất hiện thời"),
        ],
    ),
)

ALL_18_COVERAGE_FIXTURES: list[SemanticProgramSpec] = [
    P01_STACK_BRACKET,
    P02_FIND_MAX,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
    P05_SELECTION_SORT,
    P06_INSERTION_SORT,
    P07_TWO_SUM_SORTED,
    P08_PALINDROME,
    P09_GRAPH_BFS,
    P10_REVERSE_STRING_STACK,
    P11_TREE_PREORDER,
    P12_TREE_INORDER,
    P13_DECIMAL_TO_BINARY,
    P14_BITWISE_CHECK,
    P15_MATRIX_TRAVERSAL,
    P16_DFA_LEXER,
    P17_PREFIX_SUM,
    P18_FREQUENCY_COUNT,
]
