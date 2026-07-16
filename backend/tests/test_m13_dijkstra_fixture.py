"""M13 §6.1: artifact pseudo-Dijkstra KHÔNG BAO GIỜ qua được validator nữa.

Regression lock — không phải TDD RED→GREEN. Fixture phản ánh sự cố gốc: một
đề "mô phỏng thuật toán Dijkstra" bị định tuyến vào generic.rule_scene và
render thành cảnh weighted_sum lấy input là id CẠNH (edge_AB/edge_BC/edge_AC)
— cạnh không mang giá trị số nên runtime lặng lẽ tính ra 0, nhưng cảnh vẫn
chạy đủ và báo "Hoàn tất!". Validator (Task 3, M13 §3.2) phải chặn cấu hình
này ngay ở bước validate, trước khi engine chạy.
"""
import json
from pathlib import Path

from app.simulation.dsl.validator import validate_generic_config

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "m13_dijkstra_pseudo_algorithm.json").read_text(
        encoding="utf-8"
    )
)


def test_artifact_dijkstra_cu_bi_validator_tu_choi():
    config, err = validate_generic_config(FIXTURE["config"])
    assert config is None
    assert "không có nguồn giá trị" in err
