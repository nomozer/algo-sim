"""Build the 16 locked V2 malformed targets with the locked test's own _prism builder (cwd=<head>/backend, PYTHONPATH=.;tests/geometry)."""
import json, sys
import test_typed_fact_next_v2_distance_bridge as L
targets = [m.args[1] for m in L.test_malformed_distance_target_is_refused.pytestmark if m.name == 'parametrize'][0]
cases = {f'L{i:02d}': {'payload': L._prism(ask=("Tính khoảng cách từ A' đến mặt phẳng (ABC).", t)), 'target': t} for i, t in enumerate(targets)}
json.dump(cases, open(sys.argv[1], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(cases))
