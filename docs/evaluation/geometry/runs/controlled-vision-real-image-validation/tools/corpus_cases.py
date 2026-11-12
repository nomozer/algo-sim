"""Agent transcriptions of the selected VMMU solid-geometry images. Data only.

Authority: AGENT_TRANSCRIBED_UNVERIFIED. Read from the image pixels by the agent, before any OCR output for
these images was inspected. Not human verified, not an independent H-1 reference.

`statement` is the problem text as printed (source typos kept, noted in `source_notes`), with the intended
mathematical notation where the source font is corrupted. `facts` are the mathematically critical items:
(kind, accepted surface forms). A fact counts as recovered when one form occurs in the OCR text after the
normalisation in evaluate_images.py. `key` is the dataset's answer letter, not the agent's.
"""

CASES = {
    247: dict(
        statement="Câu 34. Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, BC = 2a và AA' = 3a (tham khảo hình bên). Khoảng cách giữa hai đường thẳng BD và A'C' bằng",
        choices={"A": "a", "B": "√2a", "C": "2a", "D": "3a"}, tags=["cuboid", "distance_line_line"],
        facts=[("solid", ["ABCD.A'B'C'D'", "ABCD·A'B'C'D'"]), ("length", ["AB=a"]), ("length", ["BC=2a"]), ("length", ["AA'=3a"]),
               ("goal", ["Khoảng cách giữa hai đường thẳng"]), ("goal", ["BD"]), ("goal", ["A'C'"])],
        diagram="Labelled cuboid, no measurements.", diagram_facts=[], source_notes=["small print", "centred dot in ABCD·A'B'C'D'", "watermark"]),
    254: dict(
        statement="Câu 45: Cho hình lăng trụ ABC.A'B'C' có AA' = 2√13a, tam giác ABC vuông tại C và ∠ABC = 30°, góc giữa cạnh bên CC' và mặt đáy (ABC) bằng 60°. Hình chiếu vuông góc của B' lên mặt phẳng (ABC) trùng với trọng tâm của tam giác ABC. Thể tích của khối tứ diện A'ABC theo a bằng",
        choices={"A": "33√39a³/4", "B": "9√13a³/2", "C": "99√13a³/8", "D": "27√13a³/2"}, tags=["oblique_prism", "volume"],
        facts=[("solid", ["ABC.A'B'C'"]), ("length", ["AA'=2√13a"]), ("relation", ["vuông tại C"]), ("angle", ["ABC=30°"]),
               ("relation", ["CC'"]), ("angle", ["bằng 60°"]), ("relation", ["Hình chiếu vuông góc của B'"]), ("relation", ["trọng tâm"]),
               ("goal", ["A'ABC"]), ("goal", ["Thể tích"])],
        diagram="Oblique triangular prism with G and M marked.", diagram_facts=[],
        source_notes=["SOURCE_GLYPH_CORRUPTION: several primes are printed as a cent sign and the angle hat as a grave accent", "watermark over text"]),
    256: dict(
        statement="Câu 38: Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh bằng a, ∠BAD = 120°. Mặt bên SAB là tam giác đều và (SAB) ⊥ (ABCD) (tham khảo hình vẽ). Tính khoảng cách từ A đên (SBC)",
        choices={"A": "a√15/5", "B": "a√7/7", "C": "a/2", "D": "√3a/4"}, tags=["pyramid", "distance_point_plane"],
        facts=[("solid", ["S.ABCD"]), ("relation", ["hình thoi"]), ("length", ["cạnh bằng a"]), ("angle", ["BAD=120°"]),
               ("relation", ["SAB là tam giác đều"]), ("relation", ["(SAB)⊥(ABCD)"]), ("goal", ["khoảng cách từ A"]), ("goal", ["(SBC)"])],
        diagram="Pyramid with H on AB.", diagram_facts=[], source_notes=["small print", "source typo 'đên'", "page footer inside the image"]),
    258: dict(
        statement="Câu 30. Cho hình chóp S.ABC có đáy là tam giác vuông cân tại A, SA vuông góc với đáy và SA = AB (tham khảo hình vẽ). Tang của góc giữa hai mặt phẳng (SBC) và (SBA) bằng",
        choices={"A": "√2/2", "B": "1/2", "C": "2", "D": "√2"}, tags=["pyramid", "dihedral"],
        facts=[("solid", ["S.ABC"]), ("relation", ["vuông cân tại A"]), ("relation", ["SA vuông góc với đáy"]), ("length", ["SA=AB"]),
               ("goal", ["Tang"]), ("goal", ["(SBC)"]), ("goal", ["(SBA)"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=[]),
    266: dict(
        statement="Câu 12. Cho khối chóp S.ABC có SA vuông góc với đáy, SA = 3, AB = 3, CB = 4 và ∠ABC = 30°. Thể tích khối chóp đã cho bằng",
        choices={"A": "9", "B": "1", "C": "6", "D": "3"}, tags=["pyramid", "volume"],
        facts=[("solid", ["S.ABC"]), ("relation", ["SA vuông góc với đáy"]), ("length", ["SA=3"]), ("length", ["AB=3"]), ("length", ["CB=4"]),
               ("angle", ["ABC=30°"]), ("goal", ["Thể tích"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=["degree printed as superscript zero", "angle written with a wide hat"]),
    270: dict(
        statement="Câu 43. Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B với BC = a biết mặt phẳng (A'BC) hợp với đáy (ABC) một góc 60° (tham khảo hình bên). Tính thể tích lăng trụ ABC.A'B'C'.",
        choices={"A": "a³√3/2", "B": "a³√3/6", "C": "a³√3", "D": "a³√2/3"}, tags=["right_prism", "volume", "inverse_from_angle"],
        facts=[("solid", ["lăng trụ đứng"]), ("solid", ["ABC.A'B'C'"]), ("relation", ["vuông cân tại B"]), ("length", ["BC=a"]),
               ("relation", ["(A'BC)"]), ("angle", ["góc 60°"]), ("goal", ["thể tích"])],
        diagram="Small labelled prism.", diagram_facts=[], source_notes=["small print", "degree printed as superscript zero"]),
    273: dict(
        statement="Câu 14: Cho khối chóp S.ABC có đáy là tam giác vuông tại B. Biết BC = a√3, AB = a, SA vuông góc với đáy, SA = 2a√3. Thể tích khối chóp S.ABC bằng",
        choices={"A": "a³√3", "B": "a³√3/3", "C": "3a³", "D": "a³"}, tags=["pyramid", "volume"],
        facts=[("solid", ["S.ABC"]), ("relation", ["vuông tại B"]), ("length", ["BC=a√3"]), ("length", ["AB=a"]),
               ("relation", ["SA vuông góc với đáy"]), ("length", ["SA=2a√3"]), ("goal", ["Thể tích"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=[]),
    277: dict(
        statement="Câu 44. Cho tứ diện OABC vuông tại O có OA = 2a, OB = 3a, OC = 4a. Gọi M, N, P lần lượt là điểm đối xứng với điểm O qua trung điểm ba cạnh AB, BC, CA của tam giác ABC. Thể tích của tứ diện OMNP bằng",
        choices={"A": "16a³", "B": "4a³", "C": "8a³", "D": "12a³"}, tags=["tetrahedron", "volume", "point_reflection"],
        facts=[("solid", ["OABC"]), ("relation", ["vuông tại O"]), ("length", ["OA=2a"]), ("length", ["OB=3a"]), ("length", ["OC=4a"]),
               ("relation", ["đối xứng"]), ("relation", ["trung điểm"]), ("goal", ["OMNP"]), ("goal", ["Thể tích"])],
        diagram="Tetrahedron with reflected points M, N, P and midpoints D, E, F.", diagram_facts=[], source_notes=[]),
    284: dict(
        statement="Câu 36. Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy (minh họa như hình vẽ bên). Khoảng cách từ A đến mặt phẳng (SBD) bằng",
        choices={"A": "√21a/14", "B": "√21a/28", "C": "√2a/2", "D": "√21a/7"}, tags=["pyramid", "distance_point_plane"],
        facts=[("solid", ["S.ABCD"]), ("length", ["hình vuông cạnh a"]), ("relation", ["SAB là tam giác đều"]),
               ("relation", ["vuông góc với mặt phẳng đáy"]), ("goal", ["Khoảng cách từ A"]), ("goal", ["(SBD)"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=["watermark over the first two text lines"]),
    295: dict(
        statement="Câu 35. Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy là hình vuông, AB = 1, AA' = √6 (tham khảo hình vẽ). Góc giữa đường thẳng CA' và mặt phẳng (ABCD) bằng",
        choices={"A": "30°", "B": "45°", "C": "60°", "D": "90°"}, tags=["cuboid", "angle_line_plane"],
        facts=[("solid", ["ABCD.A'B'C'D'"]), ("relation", ["đáy là hình vuông"]), ("length", ["AB=1"]), ("length", ["AA'=√6"]),
               ("goal", ["Góc giữa đường thẳng"]), ("goal", ["CA'"]), ("goal", ["(ABCD)"])],
        diagram="Labelled cuboid with diagonal.", diagram_facts=[], source_notes=[]),
    298: dict(
        statement="Câu 42. Cho hình lăng trụ tam giác đều ABC.A'B'C' có cạnh đáy bằng 2a, góc giữa hai đường thẳng AB' và BC' bằng 60° (tham khảo hình vẽ bên dưới). Tính thể tích V của khối lăng trụ đó.",
        choices={"A": "V = 2√6a³/3", "B": "V = 2√6a³", "C": "V = 2√3a³/3", "D": "V = 2√3a³"}, tags=["regular_prism", "volume", "inverse_from_angle"],
        facts=[("solid", ["lăng trụ tam giác đều"]), ("solid", ["ABC.A'B'C'"]), ("length", ["cạnh đáy bằng 2a"]), ("relation", ["AB'"]),
               ("relation", ["BC'"]), ("angle", ["bằng 60°"]), ("goal", ["thể tích"])],
        diagram="Labelled prism.", diagram_facts=[], source_notes=["degree printed as superscript zero"]),
    375: dict(
        statement="Câu 36. Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh đáy bằng 4 và độ dài cạnh bên bằng 5 (tham khảo hình vẽ). Khoảng cách từ S đến mặt phẳng (ABCD) bằng",
        choices={"A": "√21", "B": "1", "C": "√17", "D": "3"}, tags=["regular_pyramid", "distance_point_plane"],
        facts=[("solid", ["chóp tứ giác đều"]), ("solid", ["S.ABCD"]), ("length", ["cạnh đáy bằng 4"]), ("length", ["cạnh bên bằng 5"]),
               ("goal", ["Khoảng cách từ S"]), ("goal", ["(ABCD)"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=["watermark behind the figure"]),
    460: dict(
        statement="Câu 33: Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, cạnh AC = 2a. Cạnh SA vuông góc với mặt đáy (ABC), tam giác SAB cân. Thể tích khối chóp S.ABC theo a bằng",
        choices={"A": "2a³√2", "B": "a³√2", "C": "a³√2/3", "D": "2a³√2/3"}, tags=["pyramid", "volume", "hypotenuse_given"],
        facts=[("solid", ["S.ABC"]), ("relation", ["vuông cân ở B"]), ("length", ["AC=2a"]), ("relation", ["SA vuông góc với mặt đáy"]),
               ("relation", ["SAB cân"]), ("goal", ["Thể tích"])],
        diagram="Labelled pyramid beside the choices.", diagram_facts=[], source_notes=["last word clipped at the image edge"]),
    461: dict(
        statement="Câu 46. Để làm một cái mũ sinh nhật người ta lấy một miếng giấy hình tam giác ABC đều cạnh 3 dm (như hình vẽ). Gọi K là trung điểm của BC. Người ta dùng compa có tâm là A và bán kính AK vạch cung tròn MN (M, N thứ tự thuộc cạnh AB và AC) rồi cắt miếng giấy theo cung tròn đó. Lấy phần hình quạt người ta gián sao cho cạnh AM và AN trùng nhau thành một cái mũ hình nón không đáy với đỉnh A. Thể tích của cái mũ gần với giá trị nào nhất?",
        choices={"A": "0,5 dm³", "B": "0,6 dm³", "C": "0,3 dm³", "D": "0,4 dm³"}, tags=["cone", "applied"],
        facts=[("relation", ["tam giác ABC đều"]), ("length", ["cạnh 3dm"]), ("relation", ["trung điểm của BC"]), ("length", ["bán kính AK"]),
               ("solid", ["hình nón"]), ("goal", ["Thể tích"])],
        diagram="Triangle with arc MN and a cone.", diagram_facts=[], source_notes=["source typo 'gián'"]),
    463: dict(
        statement="Câu 43. Cho khối lăng trụ đứng ABCDA'B'C'D' có đáy ABCD là hình thoi, ∠BAD = 60°, cạnh bên AA' = 2a và AC' hợp với đáy góc 30°. Thể tích khối lăng trụ đã cho bằng",
        choices={"A": "2√3a³", "B": "6a³", "C": "4a³", "D": "4√3a³"}, tags=["right_prism", "volume", "inverse_from_angle"],
        facts=[("solid", ["lăng trụ đứng"]), ("solid", ["ABCDA'B'C'D'", "ABCD.A'B'C'D'"]), ("relation", ["hình thoi"]), ("angle", ["BAD=60°"]),
               ("length", ["AA'=2a"]), ("relation", ["AC'"]), ("angle", ["góc 30°"]), ("goal", ["Thể tích"])],
        diagram="Prism drawn with ABCD on top.", diagram_facts=[], source_notes=["solid named without the separating dot", "degree printed as superscript zero"]),
    475: dict(
        statement="Câu 44. Trên bàn có một cốc nước hình trụ chứa đầy nước, có chiều cao bằng 3 lần đường kính của đáy; một viên bi và một khối nón đều bằng thủy tinh. Biết viên bi là một khối cầu có đường kính bằng đường kính của đương tròn đáy cốc nước. Người ta từ từ thả vào cốc nước viên bi và khối nón sao cho đỉnh khối nón nằm trên mặt cầu (như hình vẽ) thì thấy nước trong cốc tràn ra ngoài. Tính tỉ số thể tích của lượng nước còn lại trong cốc và lượng nước ban đầu.",
        choices={"A": "4/9", "B": "5/9", "C": "2/3", "D": "1/2"}, tags=["cylinder_sphere_cone", "applied"],
        facts=[("solid", ["hình trụ"]), ("length", ["3 lần đường kính"]), ("solid", ["khối cầu"]), ("solid", ["khối nón"]), ("goal", ["tỉ số thể tích"])],
        diagram="Cylinder containing a sphere and a cone.", diagram_facts=[], source_notes=["source typo 'đương tròn'"]),
    476: dict(
        statement="Câu 2. Cho hình chóp S.ABCD, có đáy ABCD là hình vuông cạnh a√3, SA = a và SA vuông góc với đáy (tham khảo hình vẽ). Góc giữa hai mặt phẳng (SCD) và (ABCD) bằng",
        choices={"A": "45°", "B": "90°", "C": "60°", "D": "30°"}, tags=["pyramid", "dihedral"],
        facts=[("solid", ["S.ABCD"]), ("length", ["hình vuông cạnh a√3"]), ("length", ["SA=a"]), ("relation", ["SA vuông góc với đáy"]),
               ("goal", ["Góc giữa hai mặt phẳng"]), ("goal", ["(SCD)"]), ("goal", ["(ABCD)"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=["degrees in the choices printed as superscript zero"]),
    488: dict(
        statement="Câu 43: Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông, AB = BC = a. Biết góc giữa hai mặt phẳng (ACC') và (AB'C') bằng 60° (tham khảo hình vẽ bên). Thể tích của khối chóp B'.ACC'A' bằng",
        choices={"A": "a³/3", "B": "a³/2", "C": "√3a³/3", "D": "a³/6"}, tags=["right_prism", "volume", "inverse_from_angle"],
        facts=[("solid", ["lăng trụ đứng"]), ("solid", ["ABC.A'B'C'"]), ("relation", ["tam giác vuông"]), ("length", ["AB=BC=a"]),
               ("relation", ["(ACC')"]), ("relation", ["(AB'C')"]), ("angle", ["bằng 60°"]), ("goal", ["B'.ACC'A'"]), ("goal", ["Thể tích"])],
        diagram="Prism beside the text.", diagram_facts=[], source_notes=["degree printed as superscript zero", "two-column layout: text left, figure right"]),
    491: dict(
        statement="Câu 36: Cho hình lăng trụ ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = a, AC = 2a (tham khảo hình bên). Hình chiếu vuông góc của A' lên mặt phẳng (ABC) là điểm I thuộc cạnh BC. Khoảng cách từ A tới mặt phẳng (A'BC) bằng",
        choices={"A": "2/3 a", "B": "√3/2 a", "C": "1/3 a", "D": "2√5/5 a"}, tags=["oblique_prism", "distance_point_plane"],
        facts=[("solid", ["ABC.A'B'C'"]), ("relation", ["vuông tại A"]), ("length", ["AB=a"]), ("length", ["AC=2a"]),
               ("relation", ["Hình chiếu vuông góc của A'"]), ("relation", ["điểm I thuộc cạnh BC"]), ("goal", ["Khoảng cách từ A"]), ("goal", ["(A'BC)"])],
        diagram="Oblique prism; edge labels 2a and a repeat the text.", diagram_facts=[], source_notes=["two-column layout: text left, figure right", "diagram carries the numeric labels 2a and a"]),
    492: dict(
        statement="Câu 45. Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông tại A. Biết AB = √15a, AC = a và AA' = 2a (tham khảo hình bên dưới). Góc giữa đường thẳng BC' và mặt phẳng (ACC'A') bằng",
        choices={"A": "60°", "B": "45°", "C": "30°", "D": "90°"}, tags=["right_prism", "angle_line_plane"],
        facts=[("solid", ["lăng trụ đứng"]), ("solid", ["ABC.A'B'C'"]), ("relation", ["vuông tại A"]), ("length", ["AB=√15a"]), ("length", ["AC=a"]),
               ("length", ["AA'=2a"]), ("goal", ["Góc giữa đường thẳng"]), ("goal", ["BC'"]), ("goal", ["(ACC'A')"])],
        diagram="Small labelled prism.", diagram_facts=[], source_notes=["small print"]),
    498: dict(
        statement="Câu 26: Cho hình lăng trụ tứ giác đều ABCD.A'B'C'D' có cạnh đáy bằng a, cạnh bên bằng a√3. Tính cosin của góc giữa hai mặt phẳng (ABCD) và (ABC')?",
        choices={"A": "30°", "B": "1/2", "C": "60°", "D": "√3/2"}, tags=["regular_prism", "dihedral"],
        facts=[("solid", ["lăng trụ tứ giác đều"]), ("solid", ["ABCD.A'B'C'D'"]), ("length", ["cạnh đáy bằng a"]), ("length", ["cạnh bên bằng a√3"]),
               ("goal", ["cosin"]), ("goal", ["(ABCD)"]), ("goal", ["(ABC')"])],
        diagram="Labelled prism with shaded triangle.", diagram_facts=[],
        source_notes=["SOURCE_GLYPH_CORRUPTION: primes in the solid name and in (ABC') are printed as a cent sign"]),
    513: dict(
        statement="Câu 39: Cho hình hộp chữ nhật ABCD.A'B'C'D' có cạnh AA' = 1, AB = 2 Khoảng cách từ điểm A' đến mặt phẳng ADC'B' bằng.",
        choices={"A": "√5", "B": "√5/2", "C": "2√5/5", "D": "√2"}, tags=["cuboid", "distance_point_plane"],
        facts=[("solid", ["ABCD.A'B'C'D'"]), ("length", ["AA'=1"]), ("length", ["AB=2"]), ("goal", ["Khoảng cách từ điểm A'"]), ("goal", ["ADC'B'"])],
        diagram="Small labelled cuboid.", diagram_facts=[], source_notes=["small print", "plane named without parentheses", "sentence break missing after AB = 2"]),
    520: dict(
        statement="Câu 30. Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB (tham khảo hình bên). Góc giữa hai mặt phẳng (SBC) và (ABC) bằng",
        choices={"A": "60°", "B": "30°", "C": "90°", "D": "45°"}, tags=["pyramid", "dihedral"],
        facts=[("solid", ["S.ABC"]), ("relation", ["vuông tại B"]), ("relation", ["SA vuông góc với đáy"]), ("length", ["SA=AB"]),
               ("goal", ["Góc giữa hai mặt phẳng"]), ("goal", ["(SBC)"]), ("goal", ["(ABC)"])],
        diagram="Large labelled pyramid.", diagram_facts=[],
        source_notes=["small print with raised inline formulas", "SOURCE_GLYPH_CORRUPTION: degree signs in the choices are printed as a box"]),
    537: dict(
        statement="Câu 39: Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng a và diện tích đáy bằng a² (tham khảo hình bên dưới). Khoảng cách từ A đến mặt phẳng (SBC) bằng",
        choices={"A": "a√6", "B": "a√6/2", "C": "a√6/3", "D": "a√6/6"}, tags=["regular_pyramid", "distance_point_plane"],
        facts=[("solid", ["chóp tứ giác đều"]), ("solid", ["S.ABCD"]), ("length", ["cạnh bên bằng a"]), ("length", ["diện tích đáy bằng a²"]),
               ("goal", ["Khoảng cách từ A"]), ("goal", ["(SBC)"])],
        diagram="Labelled pyramid.", diagram_facts=[], source_notes=[]),
    538: dict(
        statement="Câu 26. Cho hình chóp tam giác đều S.ABC và có cạnh đáy bằng a, cạnh bên bằng 2a/3 (tham khảo hình vẽ bên). Góc giữa cạnh bên và mặt đáy bằng",
        choices={"A": "90°", "B": "45°", "C": "30°", "D": "60°"}, tags=["regular_pyramid", "angle_line_plane"],
        facts=[("solid", ["chóp tam giác đều"]), ("solid", ["S.ABC"]), ("length", ["cạnh đáy bằng a"]), ("length", ["cạnh bên bằng 2a/3"]),
               ("goal", ["Góc giữa cạnh bên và mặt đáy"])],
        diagram="Labelled pyramid beside the text.", diagram_facts=[], source_notes=["stacked fraction 2a over 3", "two-column layout: text left, figure right"]),
}

# Answers the agent derived by hand, independently of the dataset key and of any Axo output (see report for working).
AGENT_DERIVED_LETTER = {247: "D", 256: "A", 258: "D", 266: "D", 270: "A", 273: "D", 284: "D", 295: "C", 375: "C", 460: "C",
                        463: "D", 476: "D", 491: "D", 492: "A", 498: "B", 513: "C", 520: "D", 537: "C", 538: "C"}
OUT_OF_SCOPE_BY_DOMAIN = {461: "cone built from a paper sector", 475: "cylinder, sphere and cone displacement"}
