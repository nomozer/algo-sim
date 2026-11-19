# Controlled Integration Design (`AXO CONSTRUCTION /2`)

## 1. Kiến trúc nối tầng không vòng qua Source Gate

Toàn bộ luồng tích hợp thử nghiệm giữ nguyên 100% ranh giới bất biến của Axo (`Hybrid /4`):

```text
Raw Vietnamese Problem + TypedFactNext /2 (hoặc typed-facts/2)
   │
   ├─► bridge_v2 / planner.lap_ke_hoach / registry.kiem_nguon (Source Gate — ZERO BYPASS)
   │      └─ Từ chối ngay mọi thiếu dữ kiện / trích dẫn giả / phủ định / mâu thuẫn ngữ nghĩa
   │
   ├─► InitialGeometryFrame (chỉ nhận hệ tọa độ + SPD Chart Metric từ engine.dung_tu_loi_goi)
   │      └─ Trích PendingConstruction (midpoint, centroid, divide_segment, point_reflection, intersect, parallel_section) + GoalSpec
   │
   └─► resolve_dynamic_construction_mode(AXO_DYNAMIC_CONSTRUCTION_MODE)
          ├── "off" (mặc định): 100% Legacy Product Pipeline (`function_route.run_fact_route` -> `adapter4_route.build_adapter4_response`)
          ├── "shadow": trả kết quả Legacy đã xác minh; chạy song song DynamicConstructionPlanner /2 + L0–L4 offline -> phát `ShadowComparisonReceipt` (`user_impact="NONE"`)
          └── "experimental": phục vụ `DYNAMIC_CONSTRUCTION_PLANNER_V2` CHỈ KHI Source Gate=VERIFIED ∧ L0–L4 PASS ∧ Presentation 6-invariant PASS ∧ Multi-plan bundle hợp lệ; nếu timeout/lỗi ⇒ `SAFE_VERIFIED_LEGACY_FALLBACK` (khi legacy đã verified) hoặc `FAIL_CLOSED_REFUSED`.
```

## 2. Hợp đồng các thành phần mới (đã triển khai trong `backend/experimental/construction_planner/`)

1. **`verified_input_bridge.py` (`VERIFIED_INPUT_BRIDGE_VERSION`):**
   - Hàm `bridge_verified_facts_to_construction_input(...)` gọi `bridge_v2` (nếu `typed-fact-next/2`), sau đó `planner.lap_ke_hoach` và `registry.kiem_nguon(..., auxiliary=tuple(kh.auxiliary))`.
   - Khi `registry.kiem_nguon` ném `TuChoi`, trả `VerifiedBridgeOutcome(accepted=False, source_gate_status="REFUSED", source_gate_code=exc.code, ...)` ngay lập tức, tuyệt đối không dựng frame.
2. **`integration_adapter.py` (`INTEGRATION_ADAPTER_VERSION`):**
   - Cổng điều phối `AXO_DYNAMIC_CONSTRUCTION_MODE` với 3 giá trị hợp lệ `{"off", "shadow", "experimental"}` (mọi giá trị khác fail-safe về `"off"`).
   - Đặt `ALLOW_LIVE_AI="0"` và `GEMINI_API_KEY=""` mặc định ở tầng adapter; bảo đảm 0 lời gọi AI ra ngoài.
   - Cơ chế fallback (`SAFE_VERIFIED_LEGACY_FALLBACK`) chỉ kích hoạt khi `legacy_served_verified and bridge_res.source_gate_status == "VERIFIED"`; mọi trường hợp cả hai cùng không chứng minh được đều `FAIL_CLOSED_REFUSED` (`status="REFUSED"`, `answer=None`, `scene3d=None`).
3. **Handoff Patches (ngoài vùng `BLOCKED_OWNERSHIP`):**
   - [backend_adapter4_dynamic_construction_flag.patch](handoff/backend_adapter4_dynamic_construction_flag.patch) móc vào `run_typed_fact_next_v2_route` của `backend/app/ai/adapter4_route.py` sau khi `chay_sau_cau_noi` chạy xong.
   - [frontend_scene3d_multiplan_switcher.patch](handoff/frontend_scene3d_multiplan_switcher.patch) thêm `alternativePlans` và `activePlanRank` tự cô lập trong `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx`.
