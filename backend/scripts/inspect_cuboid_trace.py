import sys
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from app.simulation.semantic_program.source_entities import ky_hieu_toan, dinh_danh_thuc_the
print('ky_hieu_toan A_prime:', repr(ky_hieu_toan('A_prime')))
print('dinh_danh_thuc_the A_prime:', repr(dinh_danh_thuc_the('A_prime')))
print('dinh_danh_thuc_the A\':', repr(dinh_danh_thuc_the("A'")))
print('dinh_danh_thuc_the A′:', repr(dinh_danh_thuc_the('A\u2032')))
from app.simulation.semantic_program.analyze_contract import build_request_contract
from tests.geometry.test_cuboid_cube_production_route import _cuboid_p01_payload
from app.simulation.geometry_compiler import contract_adapter as A, compiler as C
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.simulation_state import build_simulation_state
from app.simulation.semantic_program.scene3d import build_scene3d
from app.simulation.semantic_program.validator import validate_semantic_program

text, payload = _cuboid_p01_payload()
contract = build_request_contract(payload, problem_text=text, domain='hinh_hoc')
ka = A.build_fact_graph(contract)
res = C.bien_dich(ka.graph)
val = validate_semantic_program(res.program)
interp = SemanticProgramInterpreter()
sim_res = interp.execute(val.spec)
state = build_simulation_state(val.spec, sim_res, contract)
scene = build_scene3d(state)

print('Trace steps:', len(sim_res.trace))
for s in sim_res.trace:
    print(f"Step {s.step_index}: action={s.action}, target={s.target}, narration={s.tier1_narration}")
from app.ai.pipeline import _dung_scene3d, _envelope_tu_route_sinh
from app.simulation.semantic_program.route import verify_and_compile
outcome = verify_and_compile(contract, val.spec)
outcome = outcome.model_copy(update={"scene3d": _dung_scene3d(val.spec, contract)})
env = _envelope_tu_route_sinh(outcome, {}, {}, None)
cfg = env["config"]
print("Frames count:", len(cfg["frames"]))
for f in cfg["frames"]:
    print(f"Frame {f['step_index']}: narration={f['narration']}")
from tests.geometry.test_cuboid_cube_production_route import _cube_p01_payload, _square_prism_control_payload
for name, pfn in [("CUBE_P01", _cube_p01_payload), ("SQUARE_PRISM_CONTROL", _square_prism_control_payload)]:
    text, payload = pfn()
    contract = build_request_contract(payload, problem_text=text, domain='hinh_hoc')
    ka = A.build_fact_graph(contract)
    res = C.bien_dich(ka.graph)
    val = validate_semantic_program(res.program)
    outcome = verify_and_compile(contract, val.spec)
    outcome = outcome.model_copy(update={"scene3d": _dung_scene3d(val.spec, contract)})
    env = _envelope_tu_route_sinh(outcome, {}, {}, None)
    cfg = env["config"]
    scene = env["scene3d"]
    print(f"\n--- {name} ---")
    for f in cfg["frames"]:
        print(f"Frame {f['step_index']}: {f['narration']}")
