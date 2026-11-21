# CPU và bộ nhớ toàn stack (P7 · Gate H7)

Host: Windows 11 Pro, 15.78 GiB RAM, CPU (llama.cpp 6 luồng). **Không phải phần cứng đích 4–8 GiB** (`PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`).

## 1. Ảnh chụp toàn stack trong một phiên trình duyệt (`evidence/memory/`)

8 đề qua UI thật (5 cảnh phục vụ, 3 lượt SLM bị từ chối), `tools/stack_memory_sampler.ps1` (WS / private / CPU giây theo nhóm tiến trình,
~3 s/mẫu do `Get-CimInstance`).

| Nhóm tiến trình | Số tiến trình | WS tối đa | WS trung bình | Private tối đa | CPU dùng trong phiên |
|---|---|---|---|---|---|
| Backend (uvicorn + launcher venv) | 2 | 116 MB | 114 MB | 97 MB | 3.3 s |
| llama-server (AxoV9 Q4_K_M) | 1 | 903 MB | 902 MB | 578 MB | 88.9 s |
| Chromium headless (Playwright, WebGL SwiftShader) | 4 | 500 MB | 403 MB | 371 MB | 69.6 s |
| **Tổng WS cùng thời điểm (tối đa)** | | **1519 MB** | | | |

## 2. Suốt lượt nghiệm thu 2 (`evidence/cpu_mem_pass2.csv`, 685 mẫu / 2 s)

| Chỉ số | Trung bình | p95 | Tối đa |
|---|---|---|---|
| CPU toàn máy (%) | 37.2 | 87.8 | 99.9 |
| RAM trống của máy (MB) | 3212 | 4100 | min 1408 |
| llama-server WS khi đã nạp (MB) | 837 | 903 | 919 |

RAM trống thấp vì máy dev đồng thời chạy IDE, nhiều tiến trình node và Docker — đây là điều kiện đo, không phải tải của Axo.

## Diễn giải

- So với /9 (backend + llama-server ≈ 973 MB WS): khớp bậc độ lớn (116 + 903 ≈ 1019 MB ở đây).
- Thêm trình duyệt: ≈ 1.5 GB WS cho cả backend, model và một tab Axo trên cùng một máy. Trên máy 4 GiB có hệ điều hành và trình
  duyệt thật (có GPU, không phải SwiftShader headless) con số sẽ khác — **chưa đo**.
- Chromium headless dùng WebGL phần mềm: CPU trình duyệt (69.6 s / phiên) không đại diện cho trình duyệt có GPU.

## Chưa đo

Bộ nhớ WebGL (không có công cụ phù hợp trong headless), page faults / paging, phiên dài nhiều giờ, máy 4/6/8 GiB thật, trình duyệt
có GPU.

**Gate H7: PARTIAL** — có số đo backend, model, trình duyệt và thời gian trình duyệt trên host dev; phần cứng đích `NOT_MEASURED`.
