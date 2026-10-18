import re, sys, pytest
import app.simulation.semantic_program.scale_normalization as SN
# Fault: restore the patterns of b59d14bc (before review round 2: N1 sentence-wide "tích vô hướng", N2 ":" as ratio,
# N3 ")" before "-", no coefficient before an operand).
_T = r"(?:(?<![A-Za-z0-9'′])[A-Z]\d*['′]?[A-Z]\d*['′]?(?:→|⃗)?|[)\]}])"
_P = r"(?:[+\-−–*×·⋅∙∧/:]|\\cdot|(?<=[ \t])x(?=[ \t]))"
SN._TRUOC_BIEU_THUC = re.compile(rf"(?:{_T}[ \t]*{_P}[ \t]*|{_T}\.|{_T}[ \t]+\.[ \t]*)$")
SN._TRUOC_VECTO = re.compile(rf"(?:{SN._VECTO}|tích\s+(?:vô|có)\s+hướng[^.;\n]*)\s*$", re.I)
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests/geometry/test_source_length_vector_context.py"]))
