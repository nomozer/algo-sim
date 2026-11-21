"""Agent transcriptions and scope decisions for the 48 pre-registered fresh VMMU rows. Data only.

Authority: AGENT_TRANSCRIBED_UNVERIFIED. Every sampled image was viewed on the contact sheets (none filtered by
keywords) before any OCR or Axo output for these images existed. Scope is decided from the image by the rule in
fresh_external_preregistration.json. `key` comes from the dataset; the agent's hand derivation is kept apart.
"""

CASES = {
    559: dict(
        statement="Câu 45. Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Côsin của góc giữa hai đường thẳng AC và BM bằng",
        choices={"A": "√3", "B": "√3/6", "C": "√3/2", "D": "√3/3"}, tags=["regular_tetrahedron", "angle_line_line", "cosine_output", "scale_free"],
        facts=[("solid", ["tứ diện đều"]), ("solid", ["ABCD"]), ("relation", ["M là trung điểm của CD"]),
               ("goal", ["Côsin"]), ("goal", ["góc giữa hai đường thẳng AC và BM"])],
        diagram="Labelled tetrahedron with M on CD, no measurements.", source_notes=["no edge length given (answer is scale-free)"]),
    695: dict(
        statement="Câu 36. Cho hình chóp S.ABCD có SA ⊥ (ABCD), đáy ABCD là hình vuông, biết AB = 1, SA = 2 (tham khảo hình vẽ bên dưới). Khoảng cách từ điểm C đến mặt phẳng (SBD) bằng",
        choices={"A": "√2/2", "B": "2/3", "C": "3/2", "D": "√2"}, tags=["pyramid", "distance_point_plane"],
        facts=[("solid", ["S.ABCD"]), ("relation", ["SA⊥(ABCD)"]), ("relation", ["hình vuông"]), ("length", ["AB=1"]), ("length", ["SA=2"]),
               ("goal", ["Khoảng cách từ điểm C"]), ("goal", ["(SBD)"])],
        diagram="Labelled pyramid, no measurements.", source_notes=["watermark over the first line"]),
}

# Hand derivations (independent of Axo): r559 AC ⟂ BD in a regular tetrahedron, AC·BM = (AC·BC + AC·BD)/2 = 1/4,
# |BM| = √3/2 -> √3/6. r695 d(C,(SBD)) = d(A,(SBD)) by symmetry about BD; 1/d² = 1 + 1 + 1/4 -> 2/3.
AGENT_DERIVED_LETTER = {559: "B", 695: "B"}

_FN = "function / calculus problem (graph, variation table, extremum, equation roots), not solid geometry"
NOT_IN_SCOPE = {
    541: _FN, 542: "integral and area under a derivative graph", 543: _FN, 544: _FN, 546: _FN, 549: _FN, 553: _FN, 554: _FN,
    560: _FN, 565: "plane area between a line and a parabola", 568: _FN, 572: _FN, 577: _FN, 578: _FN, 580: _FN, 582: _FN,
    586: _FN, 589: _FN, 594: _FN, 599: _FN, 606: _FN, 607: _FN, 609: _FN, 610: _FN, 626: _FN, 632: _FN, 635: _FN, 636: _FN,
    638: _FN, 642: _FN, 644: _FN, 647: _FN, 649: _FN, 652: _FN, 654: _FN, 658: "plane area between a line and y = √x", 660: _FN,
    662: "plane optimisation word problem (boat and walk)", 665: _FN, 669: _FN,
    677: "recognise which drawing is not a polyhedron: no metric question",
    684: _FN, 686: "cylinder inscribed in a sphere, maximise volume: curved solids with optimisation", 689: _FN,
    691: "exponential function graphs", 693: _FN,
}
