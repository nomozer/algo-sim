# -*- coding: utf-8 -*-
"""5 UNSEEN LIVE SMOKE FIXTURES: 5 bài toán hoàn toàn mới ngoài 18 bài mẫu.

Dùng để chứng minh khả năng tổng quát hóa (generalization) của SemanticProgramEngine:
1. Đếm số nguyên âm trong chuỗi ký tự (Vowel Count)
2. Tìm số lớn thứ nhì trong mảng (Second Largest)
3. Đổi cơ số 10 sang hệ Hexadecimal 16 bằng Stack (Base 16 Conversion)
4. Xóa phần tử trùng lặp trên mảng đã sắp (Two Pointers In-Place)
5. Trò chơi truyền bóng vòng tròn bằng Hàng đợi (Hot Potato Queue Simulation)
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
    IfStmt,
    WhileStmt,
    ForRangeStmt,
    ForEachStmt,
    BreakStmt,
    ReturnStmt,
    LiteralExpr,
    VarRefExpr,
    IndexRefExpr,
    BinaryArithExpr,
    LengthExpr,
    PeekExpr,
    MapGetExpr,
    CompareCond,
    LogicCond,
    NotCond,
    IsEmptyCond,
    ContainsCond,
)

# ── 1. Đếm số nguyên âm trong xâu ─────────────────────────────────────────
UNSEEN_01_VOWEL_COUNT = SemanticProgramSpec(
    title="Đếm số lượng ký tự nguyên âm trong xâu",
    description="Duyệt từng ký tự và kiểm tra xem có thuộc tập nguyên âm (a, e, i, o, u) hay không.",
    pedagogical_intent="Học sinh hiểu cách dùng mảng tra cứu hoặc bảng băm để kiểm tra điều kiện thành viên.",
    memory_declarations=[
        MemoryDeclaration(name="text", type="array", element_type="str", initial_value=["h", "e", "l", "l", "o", "w", "o", "r", "l", "d"]),
        MemoryDeclaration(name="vowels", type="map", key_type="str", val_type="int", initial_value={"a": 1, "e": 1, "i": 1, "o": 1, "u": 1}),
        MemoryDeclaration(name="vowel_count", type="int", initial_value=0),
    ],
    statements=[
        ForEachStmt(
            item_var="ch",
            container_or_expr="text",
            body=[
                IfStmt(
                    condition=ContainsCond(container="vowels", item=VarRefExpr(name="ch")),
                    then_body=[
                        AssignStmt(
                            target_var="vowel_count",
                            expr=BinaryArithExpr(op="+", left=VarRefExpr(name="vowel_count"), right=LiteralExpr(value=1)),
                        ),
                    ],
                ),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="text", primitive="array_strip", label="Xâu ký tự"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_c", var_ref="ch", target_container="text", label="ký tự"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="count_box", var_ref="vowel_count", label="Số nguyên âm"),
        ],
    ),
)

# ── 2. Tìm số lớn thứ nhì trong mảng ──────────────────────────────────────
UNSEEN_02_SECOND_LARGEST = SemanticProgramSpec(
    title="Tìm phần tử lớn thứ nhì trong mảng số nguyên",
    description="Quét một lượt qua mảng và duy trì 2 biến: lớn nhất và lớn thứ nhì.",
    pedagogical_intent="Học sinh nắm vững kỹ thuật duy trì nhiều mốc cực trị trong một lần duyệt tuyến tính.",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[10, 40, 20, 50, 30]),
        MemoryDeclaration(name="first_max", type="int", initial_value=0),
        MemoryDeclaration(name="second_max", type="int", initial_value=0),
    ],
    statements=[
        AssignStmt(target_var="first_max", expr=IndexRefExpr(container="arr", index=LiteralExpr(value=0))),
        AssignStmt(target_var="second_max", expr=LiteralExpr(value=-1)),
        ForRangeStmt(
            loop_var="i",
            start=LiteralExpr(value=1),
            end=LengthExpr(container="arr"),
            body=[
                IfStmt(
                    condition=CompareCond(
                        op=">",
                        left=IndexRefExpr(container="arr", index=VarRefExpr(name="i")),
                        right=VarRefExpr(name="first_max"),
                    ),
                    then_body=[
                        AssignStmt(target_var="second_max", expr=VarRefExpr(name="first_max")),
                        AssignStmt(target_var="first_max", expr=IndexRefExpr(container="arr", index=VarRefExpr(name="i"))),
                    ],
                    else_body=[
                        IfStmt(
                            condition=LogicCond(
                                op="and",
                                left=CompareCond(
                                    op=">",
                                    left=IndexRefExpr(container="arr", index=VarRefExpr(name="i")),
                                    right=VarRefExpr(name="second_max"),
                                ),
                                right=CompareCond(
                                    op="!=",
                                    left=IndexRefExpr(container="arr", index=VarRefExpr(name="i")),
                                    right=VarRefExpr(name="first_max"),
                                ),
                            ),
                            then_body=[
                                AssignStmt(target_var="second_max", expr=IndexRefExpr(container="arr", index=VarRefExpr(name="i"))),
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
            VisualPointerBinding(pointer_id="ptr_i", var_ref="i", target_container="arr", label="i"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="max1_box", var_ref="first_max", label="Lớn nhất"),
            VisualValueBoxBinding(box_id="max2_box", var_ref="second_max", label="Lớn thứ nhì"),
        ],
    ),
)

# ── 3. Đổi cơ số 10 sang Hexadecimal 16 bằng Stack ─────────────────────────
UNSEEN_03_DECIMAL_TO_HEX = SemanticProgramSpec(
    title="Chuyển đổi số nguyên sang hệ thập lục phân (Hexadecimal Base 16)",
    memory_declarations=[
        MemoryDeclaration(name="n", type="int", initial_value=43), # 43 -> "2B"
        MemoryDeclaration(name="s", type="stack", element_type="str", initial_value=[]),
        MemoryDeclaration(
            name="hex_map",
            type="map",
            key_type="str",
            val_type="str",
            initial_value={"10": "A", "11": "B", "12": "C", "13": "D", "14": "E", "15": "F"},
        ),
        MemoryDeclaration(name="hex_digits", type="array", element_type="str", initial_value=[]),
    ],
    statements=[
        WhileStmt(
            condition=CompareCond(op=">", left=VarRefExpr(name="n"), right=LiteralExpr(value=0)),
            body=[
                AssignStmt(
                    target_var="rem",
                    expr=BinaryArithExpr(op="%", left=VarRefExpr(name="n"), right=LiteralExpr(value=16)),
                ),
                IfStmt(
                    condition=CompareCond(op=">=", left=VarRefExpr(name="rem"), right=LiteralExpr(value=10)),
                    then_body=[
                        PushStmt(
                            container="s",
                            val=MapGetExpr(
                                container="hex_map",
                                key=BinaryArithExpr(op="+", left=LiteralExpr(value=""), right=VarRefExpr(name="rem")),
                                default=LiteralExpr(value="?"),
                            ),
                        ),
                    ],
                    else_body=[
                        PushStmt(
                            container="s",
                            val=BinaryArithExpr(op="+", left=LiteralExpr(value=""), right=VarRefExpr(name="rem")),
                        ),
                    ],
                ),
                AssignStmt(
                    target_var="n",
                    expr=BinaryArithExpr(op="//", left=VarRefExpr(name="n"), right=LiteralExpr(value=16)),
                ),
            ],
        ),
        WhileStmt(
            condition=NotCond(expr=IsEmptyCond(container="s")),
            body=[
                PopStmt(container="s", dest_var="ch"),
                PushStmt(container="hex_digits", val=VarRefExpr(name="ch")),
            ],
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="s", primitive="stack_view", label="Ngăn xếp số dư"),
            VisualContainerBinding(semantic_id="hex_digits", primitive="array_strip", label="Ký tự Hexadecimal"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="n_box", var_ref="n", label="Số n hiện thời"),
        ],
    ),
)

# ── 4. Xóa phần tử trùng lặp trên mảng đã sắp ──────────────────────────────
UNSEEN_04_REMOVE_DUPLICATES = SemanticProgramSpec(
    title="Xóa phần tử trùng lặp trong mảng đã sắp thứ tự (In-Place)",
    memory_declarations=[
        MemoryDeclaration(name="arr", type="array", element_type="int", initial_value=[1, 1, 2, 2, 3, 4, 4]),
        MemoryDeclaration(name="slow", type="int", initial_value=0),
        MemoryDeclaration(name="fast", type="int", initial_value=1),
        MemoryDeclaration(name="unique_count", type="int", initial_value=1),
    ],
    statements=[
        ForRangeStmt(
            loop_var="fast",
            start=LiteralExpr(value=1),
            end=LengthExpr(container="arr"),
            body=[
                IfStmt(
                    condition=CompareCond(
                        op="!=",
                        left=IndexRefExpr(container="arr", index=VarRefExpr(name="fast")),
                        right=IndexRefExpr(container="arr", index=VarRefExpr(name="slow")),
                    ),
                    then_body=[
                        AssignStmt(
                            target_var="slow",
                            expr=BinaryArithExpr(op="+", left=VarRefExpr(name="slow"), right=LiteralExpr(value=1)),
                        ),
                        WriteIndexStmt(
                            container="arr",
                            index=VarRefExpr(name="slow"),
                            val=IndexRefExpr(container="arr", index=VarRefExpr(name="fast")),
                        ),
                    ],
                ),
            ],
        ),
        AssignStmt(
            target_var="unique_count",
            expr=BinaryArithExpr(op="+", left=VarRefExpr(name="slow"), right=LiteralExpr(value=1)),
        ),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="arr", primitive="array_strip", label="Mảng số"),
        ],
        pointers=[
            VisualPointerBinding(pointer_id="ptr_slow", var_ref="slow", target_container="arr", label="slow"),
            VisualPointerBinding(pointer_id="ptr_fast", var_ref="fast", target_container="arr", label="fast"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="cnt_box", var_ref="unique_count", label="Số phần tử phân biệt"),
        ],
    ),
)

# ── 5. Trò chơi truyền bóng vòng tròn Hot Potato bằng Hàng đợi ────────────
UNSEEN_05_HOT_POTATO = SemanticProgramSpec(
    title="Trò chơi truyền bóng vòng tròn (Hot Potato) bằng Hàng đợi",
    memory_declarations=[
        MemoryDeclaration(name="q", type="queue", element_type="str", initial_value=["An", "Bình", "Cường", "Dũng", "Em"]),
        MemoryDeclaration(name="k", type="int", initial_value=2),
        MemoryDeclaration(name="winner", type="str", initial_value=""),
    ],
    statements=[
        WhileStmt(
            condition=CompareCond(op=">", left=LengthExpr(container="q"), right=LiteralExpr(value=1)),
            body=[
                # Truyền k-1 lượt từ đầu hàng đợi xuống cuối hàng đợi
                ForRangeStmt(
                    loop_var="step",
                    start=LiteralExpr(value=1),
                    end=VarRefExpr(name="k"),
                    body=[
                        DequeueStmt(container="q", dest_var="passed"),
                        EnqueueStmt(container="q", val=VarRefExpr(name="passed")),
                    ],
                ),
                # Lượt thứ k: người cầm bóng bị loại
                DequeueStmt(container="q", dest_var="eliminated"),
            ],
        ),
        DequeueStmt(container="q", dest_var="winner"),
    ],
    visual_bindings=VisualBindings(
        containers=[
            VisualContainerBinding(semantic_id="q", primitive="queue_view", label="Hàng đợi người chơi"),
        ],
        value_boxes=[
            VisualValueBoxBinding(box_id="win_box", var_ref="winner", label="Người chiến thắng cuối cùng"),
        ],
    ),
)

ALL_5_UNSEEN_FIXTURES = [
    UNSEEN_01_VOWEL_COUNT,
    UNSEEN_02_SECOND_LARGEST,
    UNSEEN_03_DECIMAL_TO_HEX,
    UNSEEN_04_REMOVE_DUPLICATES,
    UNSEEN_05_HOT_POTATO,
]
