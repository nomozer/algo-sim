"""Khai báo nới cổng nguồn (AB_OFFLINE_RESULTS §6): khôi phục TRONG BỘ NHỚ từ khoá cổng nguồn trước `65fd0328` rồi chạy nhánh A
trên các ca holdout lập phương / hộp chữ nhật. Chỉ khôi phục `keywords` (kiểm 'lăng trụ đứng' trong engine giữ bản mới ⇒ đây là
cận dưới của số ca bị chặn). 0 API call. Chạy từ backend/."""
import dataclasses
import json
import sys

sys.path.insert(0, ".")
from app.ai.function_route import run_function_route
from app.simulation.geometry_functions import registry as R

CU = {"regular_polygon": (("đều", "hình vuông"),), "rectangle": (("hình chữ nhật",),), "prism": (("lăng trụ", "hình hộp"),)}
for ten, kw in CU.items():
    R.REGISTRY[ten] = dataclasses.replace(R.REGISTRY[ten], keywords=kw)
cases = {c["id"]: c for c in json.load(open("tests/geometry/fixtures/hybrid_holdout_cases.json", encoding="utf-8"))["cases"]}
for cid in ("H01_CUBE", "H02_CUBOID_DISTANCE", "H09_CUBE_CONTRADICTION", "H10_CUBOID_MISSING_HEIGHT",
            "H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS"):
    r = run_function_route(cases[cid]["text"], {"calls": cases[cid]["a_calls"]})
    print(cid, r.status, r.code, r.reason or "")
