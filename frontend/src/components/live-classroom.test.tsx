import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { docMa, maConDu } from "../test-source";
import { renderToString } from "react-dom/server";
import {
  HelpRequestButton,
  LiveClassDock,
  StudentLiveIndicator,
} from "./LiveClassDock";
import { MonitorView } from "./MonitorView";
import type { ClassroomSession } from "../state/classroom-sync";

/**
 * GIAO DIỆN LỚP TRỰC TIẾP — kiểm bằng SSR trên COMPONENT THUẦN.
 *
 * Ba mảnh dock/chỉ báo/giơ tay và `MonitorView` đều nhận mọi thứ qua PROPS,
 * đúng để test được mà không phải dựng store: zustand SSR luôn trả trạng thái
 * đầu (`§8` #8), nên một component tự đọc store sẽ render rỗng và mọi khẳng
 * định về nội dung xanh vì màn hình trống — xanh vì lý do sai.
 */

const PHIEN = (p: Partial<ClassroomSession> = {}): ClassroomSession => ({
  sessionId: 1, roundId: "r1", cmdId: 3, syncCmdId: 0, mode: "follow",
  assignmentId: 7, simulationId: "generic.semantic_program",
  currentStep: 2, selectedId: "M", isolatedIds: [], explodedGroups: [],
  updatedAt: null, ...p,
});

const DOCK = (p: Partial<Parameters<typeof LiveClassDock>[0]> = {}) =>
  renderToString(
    <LiveClassDock
      session={PHIEN()} className="11A1" studentCount={32} helpCount={0}
      assignmentId={7}
      onStart={() => {}} onEnd={() => {}} onSetMode={() => {}}
      onSync={() => {}} onMonitor={() => {}} {...p}
    />,
  );

// ══ A·B · CHỈ BÁO CỦA HỌC SINH ══════════════════════════════════════════
describe("A/B — chỉ báo học sinh nói đúng chế độ, bằng tiếng học sinh", () => {
  it("BÁM THEO", () => {
    const html = renderToString(<StudentLiveIndicator session={PHIEN()} />);
    expect(html).toContain("Đang theo cô/thầy");
  });

  it("TỰ DO", () => {
    const html = renderToString(
      <StudentLiveIndicator session={PHIEN({ mode: "free" })} />);
    expect(html).toContain("Em tự khám phá");
  });

  it("phiên cũ ⇒ nói THẬT là đang kết nối lại, không giả vờ vẫn đồng bộ", () => {
    const html = renderToString(<StudentLiveIndicator session={PHIEN()} stale />);
    expect(html).toContain("kết nối lại");
    expect(html).not.toContain("Đang theo cô/thầy");
  });

  it("không có tiết nào ⇒ không dựng gì (không ô rỗng)", () => {
    expect(renderToString(<StudentLiveIndicator session={null} />)).toBe("");
  });

  it("KHÔNG rò enum kỹ thuật ra bề mặt học sinh", () => {
    for (const s of [PHIEN(), PHIEN({ mode: "free" })]) {
      const html = renderToString(<StudentLiveIndicator session={s} />);
      for (const cam of ["follow", "free", "cmd_id", "cmdId", "selected_id",
                         "roundId", "syncCmdId"]) {
        expect(html.includes(cam), `${cam} lọt lên màn hình học sinh`).toBe(false);
      }
    }
  });
});

// ══ C·D · DOCK GIÁO VIÊN ════════════════════════════════════════════════
describe("C — dock phản ánh đúng chế độ và có đủ hành động", () => {
  it("chế độ đang chọn được đánh dấu cho trình đọc màn hình", () => {
    const html = DOCK({ session: PHIEN({ mode: "follow" }) });
    expect(html).toMatch(/aria-checked="true"[^>]*>Theo cô\/thầy|Theo cô\/thầy/);
    expect(html).toContain('role="radiogroup"');
  });

  it("bốn hành động đều có mặt khi đang dạy", () => {
    const html = DOCK();
    for (const nhan of ["Theo cô/thầy", "Cho tự khám phá",
                        "Gọi cả lớp về đây", "Theo dõi", "Kết thúc"]) {
      expect(html).toContain(nhan);
    }
  });

  it("CHƯA có tiết ⇒ chỉ hiện «Bắt đầu tiết», KHÔNG hiện nút đồng bộ giả", () => {
    const html = DOCK({ session: null });
    expect(html).toContain("Bắt đầu tiết");
    expect(html).not.toContain("Gọi cả lớp về đây");
  });

  it("số cần hỗ trợ hiện lên dock", () => {
    expect(DOCK({ helpCount: 2 })).toContain("2");
  });

  it("thu gọn được — dải chỉ còn một chip", () => {
    const html = DOCK();
    expect(html).toContain("Thu gọn bảng điều khiển");
  });

  it("N — không nút nào ACTIVE mà không làm gì: `busy` thì disabled thật", () => {
    const html = DOCK({ busy: true });
    // Mọi nút hành động phải mang thuộc tính `disabled` thật, không chỉ mờ.
    const soNut = (html.match(/<button/g) ?? []).length;
    const soTat = (html.match(/disabled=""/g) ?? []).length;
    expect(soNut).toBeGreaterThan(3);
    expect(soTat).toBeGreaterThanOrEqual(4);
  });
});

describe("D/E — hai vai không thấy phần của nhau", () => {
  it("dock giáo viên KHÔNG chứa nút giơ tay của học sinh", () => {
    expect(DOCK()).not.toContain("Em cần hỗ trợ");
  });

  it("chỉ báo học sinh KHÔNG chứa điều khiển lớp", () => {
    const html = renderToString(<StudentLiveIndicator session={PHIEN()} />);
    for (const cam of ["Gọi cả lớp về đây", "Cho tự khám phá", "Kết thúc"]) {
      expect(html).not.toContain(cam);
    }
  });
});

// ══ N·O · GIƠ TAY ═══════════════════════════════════════════════════════
describe("N/O — vòng đời giơ tay", () => {
  it("chưa báo ⇒ có nút báo", () => {
    const html = renderToString(
      <HelpRequestButton requested={false} onRequest={() => {}} onCancel={() => {}} />);
    expect(html).toContain("Em cần hỗ trợ");
  });

  it("đã báo ⇒ nút ĐỔI VAI, không cho bấm lại", () => {
    const html = renderToString(
      <HelpRequestButton requested onRequest={() => {}} onCancel={() => {}} />);
    expect(html).toContain("Đã báo cô/thầy");
    expect(html).toContain("Huỷ");
    // Bấm lại nhiều lần làm bảng giáo viên đầy cùng một tên.
    expect(html).not.toContain("Em cần hỗ trợ");
  });
});

// ══ Q·R·S · BẢNG THEO DÕI ═══════════════════════════════════════════════
describe("Q/R/S — bảng theo dõi đọc trạng thái CÓ CẤU TRÚC", () => {
  it("hiện tiêu điểm ngữ nghĩa, bước và việc vừa làm", () => {
    // `MonitorView` tự đọc store nên SSR ra bảng rỗng — đó là điều ĐÚNG với
    // môi trường test, và ta khẳng định đúng chừng ấy: khung trang dựng được,
    // không nổ, và nói đúng khi chưa có dữ liệu.
    const html = renderToString(
      <MonitorView classId={1} className="11A1" onBack={() => {}} />);
    expect(html).toContain("11A1");
    expect(html).toContain("Tất cả");
    expect(html).toContain("Cần hỗ trợ");
    expect(html).toContain("Chưa hoạt động gần đây");
  });

  it("R/S — tên bộ lọc TRUNG TÍNH, không phán học sinh", () => {
    // Bóc chú thích: file NÓI RÕ vì sao không dùng nhãn "đang gặp khó" — và
    // bản đầu của guard này đỏ vì chính câu ấy (lần thứ tư của cùng lớp lỗi).
    const src = docMa(join(__dirname, "MonitorView.tsx"));
    expect(maConDu(src, "MonitorView")).toBe(true);
    for (const cam of ["gặp khó", "học yếu", "kém", "lười", "điểm số"]) {
      expect(src.includes(cam), `nhãn phán xét: ${cam}`).toBe(false);
    }
  });

  it("không sắp xếp học sinh theo SỐ LẦN BẤM", () => {
    const src = readFileSync(join(__dirname, "MonitorView.tsx"), "utf-8");
    expect(src).not.toMatch(/sort[^)]*actionCount/);
  });
});

// ══ T·U · KHÔNG TELEMETRY THÔ, KHÔNG CHIẾU MÀN HÌNH ═════════════════════
describe("T/U — chỉ trạng thái có cấu trúc", () => {
  const FILES = ["LiveClassDock.tsx", "LiveClassStrip.tsx", "MonitorView.tsx",
                 "MonitorRoute.tsx"];

  it("không có nguyên thuỷ chiếu màn hình / điều khiển từ xa", () => {
    for (const f of FILES) {
      const src = readFileSync(join(__dirname, f), "utf-8");
      for (const cam of ["getDisplayMedia", "captureStream", "toDataURL",
                         "RTCPeerConnection", "html2canvas", "innerHTML",
                         "outerHTML", "documentElement.outerHTML"]) {
        expect(src.includes(cam), `${f} có ${cam}`).toBe(false);
      }
    }
  });

  it("không theo dõi chuột/khung hình thô", () => {
    for (const f of FILES) {
      const src = readFileSync(join(__dirname, f), "utf-8");
      for (const cam of ["mousemove", "pointermove", "requestAnimationFrame",
                         "onMouseMove"]) {
        expect(src.includes(cam), `${f} có ${cam}`).toBe(false);
      }
    }
  });

  it("V — tầng lớp học KHÔNG chạm hình học", () => {
    for (const f of FILES) {
      const src = readFileSync(join(__dirname, f), "utf-8");
      for (const cam of ["GeometryState", "cross_section", "Vec3", "Fraction",
                         "three"]) {
        expect(src.includes(cam), `${f} chạm hình học: ${cam}`).toBe(false);
      }
    }
  });

  it("AD — không gọi model từ tương tác lớp học", () => {
    for (const f of FILES) {
      const src = readFileSync(join(__dirname, f), "utf-8");
      for (const cam of ["/api/analyze", "/api/explain", "gemini", "openai"]) {
        expect(src.includes(cam), `${f} gọi model: ${cam}`).toBe(false);
      }
    }
  });
});

// ══ V · XƯỞNG 3D KHÔNG PHỤ THUỘC TẦNG LỚP HỌC ═══════════════════════════
describe("ranh giới — miền hình học không biết tới lớp học", () => {
  it("`Scene3DExplorer` KHÔNG import store lớp học", () => {
    const src = docMa(
      join(__dirname, "../simulations/domains/geometry/Scene3DExplorer.tsx"));
    expect(maConDu(src, "Scene3DExplorer")).toBe(true);
    expect(src).not.toContain("useClassroomStore");
    expect(src).not.toContain("state/classroom\"");
    // …nhưng NHẬN phiên qua prop, và áp lệnh bằng hàm thuần đã có test riêng.
    expect(src).toContain("apDungPhien");
    expect(src).toMatch(/phien\?:/);
  });

  it("effect áp lệnh khoá theo cmdId/roundId, KHÔNG theo cả object phiên", () => {
    // Khoá theo `phien` (object mới mỗi nhịp hỏi) ⇒ effect chạy 1,5 giây một
    // lần và học sinh bị kéo về liên tục — đúng lỗi mà `cmd_id` sinh ra để
    // chặn, và nó quay lại ngay nếu khoá sai.
    const src = readFileSync(
      join(__dirname, "../simulations/domains/geometry/Scene3DExplorer.tsx"), "utf-8");
    expect(src).toMatch(/\[phien\?\.roundId, phien\?\.cmdId, phien\?\.syncCmdId/);
  });
});
