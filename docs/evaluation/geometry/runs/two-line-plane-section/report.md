# Mặt phẳng theo hai đường thẳng và thiết diện — LOCAL research

**GO trong phạm vi Group A nghiên cứu đã đăng ký.** Product `2b42eb40`, candidate freeze sạch; T3 tại clean69ff3a16 PASS backend9274 /frontend1053. Group B chưa triển khai; Hybrid product enablement NO-GO.
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

T3 authoritative: backend9274 PASS, skipped1/deselected2/xfail6; frontend1053/68files, build/demo5/5/crash6/6 PASS.
Heldout32 chỉ mở sau freeze:11correct served/21correct refusals, wrong0/false refusal0. Hai lần T3 trước FAIL
được giữ dưới dạng receipt tổng hợp, không ghi công PASS; taxonomy rồi lỗi Windows asyncio socketpair LOCAL được xử lý
trong bộ đo. Retry chỉWinError10013, tối đa3/freshoutputs, không retry lỗi hình học; independent harness follow-up NONBLOCKING.
SwiftShader và Intel UHD Graphics D3D11 (Chromium151.0.7922.34) PASS cả3served+1refused, no product console errors;
11/4 local network retries được báo rõ. Initial scrubber receipt FAIL do ownerid progressive suffix, giữ nguyên byte;
final checks nhận đúng semantic owner và dùng slider/selection thật. Oracle quyết định toán học, ảnh chỉ thể hiện.
Giới hạn: canvas chưa vẽ tên mặt(P), một số nhãn đỉnh như S bị che trong view mặc định; picker/details dùng đúng(P) và
Điểm dựng phụ. Điểm phụ có thể trùng tọa độ đỉnh section, semantic identity riêng. Không gọi đây là product/API E2E.
Cleanup cuối: `cleanup.json`; `run.json` là trạng thái máy; final docs/identity receipts trong `verification/`.
Scene3D chỉ harness Workspace qua Hybrid IR, không API/trang sản phẩm. Không gọi Gemini; Hybrid product enablement NO-GO.
Giữ DSL archived/bundles, real-model branches/pilot471a2c79, preserved/, frontend/public và old scratch/database.
Next action duy nhất sau gates: người dùng quyết định nghiệm thu/tích hợp nhánh nghiên cứu ở lượt riêng.

Cleanup thực tế: registered1→peak2→1, physical[]→[two-line-verify]→[]; verifier, junction và hai task scratch/temp đều đã mất trên ổ đĩa. Nội dung đã xóa 1857181926bytes (gồm review temp 871871bytes trên C); tồn đọng cũ0bytes. D free-volume observed delta 1916272640bytes; không gán toàn bộ chênh lệch này là nhân quả của task. Không còn deletion blocker; old permission-warning caches, old scratch/DB và dữ liệu được bảo vệ giữ nguyên.
Third full attempt interrupted at94percent, no footer/no credit; final fresh runnerPID22624 exited0, T3 all gatesPASS. Final LOCAL harness follow-up31PASS plus taxonomy completenessPASS, ordinary failures stop1, exact WinError10013 exhaustion stops3 and missing last-attempt fixtures fail; no partial credit.
Final docs/identity94PASS, docs auditPASS/secret0; candidateverify vẫn khớp. Temp của doc tests 45.0bytes đã dọn; tổng nội dung task đã xóa 1857181971.0bytes.
