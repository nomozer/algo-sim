import sys; sys.path.insert(0,'.')
from app.ai.adapter4_route import run_typed_fact_next_v2_route
def case(hq, base="tứ giác đều S.ABCD", verts="ABCD", shape="hình vuông cạnh 6"):
    V=list(verts); n="S."+verts
    t=(f"Cho hình chóp {base} có đáy {verts} là {shape}, {hq}. Lấy điểm M trên cạnh SA sao cho SM = 1/3 SA. "
       f"Gọi (P) là mặt phẳng đi qua điểm M và song song với mặt phẳng (ABC). Tính diện tích thiết diện của hình chóp {n} cắt bởi mặt phẳng (P).")
    return {"schema_version":"typed-fact-next/2","problem_text":t,"length_unit":"1",
     "solids":[{"solid_id":"s1","solid_type":"pyramid","notation":n,"quote":f"Cho hình chóp {base}"}],
     "premises":[{"kind":"regular_pyramid","args":{"apex":"S","base":V},"quote":f"Cho hình chóp {base}","solid_id":"s1"},
       {"kind":"regular_polygon","args":{"vertices":V,"side":"6"},"quote":f"có đáy {verts} là {shape}","solid_id":"s1"},
       {"kind":"height","args":{"value":"4","solid":"s1"},"quote":hq,"solid_id":"s1"},
       {"kind":"divide_segment","args":{"point":"M","segment":["S","A"],"ratio":"1/3"},"quote":"Lấy điểm M trên cạnh SA sao cho SM = 1/3 SA","solid_id":"s1"}],
     "derived_sections":[{"section_id":"sec","plane_name":"P","target_solid_id":"s1","plane_kind":"through_point_parallel_plane","through_point":"M","parallel_plane":["A","B","C"],"stated_intersections":[],"quote":"Gọi (P) là mặt phẳng đi qua điểm M và song song với mặt phẳng (ABC)"}],
     "relations":[],"simulation_goals":[{"goal_id":"sg1","kind":"construct_object","target_solid_id":"s1","quote":f"Cho hình chóp {base}"}],
     "math_goals":[{"goal_id":"mg1","kind":"measurement","goal_type":"area","solid_id":"s1","target":{"section_id":"sec"},"quote":f"Tính diện tích thiết diện của hình chóp {n} cắt bởi mặt phẳng (P)"}]}
cases=[(hq,{}) for hq in ["chiều cao của hình chóp bằng 4","chiều cao bằng 4","chiều cao hình chóp bằng 4","chiều cao của khối chóp bằng 4"]]
cases+=[("chiều cao bằng 4",dict(base="tam giác đều S.ABC",verts="ABC",shape="tam giác đều cạnh 6"))]
for hq,kw in cases:
    r=run_typed_fact_next_v2_route(case(hq,**kw)); print(repr(hq), kw.get("verts","ABCD"), r.status, r.code, (r.reason or "")[:90], getattr(r,"answer_exact",None))
