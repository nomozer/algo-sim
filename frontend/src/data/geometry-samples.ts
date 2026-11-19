/**
 * BÀI MẪU HÌNH HỌC — envelope dựng sẵn, chạy ngay, **0 gọi AI**.
 *
 * ─── VÌ SAO TÁCH KHỎI `sim-samples.ts` ──────────────────────────────────
 *
 * `OFFLINE_SAMPLES` là mẫu VIẾT TAY: ai đó gõ `config: { inputA: 0 }` rồi
 * envelope xong. Với hình học thì không được — `config.frames` là chuỗi khung
 * do interpreter sinh, và `scene3d` là toạ độ do KERNEL tính. Viết tay chúng
 * là đặt toạ độ kết quả vào tay người, đúng thứ ranh giới R0 cấm.
 *
 * Nên các file JSON cạnh đây là **SINH RA**:
 *
 *     cd backend && .venv/Scripts/python.exe scripts/build_advanced_geometry_samples.py
 *     cd backend && .venv/Scripts/python.exe scripts/build_geometry_samples.py
 *
 * Sửa đề bài hay các bước dựng thì sửa **script**, không sửa JSON — chạy lại
 * sẽ ghi đè. `geometry-samples.test.ts` khoá cho JSON không trôi khỏi script.
 *
 * ─── NHỮNG BÀI NÀY DẠY GÌ ───────────────────────────────────────────────
 *
 * Phủ đầy đủ các dạng hoạt động TRONG PHẠM VI đề tài hình học không gian THPT:
 * dựng hình/thiết diện · quan hệ song song–vuông góc · khoảng cách/thể tích/góc
 * · giao điểm đường–mặt trong Oxyz · mặt cầu cắt/tiếp xúc/ngoại tiếp · khối tròn xoay.
 */
import { attachProblemContextToScene } from "../simulations/domains/geometry/scene3d-semantic-policy";
import type { SimulationEnvelope } from "../simulations/types";
import advancedRaw from "./advanced-geometry-samples.json";
import legacyRaw from "./geometry-samples.json";

export interface GeometrySample {
  id: string;
  /** Nhóm hoạt động — để danh mục xếp theo VIỆC HỌC, không theo tên hàm. */
  group: string;
  /** Đề bài nguyên văn, đúng giọng SGK. */
  problemText: string;
  envelope: SimulationEnvelope;
}

interface RawFile {
  khai: string;
  samples: GeometrySample[];
}

/** 11 bài toán hình học THPT nâng cao hiển thị công khai trong Thư viện. */
export const PUBLIC_GEOMETRY_SAMPLES: GeometrySample[] =
  (advancedRaw as unknown as RawFile).samples;

/** 11 fixture hình học cũ được bảo toàn cho kiểm thử hồi quy và tương thích lịch sử/URL cũ. */
export const LEGACY_GEOMETRY_SAMPLES: GeometrySample[] =
  (legacyRaw as unknown as RawFile).samples;

export const GEOMETRY_SAMPLES: GeometrySample[] = [
  ...PUBLIC_GEOMETRY_SAMPLES,
  ...LEGACY_GEOMETRY_SAMPLES,
];

for (const sample of GEOMETRY_SAMPLES) {
  const sc = (sample.envelope as unknown as { scene3d?: unknown })?.scene3d;
  if (sc && typeof sc === "object") {
    attachProblemContextToScene(sc as never, {
      title: sample.envelope.title,
      statement: sample.problemText || sample.envelope.description,
    });
  }
}

/** Bài mẫu theo id, hoặc `undefined`. Không ném — id lạ đến từ URL cũ. */
export function geometrySampleById(id: string): GeometrySample | undefined {
  return GEOMETRY_SAMPLES.find((s) => s.id === id);
}
