# Mặt phẳng theo hai đường thẳng và thiết diện — LOCAL research

Trạng thái hiện tại: product `2b42eb40` đã đóng băng sạch; final gates đang chạy, chưa tuyên bố nghiệm thu.
Nhánh `research/goal-directed-two-line-plane-section`; main/origin `5270f3dd` giữ nguyên; push NONE.

Planner trước chỉ dựng mặt qua điểm song song một mặt có tên. Nay cùng `_mat_qua_diem` nhận mục tiêu
`parallel_two_lines`, phân rã VerifiedPoint/VerifiedLine →2 `translate_point` → `vector_from_points`/`translate` →
`construct_plane` → `construct_section` → area. Giới hạn64calls/4derived planes, fresh identity và dedup/DAG được giữ.
Không hardcode họ hình/nhãn/số liệu; không có compiler, engine, semantic authority hoặc FactGraph thứ hai.
Geometry Compiler cũ giữ nguyên; predicates/IR/Kernel hiện hành được tái sử dụng, không sao chép thuật toán của nó.

TypedFact thêm enum `parallel_two_lines` và trường optional `plane_name` (bắt buộc biến thể này); dùng lại point/points_a/
points_b/source quotes/role. B prompt/schema đổi có chủ đích, hash `145feb18…`; A `912b22ef…` và declarations `f2ec9698…`
giữ nguyên; chi tiết/serialization trong `provider-surfaces.json`. Fake extraction đi qua adapter thật, Gemini NOT_MEASURED.
Cache125 và LLM_ONLY giữ; explicit plane display defaults false và chỉ bật trên rule nghiên cứu mới.

Group A đúng trong văn phạm đóng đã công bố: khối lồi đơn có Engine section certificate, hai phương khác0/độc lập,
M đã xác minh. Dùng strict parallel: chứa đường không được gọi là song song không giao nhau. Ví dụ prompt M giữaSC,
AB/SD trên chóp đáy vuông có SA vuông đáy phải REFUSE vì mặt chứaSD. Positive control thay M giữaSB dựng tứ giác diện
tích `3√13/4`; tên(P) được giữ qua section. Có controls chóp tam giác/tứ giác, lăng trụ tam giác đứng, hộp chữ nhật.
Từ chối thiếu nguồn/sai role/condition/negation/finite segment, unknown point, zero/dependent directions,
line contained, mặt biên/tangent/no valid polygon hoặc unsupported grammar; không tự tạo giả thiết.

Group B `DEFERRED_WITH_REASON`: chưa có biến thể trích xuất/grounding/chứng chỉ chứa đường và corpus đăng ký riêng trong
freeze A; không tái dùng strict-A để phục vụ containment, không mở rộng sau heldout. Reuse hình học tiềm năng có;
điều này không phải tuyên bố cần kiến trúc mới. Báo cáo kết thúc Group A và giữ B chưa triển khai.

45ca development đăng ký trước sản phẩm:12 đúng phục vụ/33 đúng từ chối,0 wrong served/0 false refusal; corpus gồm
positive và mathematical boundary. Semantic negative/adversarial/multi-goal/metamorphic nằm ở111 focused tests riêng,
không gán nhãn ngụy tạo cho tập toán. Heldout32 sealed trước sửa, chỉ mở sau freeze. Oracle nghiên cứu exact facet-pair
halfspaces + convex hull, khác product edge clipping; kiểm tập đỉnh/chung mặt, cạnh biên và area theo det(G)·aᵀG⁻¹a.
Tác giả oracle/corpus cùng implementer; độc lập thuật toán, không độc lập người đánh giá. Endpoint/order/rename,
collision, translation, uniform scale, normal flip và shared plane controls PASS. Review LOCAL độc lập NONBLOCKING;
phát hiện quote closure đã sửa RED→GREEN, receipt `review.md`. Residual old routes vẫn OPEN; new-route probes fail-closed.

Benchmark30 lịch sử giữ19/9/0/2 cả facts/pipeline, byte-identical; file `benchmark/metrics.json`.
Candidate `c2ac6dbe1cc65170e75db6a0d6d7e4e8e0a1c544db5961fcd16120a89606c5d4`,110files;
measured paths backend/app +frontend semantic domain/schema. Freeze tại clean detached2b42eb40;
additive `inputs/candidate_divergence.json` extends source-grounding-integration; historical evidence giữ nguyên.

T3/heldout/Playwright/docs receipts và cleanup cuối cập nhật sau khi kết thúc, `run.json` là trạng thái máy.
Scene3D chỉ harness Workspace qua Hybrid IR, không API/trang sản phẩm. Không gọi Gemini; Hybrid product enablement NO-GO.
Giữ DSL archived/bundles, real-model branches/pilot471a2c79, preserved/, frontend/public và old scratch/database.
Next action duy nhất sau gates: người dùng quyết định nghiệm thu/tích hợp nhánh nghiên cứu ở lượt riêng.
