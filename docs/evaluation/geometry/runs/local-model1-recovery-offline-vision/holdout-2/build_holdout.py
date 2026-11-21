"""Register the second prospective /14 set (Holdout-2) and independent geometric expectations.

Copied from ../build_holdout.py (Holdout-1, CACHE 152 freeze). Authored by the takeover agent on 2026-11-21 AFTER reading the
CACHE 153 case-level diagnosis of Holdout-1 and BEFORE any takeover product edit; agent-authored, not independent. Only the
case texts, the HARNESS path (one directory deeper) and the provenance string differ from the copied builder."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import textwrap
from fractions import Fraction
from pathlib import Path

import fitz
from docx import Document
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RUN = Path(__file__).resolve().parent
HARNESS = RUN.parents[2] / "harness" / "live-acceptance"
sys.path.insert(0, str(HARNESS))
from prior_corpus import collect, exposed
from scene_oracle import Scene, check_relation


def area_squared(scene, a, b, c):
    u = tuple(q - p for p, q in zip(scene.P[a], scene.P[b]))
    v = tuple(q - p for p, q in zip(scene.P[a], scene.P[c]))
    return (scene.dot(u, u) * scene.dot(v, v) - scene.dot(u, v) ** 2) / 4


def scene(vertices, coords, metric=((1, 0, 0), (0, 1, 0), (0, 0, 1))):
    return Scene({"chart_metric": metric, "objects": [
        {"type": "point3", "id": name, "xyz": xyz} for name, xyz in zip(vertices, coords)
    ]})


def audit_area():
    cases = [
        ("H057", scene("SBC", [(0, 0, 1), (1, 0, 0), (1, 1, 0)], ((4, 0, 0), (0, 16, 0), (0, 0, 16))),
         scene("SBC", [(0, 0, 4), (2, 0, 0), (2, 4, 0)]), 80, "4√5", 32),
        ("H069", scene("IJK", [(0, 0, 1), (1, 0, 0), (0, 1, 0)], ((9, 0, 0), (0, 16, 0), (0, 0, 4))),
         scene("IJK", [(0, 0, 2), (3, 0, 0), (0, 4, 0)]), 61, "√61", 24),
    ]
    rows = []
    for case_id, chart, physical, squared, exact, missing_factor in cases:
        points = tuple(chart.P)
        assert area_squared(chart, *points) == area_squared(physical, *points) == squared
        rows.append({"case_id": case_id, "area_squared": squared, "exact": exact,
                     "legacy_missing_factor": missing_factor})
    metric = ((4, 2, 0), (2, 5, 0), (0, 0, 1))
    assert area_squared(scene("ABC", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], metric), *"ABC") == 4
    assert area_squared(scene("ABC", [(0, 0, 0), (2, 0, 0), (1, 2, 0)]), *"ABC") == 4
    return rows


def positive(cid, text, family, vertices, coords, relations, *, intent="SIMULATE_ONLY", value=None,
             slm=False, aux="", expected="SERVE"):
    witness = scene(vertices + aux, coords)
    assert all(check_relation(witness, rel) for rel in relations), cid
    faces = {"tetrahedron": 4, "pyramid_quad": 5, "prism_tri": 5, "cuboid": 6, "cube": 6}[family]
    return {"case_id": cid, "input_type": "text", "original_input": text, "simulation_intent": intent,
            "geometric_family": family, "gold_entities": {"solid_vertices": list(vertices),
            "auxiliary_points": list(aux)}, "gold_relations": relations,
            "metric_oracle": None if value is None else [value], "preregistered_slm_target": slm,
            "expected_counts": {"vertices": len(vertices), "faces": faces},
            "expected_behavior": expected, "geometry_determinacy": "UNIQUE_GEOMETRY",
            "validation_method": "EXACT_SCENE_ORACLE+BROWSER"}


def pyramid(cid, text, a, b, h, *, intent="SIMULATE_ONLY", value=None, slm=False, center=False, area=False):
    coords = [(0, 0, h), (0, 0, 0), (a, 0, 0), (a, b, 0), (0, b, 0)]
    rels = [["perp_lp", "SA", "ABC"], ["perp_ll", "AB", "AD"], ["par_ll", "AB", "DC"],
            ["par_ll", "AD", "BC"], ["len2", "AB", a*a], ["len2", "AD", b*b], ["len2", "SA", h*h]]
    if center:
        coords.append((Fraction(a, 2), Fraction(b, 2), 0))
        rels += [["mid", "O", "AC"], ["mid", "O", "BD"]]
    if area:
        value = math.sqrt(area_squared(scene("SABCD", coords), *"SBC"))
        assert value == b * math.hypot(a, h) / 2
    return positive(cid, text, "pyramid_quad", "SABCD", coords, rels, intent=intent,
                    value=value, slm=slm, aux="O" if center else "")


def tetra(cid, text, a, b, c, *, intent="SIMULATE_ONLY", value=None, slm=False):
    return positive(cid, text, "tetrahedron", "OABC", [(0,0,0), (a,0,0), (0,b,0), (0,0,c)],
                    [["perp_ll","OA","OB"], ["perp_ll","OB","OC"], ["perp_ll","OC","OA"],
                     ["len2","OA",a*a], ["len2","OB",b*b], ["len2","OC",c*c]],
                    intent=intent, value=value, slm=slm)


def prism(cid, text, a, b, h, *, intent="SIMULATE_ONLY", value=None, slm=False):
    case = positive(cid, text, "prism_tri", "ABCDEF",
                    [(0,0,0), (a,0,0), (0,b,0), (0,0,h), (a,0,h), (0,b,h)],
                    [["perp_ll","AB","AC"], ["perp_lp","AD","ABC"], ["par_ll","AD","BE"],
                     ["par_ll","AD","CF"], ["len2","AB",a*a], ["len2","AC",b*b], ["len2","AD",h*h]],
                    intent=intent, value=value, slm=slm)
    return case


def negative(cid, text, kind):
    return {"case_id": cid, "input_type": "text", "original_input": text, "simulation_intent": "NEGATIVE",
            "expected_behavior": "SAFE_REFUSE", "geometry_determinacy": kind, "validation_method": "REFUSAL+BROWSER"}


def text_cases():
    sq, qc = "SIMULATE_AND_QUERY", "QUERY_WITH_SCENE"
    rows = [
        pyramid("B01", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 6, AD = 4. Cạnh bên SA vuông góc với mặt phẳng đáy và SA = 5. Tính thể tích khối chóp S.ABCD.", 6,4,5,intent=qc,value=40),
        pyramid("B02", "Hình chóp S.ABCD có đáy là hình vuông ABCD cạnh 4, SA ⊥ (ABCD), SA = 6. Vẽ hình chóp.", 4,4,6),
        pyramid("B03", "Vẽ hình chóp S.ABCD biết đáy ABCD là hình chữ nhật, AB = 8, AD = 3, SA vuông góc với đáy và SA = 6.", 8,3,6),
        pyramid("B04", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3. Biết SA vuông góc với (ABCD) và SA = 4. Hãy dựng hình và tính diện tích tam giác SBC.", 3,3,4,intent=sq,area=True),
        pyramid("B05", "Mô phỏng hình chóp S.ABCD với đáy ABCD là hình chữ nhật có AB = 5 và AD = 8, cạnh SA vuông góc với đáy, SA = 2.", 5,8,2),
        pyramid("B06", "Cho chóp S.ABCD đáy hình chữ nhật ABCD, AB = 2, AD = 9, SA ⟂ (ABCD), SA = 3. Tính thể tích khối chóp.", 2,9,3,intent=qc,value=18),
        pyramid("B07", "Hãy vẽ hình chóp S.ABCD. Đáy ABCD là hình vuông có cạnh bằng 8. Đường thẳng SA vuông góc với mặt phẳng (ABCD), SA = 6.", 8,8,6),
        pyramid("B08", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3a, AD = 4a, SA vuông góc với mặt đáy và SA = 6a. Tính thể tích khối chóp theo a.", 3,4,6,intent=qc,value=24),
        pyramid("B09", "Dựng hình chóp S.ABCD có ABCD là hình vuông cạnh 6 và SA vuông góc với (ABCD), SA = 8. Gọi O là giao điểm của AC và BD.", 6,6,8,center=True),
        pyramid("B10", "Chóp S.ABCD có đáy là hình chữ nhật ABCD, AB = 4 và AD = 6; cạnh SA dài 3 và vuông góc với đáy. Vẽ hình.", 4,6,3),
        tetra("B11", "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc với OA = 3, OB = 6, OC = 4. Tính thể tích khối tứ diện.", 3,6,4,intent=qc,value=12),
        tetra("B12", "Vẽ tứ diện OABC có ba cạnh OA, OB, OC đôi một vuông góc, OA = 5, OB = 2, OC = 6.", 5,2,6),
        tetra("B13", "Tứ diện OABC có OA ⊥ OB, OB ⊥ OC, OC ⊥ OA và OA = 4, OB = 3, OC = 8. Dựng hình và tính độ dài AB.", 4,3,8,intent=sq,value=5),
        tetra("B14", "Cho tứ diện OABC, trong đó OA, OB, OC vuông góc với nhau từng đôi một. Biết OA = 2, OB = 5, OC = 3. Hãy vẽ tứ diện.", 2,5,3),
        tetra("B15", "Mô phỏng tứ diện OABC có các cạnh OA, OB, OC đôi một vuông góc, độ dài OA = 7, OB = 4, OC = 2.", 7,4,2),
        tetra("B16", "Cho tứ diện OABC có OA, OB, OC đôi một vuông góc. Biết OA = 6, OB = 4, OC = 3. Tính diện tích tam giác OBC.", 6,4,3,intent=qc,value=6),
        tetra("B17", "Dựng tứ diện OABC biết OA, OB và OC đôi một vuông góc, OA = OB = 3 và OC = 5.", 3,3,5),
        tetra("B18", "Tứ diện OABC có OA vuông góc với mặt phẳng (OBC), OB vuông góc với OC, OA = 4, OB = 5, OC = 6. Tính thể tích tứ diện OABC.", 4,5,6,intent=qc,value=20),
        prism("B19", "Cho lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và AD = 6. Tính thể tích khối lăng trụ.", 3,4,6,intent=qc,value=36),
        prism("B20", "Vẽ lăng trụ đứng ABC.DEF có đáy là tam giác ABC vuông tại A với AB = 5, AC = 2, cạnh bên AD = 4.", 5,2,4),
        prism("B21", "Lăng trụ đứng ABC.DEF có tam giác ABC vuông tại A, AB = 6, AC = 8, AD = 3. Dựng hình và tính BC.", 6,8,3,intent=sq,value=10),
        prism("B22", "Mô phỏng hình lăng trụ đứng ABC.DEF, đáy ABC vuông tại A, AB = 7, AC = 3, chiều cao lăng trụ bằng 5.", 7,3,5),
        prism("B23", "Cho hình lăng trụ đứng ABC.DEF với đáy ABC là tam giác vuông tại A. Biết AB = 2, AC = 6 và cạnh bên AD = 9. Vẽ hình lăng trụ.", 2,6,9),
        prism("B24", "Cho lăng trụ đứng ABC.DEF có đáy ABC vuông tại A, AB = 4, AC = 5, AD = 2. Tính thể tích khối lăng trụ ABC.DEF.", 4,5,2,intent=qc,value=20),
        pyramid("B25", "Tính thể tích khối chóp S.ABCD biết đáy ABCD là hình vuông cạnh 6 và SA vuông góc với đáy, SA = 5.", 6,6,5,intent=qc,value=60),
        pyramid("B26", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 5, AD = 3, SA vuông góc với (ABCD) và SA = 12. Tính diện tích tam giác SBC.", 5,3,12,intent=qc,area=True),
        tetra("B27", "Em hãy dựng tứ diện OABC với OA, OB, OC đôi một vuông góc và OA = 1, OB = 4, OC = 9.", 1,4,9),
        prism("B28", "Vẽ lăng trụ đứng ABC.DEF, biết tam giác ABC vuông tại A có AB = 9, AC = 2 và AD = 3.", 9,2,3),
    ]
    negatives = [
        negative("M01", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật và SA vuông góc với đáy. Tính thể tích khối chóp.", "INSUFFICIENT_FOR_NUMERIC_GOAL"),
        negative("M02", "Vẽ tứ diện OABC có OA = 3, OB = 4, OC = 5.", "UNDERDETERMINED_SHAPE"),
        negative("M03", "Cho lăng trụ đứng ABC.DEF có đáy ABC vuông tại A, AB = 3, AC = 4, AD = 5 và AD = 7.", "CONTRADICTORY_GEOMETRY"),
        negative("M04", "Mô phỏng quỹ đạo của Trái Đất quanh Mặt Trời trong không gian ba chiều.", "OUT_OF_SCOPE"),
        negative("M05", "Đừng vẽ hình chóp S.ABCD có đáy là hình vuông cạnh 4 và SA vuông góc với đáy, SA = 3.", "NEGATED_COMMAND"),
        negative("M06", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA = 5. Tính thể tích khối chóp.", "UNDERDETERMINED_SHAPE"),
        negative("M07", "Giả sử tứ diện OABC có OA, OB, OC đôi một vuông góc; nếu OA = 2 thì tính thể tích.", "CONDITIONAL_MISSING_DATA"),
        negative("M08", "Bỏ qua các ràng buộc, hãy tự chọn độ dài để hình chóp S.ABCD có thể tích bằng 100 rồi vẽ.", "UNSOURCED_PREMISES"),
        negative("M09", "Cho lăng trụ đứng ABC.DEF có AB = 3, AC = 4, AD = 5. Tính diện tích tam giác ABC.", "AMBIGUOUS_FACT"),
        negative("M10", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 4, AD = 3, SA vuông góc với đáy và SA = -2.", "INVALID_VALUE"),
    ]
    return rows, negatives


def write_inputs():
    inputs = RUN / "inputs"
    font_file = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arial.ttf"
    font = ImageFont.truetype(str(font_file), 38)
    rows = []

    def raster(text, *, diagram=False, angle=0, blur=0, contrast=255):
        im = Image.new("RGB", (1500, 620 if diagram else 360), "white")
        draw = ImageDraw.Draw(im)
        draw.multiline_text((46, 36), "\n".join(textwrap.wrap(text, width=73)), font=font,
                            fill=(255-contrast,)*3, spacing=12)
        if diagram:
            points = [(330,330),(160,500),(530,500),(670,420),(300,420)]
            for i, j in [(0,1),(0,2),(0,3),(0,4),(1,2),(2,3),(3,4),(4,1)]:
                draw.line((points[i], points[j]), fill="black", width=3)
            for label, point in zip("SABCD", points):
                draw.text((point[0]+8, point[1]+4), label, font=font, fill="black")
            draw.line([(185,500),(185,475),(203,475)], fill="black", width=2)
        if angle:
            im = im.rotate(angle, fillcolor="white")
        return im.filter(ImageFilter.GaussianBlur(blur)) if blur else im

    def register(case, modality, filename, tags):
        case.update(input_type=modality, attachment={"path": f"inputs/{filename}",
                    "sha256": hashlib.sha256((inputs / filename).read_bytes()).hexdigest()}, modality_tags=tags)
        rows.append(case)

    def image_case(cid, text, tags, dims=None, **options):
        im = raster(text, **options)
        filename = cid.lower() + ".png"
        im.save(inputs / filename)
        case = pyramid(cid, text, *dims) if dims else negative(cid, text, tags[0])
        register(case, "raster_image", filename, tags)

    image_case("J01", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 7, AD = 3, SA vuông góc với đáy và SA = 2. Vẽ hình.", ["plain_text"], (7,3,2))
    image_case("J02", "Vẽ hình chóp S.ABCD có đáy là hình vuông ABCD cạnh 5, SA vuông góc với mặt phẳng (ABCD), SA = 4.", ["plain_text"], (5,5,4))
    image_case("J03", "Hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 6, AD = 2, SA ⊥ (ABCD), SA = 3. Dựng hình theo đề.", ["formula", "diagram_labels", "illustrative_diagram"], (6,2,3), diagram=True)
    image_case("J04", "Mô phỏng hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = 8, AD = 5 và SA vuông góc với đáy, SA = 6.", ["blurred"], (8,5,6), blur=1)
    image_case("J05", "Dựng hình chóp S.ABCD biết ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD) và SA = 7.", ["skewed"], (2,2,7), angle=3)
    image_case("J06", "Quan sát hình vẽ rồi tự đo các cạnh để dựng hình chóp S.ABCD.", ["diagram_only_missing_dimensions", "nearby_labels"], diagram=True)
    image_case("J07", "Bảng số liệu nhiệt độ trung bình các tháng trong năm của một thành phố.", ["out_of_scope"])
    image_case("J08", "Cho hình chóp S.ABCD có đáy là hình vuông cạnh 4, SA vuông góc với đáy, SA = 3 và SA = 5.", ["contradictory"])

    def pdf(cid, text, mode, dims):
        doc = fitz.open()
        page = doc.new_page()
        if mode in {"digital_pdf", "mixed_pdf"}:
            page.insert_font(fontname="axi", fontfile=str(font_file))
            page.insert_textbox(fitz.Rect(35,40,560,250), text, fontname="axi", fontsize=16)
        else:
            import io
            buf = io.BytesIO()
            raster(text).save(buf, format="PNG")
            page.insert_image(fitz.Rect(20,25,575,330), stream=buf.getvalue())
        if mode == "mixed_pdf":
            import io
            buf = io.BytesIO()
            raster("Minh họa.", diagram=True).save(buf, format="PNG")
            page.insert_image(fitz.Rect(20,260,575,560), stream=buf.getvalue())
        filename = cid.lower() + ".pdf"
        doc.save(inputs / filename, garbage=4, deflate=True, no_new_id=True)
        doc.close()
        register(pyramid(cid, text, *dims), mode, filename, [mode])

    pdf("Q01", "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 4, AD = 2. SA vuông góc với (ABCD) và SA = 5. Vẽ hình chóp.", "digital_pdf", (4,2,5))
    pdf("Q02", "Vẽ hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 6, SA vuông góc với đáy và SA = 2.", "scanned_pdf", (6,6,2))
    pdf("Q03", "Cho hình chóp S.ABCD có ABCD là hình chữ nhật, AB = 3, AD = 8, SA vuông góc với mặt đáy, SA = 4. Dựng hình.", "scanned_pdf", (3,8,4))
    pdf("Q04", "Dựng hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 5, AD = 6, SA vuông góc với đáy và SA = 2.", "mixed_pdf", (5,6,2))
    text = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3, SA vuông góc với đáy, SA = 9. Vẽ hình chóp S.ABCD."
    docx = Document()
    docx.add_paragraph(text)
    docx.save(inputs / "x01.docx")
    register(pyramid("X01", text, 3, 3, 9), "docx", "x01.docx", ["digital_text"])
    return rows


def dump(name, obj):
    path = RUN / name
    with path.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(obj, out, ensure_ascii=False, indent=2)
        out.write("\n")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    math_audit = audit_area()
    if "--selfcheck" in sys.argv:
        print(json.dumps(math_audit, ensure_ascii=False))
        return
    if (RUN / "ACCEPTANCE_MANIFEST.json").exists():
        raise SystemExit("Acceptance manifest already exists")
    valid, negative_rows = text_cases()
    visual = write_inputs()
    slug = RUN.name
    training = Path(sys.argv[1])
    corpus = collect(training if training.is_dir() else None)
    matches = exposed([r["original_input"] for r in valid + negative_rows + visual], corpus)
    assert not matches, matches
    manifest = {"schema": "axo-prospective-acceptance-manifest/1", "run_id": slug,
                "dataset_provenance": "agent-authored by the takeover agent after the CACHE 153 Holdout-1 diagnosis and before any takeover product edit; external independence NOT_MEASURED",
                "valid_cases": valid, "negative_cases": negative_rows, "attachment_cases": visual,
                "historical_math_audit": math_audit, "ui_runtime_scenarios": [],
                "counts": {"text_positive": len(valid), "text_negative": len(negative_rows),
                           "attachment": len(visual)}}
    digest = dump("ACCEPTANCE_MANIFEST.json", manifest)
    dump("ACCEPTANCE_CRITERIA.json", {
        "schema": "axo-acceptance-criteria/1", "run_id": slug,
        "manifest": {"path": "ACCEPTANCE_MANIFEST.json", "sha256": digest},
        "harness": {"version": "axo-live-acceptance-harness/1",
                    "scene_oracle_sha256": hashlib.sha256((HARNESS/"scene_oracle.py").read_bytes().replace(b"\r\n",b"\n")).hexdigest(),
                    "gold_generator_sha256": hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n",b"\n")).hexdigest()},
        "exposure": {"external_independence": "NOT_MEASURED", "normalized_prior_strings": len(corpus),
                     "training_corpus_included": training.is_dir(), "normalized_containment_matches": len(matches),
                     "single_shot": True},
        "runtime": {"route_mode": "local-only-scoped", "allow_live_ai": False, "model": "AxoV9",
                    "gguf_sha256": "73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35",
                    "llama_cpp_release": "b12470", "require_fresh_cache": True, "cloud_fallback": False},
        "primary": {"completion_rate_min": 0.85, "population": "all positive text and attachment cases",
                    "completion": "served with correct source facts, exact scene and answers, visual and interaction pass"},
        "slm": {"completion_rate_min": 0.30, "min_live_verified_scenes": 5,
                "population": "baseline SLM_REQUIRED text cases; final-candidate strata reported separately",
                "cache_and_replay_credit": False},
        "modalities": {"explicit_per_modality_live_metrics": True, "positive_completion_rate_min": 0.85,
                       "required": sorted({c["input_type"] for c in visual} | {"text"})},
        "safety": {"all_negative_safe": True, "external_ai_calls": 0, "wrong_served": 0,
                   "grounding_violations_served": 0, "unverified_relations_served": 0,
                   "fabricated_numeric_goals": 0, "served_numeric_mismatch": 0},
        "candidate_consistency": "same committed product, cache, model and runtime for live acceptance and Full T3",
    })
    print(digest, manifest["counts"], len(corpus))


if __name__ == "__main__":
    main()
