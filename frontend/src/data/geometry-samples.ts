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
 * Nên file JSON cạnh đây là **SINH RA**:
 *
 *     cd backend && .venv/Scripts/python.exe scripts/build_geometry_samples.py
 *
 * Sửa đề bài hay các bước dựng thì sửa **script**, không sửa JSON — chạy lại
 * sẽ ghi đè. `geometry-samples.test.ts` khoá cho JSON không trôi khỏi script.
 *
 * ─── NHỮNG BÀI NÀY DẠY GÌ ───────────────────────────────────────────────
 *
 * Ba bài phủ đúng ba loại hoạt động TRONG PHẠM VI đề tài: dựng hình/thiết
 * diện · quan hệ song song–vuông góc · khoảng cách/thể tích/góc. Không có bài
 * "kéo để thấy bất biến" kiểu GeoGebra — thứ ấy liên tục và phá song ánh
 * `frame k ⇔ trace[k]`.
 */
import type { SimulationEnvelope } from "../simulations/types";
import raw from "./geometry-samples.json";

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

export const GEOMETRY_SAMPLES: GeometrySample[] =
  (raw as unknown as RawFile).samples;

/** Bài mẫu theo id, hoặc `undefined`. Không ném — id lạ đến từ URL cũ. */
export function geometrySampleById(id: string): GeometrySample | undefined {
  return GEOMETRY_SAMPLES.find((s) => s.id === id);
}
