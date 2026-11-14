"""Reproduction on the PREVIOUS product code (run from an archive of 914dd41db/backend): what the /1 verifier accepts.
  PYTHONPATH=<archive>/backend python old_verifier_probe.py <out.json>
Development text only (agent-written, the r520 configuration renamed nowhere)."""
import copy, json, os, sys
os.environ["ALLOW_LIVE_AI"] = "0"
from app.ai.local_geometry_parser import parse_geometry_problem_locally as P
from app.simulation.geometry_functions import planner
from app.simulation.geometry_functions.registry import doc_ke_hoach
from app.simulation.geometry_functions.target_invariance import prove_plane_angle, verify_target_invariance_certificate as V
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

T = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. Tính góc giữa hai mặt phẳng (SBC) và (ABC)."
lp = P(T, use_cache=False)
calls = doc_ke_hoach({"calls": planner.lap_ke_hoach({"facts": bridge_v2(lp.parsed_contract)["facts"]}, T).calls})
ask = next(c for c in calls if c.fn == "ask_angle_plane_plane")
cert = prove_plane_angle(calls, ask.id, ask.args.plane1, ask.args.plane2)
pa = next(s for s in cert["steps"] if s["rule"] == "PLANE_ANGLE")
out = {"generated_plane_angle_step": pa, "claim": cert["claim"], "original_verified": V(cert, calls)["verified"], "probes": {}}

def probe(name, mut, note):
    c = copy.deepcopy(cert); mut(c)
    out["probes"][name] = {"accepted_by_old_verifier": V(c, calls)["verified"], "note": note}

step = lambda c, r: next(s for s in c["steps"] if s["rule"] == r)
probe("triple_in_standard_notation_vertex_in_the_middle", lambda c: step(c, "PLANE_ANGLE")["conclusion"].__setitem__("equals_angle", ["S", "B", "A"]),
      "the correct angle SBA written in standard notation (vertex in the middle)")
probe("triple_as_generated_vertex_first", lambda c: None, "the generated triple ['B','S','A'] — reads as angle BSA (vertex S) in standard notation")
def forge_plane(c):
    s = step(c, "PERP_TWO_LINES"); s["conclusion"]["line_perp_plane"][1] = ["A", "B", "C", "S"]
probe("forged_four_label_non_coplanar_plane", forge_plane, "PERP_TWO_LINES concluding BC ⊥ 'plane' {A,B,C,S} (four non-coplanar labels)")
def other_goal(c):
    c["goal_id"] = "q_other"
probe("certificate_attached_to_another_goal", other_goal, "goal_id changed: the verifier never sees the asked planes")
def shape_vertex(c):
    step(c, "TRIANGLE_SHAPE_FIXED")["conclusion"]["triangle"] = ["S", "B", "A"]
probe("triangle_listed_with_another_first_label", shape_vertex, "the fixed triangle named with S first: the angle's vertex is not tied to the triangle step")
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: v["accepted_by_old_verifier"] for k, v in out["probes"].items()}, indent=0))
