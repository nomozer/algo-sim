import sys, pytest
import app.simulation.semantic_program.segment_relation as SR
import app.simulation.semantic_program.scale_normalization as SN
# Fault: every "label = value" is a length again (the reader before c55374cc).
SN.loai_nhan_doan = lambda *a: SN.DO_DAI
SR.loai_nhan_doan = lambda *a: SN.DO_DAI
SR.nhan_doan_dung_mot_minh = lambda *a: True
SN.nhan_doan_dung_mot_minh = lambda *a: True
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", "tests/geometry/test_source_length_vector_context.py"]))
