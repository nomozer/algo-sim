# scratch plugin: measure Adapter /3 fallout of a source-gate policy without editing product code
import os, pytest
from app.ai import adapter3_simulation as A
from app.simulation.geometry_functions.registry import TuChoi
_real = A._shared_source_gate
MODE = os.environ["GATE_MODE"]
def gated(payload):
    v = _real(payload)
    if v["authority"] != A.SOURCE_GATE_AUTHORITY:
        if MODE == "strict" or (MODE == "answers" and payload.math_goals):
            raise TuChoi("SOURCE_GATE_UNAVAILABLE", v["gate_unavailable"])
    return v
A._shared_source_gate = gated
