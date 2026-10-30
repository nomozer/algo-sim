/**
 * W4 · «Vì sao» của bước dựng và điều hướng bằng bàn phím. **0 mạng, 0 LLM.** Cảnh thật xuất từ bộ dev W4
 * (`TP1.canon.area`: mặt phẳng song song đáy ⇒ ba giao tuyến song song ba cạnh đáy, backend đã kiểm chính xác).
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import type { Scene3D } from "./scene3d-model";
import {
  anchorOfGeometryStep,
  geometryJustificationsAt,
  geometryStepCount,
  geometryTimeline,
} from "./scene3d-model";

const CANH: Scene3D = JSON.parse(readFileSync(fileURLToPath(new URL(
  "../../../../../docs/evaluation/geometry/runs/geometry-generalization-and-pedagogical-construction/dev-corpus/scene-TP1.canon.area.json",
  import.meta.url)), "utf8")).scene3d;
const nguon = (f: string) => readFileSync(new URL(f, import.meta.url), "utf8").replace(/\r\n/g, "\n");
const coLyDo = (s: Scene3D) => geometryTimeline(s).map((g) => geometryJustificationsAt(s, g.anchor));

describe("W4 · «Vì sao» chỉ là quan hệ backend đã chứng nhận", () => {
  it("bước dựng giao tuyến mang lý do song song; bước dữ kiện thì không", () => {
    const tatCa = coLyDo(CANH).flat();
    expect(tatCa).toHaveLength(3);
    for (const t of tatCa) expect(t).toMatch(/^Vì \(α\) song song với \S+ và \S+ nằm trong mặt \(\S+\), nên giao tuyến/);
    expect(geometryJustificationsAt(CANH, 0)).toEqual([]);
  });

  it("mỗi lý do thuộc đúng bước của sự kiện sinh ra nó (không rò sang bước khác)", () => {
    const t = geometryTimeline(CANH);
    for (const g of t) {
      const tuSuKien = CANH.events
        .filter((e) => e.step_index >= g.start && e.step_index <= g.end && e.justification_text)
        .map((e) => e.justification_text);
      expect(geometryJustificationsAt(CANH, g.anchor)).toEqual([...new Set(tuSuKien)]);
    }
  });

  it("frontend không tự suy ra lý do: cảnh không có `justification_text` ⇒ không có dòng «Vì sao»", () => {
    const tron: Scene3D = { ...CANH, events: CANH.events.map(({ justification_text: _b, ...e }) => e) };
    expect(coLyDo(tron).flat()).toEqual([]);
  });

  it("lý do chứa định danh máy bị lọc như lời kể (cùng `learnerTextIsSafe`)", () => {
    const ro: Scene3D = {
      ...CANH,
      events: CANH.events.map((e) => (e.justification_text ? { ...e, justification_text: "Vì mp_td_sec song song." } : e)),
    };
    expect(coLyDo(ro).flat()).toEqual([]);
  });

  it("bảng «Các bước dựng» hiện dòng «Vì sao» ngay dưới mô tả của bước đang xem", () => {
    const src = nguon("./scene3d-playback.tsx");
    expect(src).toMatch(/const lyDo = geometryJustificationsAt\(scene, step\);/);
    expect(src).toMatch(/b\.index === buocHinh && lyDo\.length > 0 &&/);
    expect(src).toContain('className="geo3d-cac-buoc-vi-sao"');
    expect(nguon("../../../styles/global.css")).toContain(".geo3d-cac-buoc-vi-sao {");
  });
});

describe("W4 · điều hướng bước bằng bàn phím trong trình phát", () => {
  it("←/→/Home/End đi qua đúng các hàm bước của mô hình và dừng phát tự động", () => {
    const src = nguon("./scene3d-playback.tsx");
    expect(src).toContain('<div ref={playerRef} className="geo3d-player" onKeyDown={phimBuoc}>');
    expect(src).toMatch(/ArrowLeft: \(s\) => prevGeometryStep\(scene, s\)/);
    expect(src).toMatch(/ArrowRight: \(s\) => nextGeometryStep\(scene, s\)/);
    expect(src).toMatch(/Home: \(\) => anchorOfGeometryStep\(scene, 0\)/);
    expect(src).toMatch(/End: \(\) => anchorOfGeometryStep\(scene, tong - 1\)/);
    expect(src).toMatch(/e\.preventDefault\(\);\n\s*setDangPhat\(false\);\n\s*setStep\(f\);/);
    // thanh kéo (input range) và ô chọn tự xử lý phím của chúng — không giành phím; trình phát không có ô nhập văn bản
    expect(src).toMatch(/t\.closest\("input, select"\)\) return;/);
    // review M2: the floating panel's drag handle consumes arrows (preventDefault) — the player must not also step
    expect(src).toMatch(/if \(e\.defaultPrevented \|\|/);
    expect(nguon("./scene3d-floating-panel.tsx")).toMatch(/preventDefault\(\)/);
  });

  it("Home/End rơi đúng neo bước đầu/cuối của cảnh thật", () => {
    expect(anchorOfGeometryStep(CANH, 0)).toBe(geometryTimeline(CANH)[0].anchor);
    expect(anchorOfGeometryStep(CANH, geometryStepCount(CANH) - 1)).toBe(geometryTimeline(CANH).at(-1)!.anchor);
  });
});
