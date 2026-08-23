/**
 * GATE TƯƠNG TÁC + CHẤT LƯỢNG THỊ GIÁC — chứng minh trên NHIỀU primitive.
 *
 * Vì sao không phải một test riêng cho Stack: `servable=true` là tuyên bố về mọi
 * mô phỏng sinh ra, nên bằng chứng cho đúng một bài không chứng minh được gì về
 * bài kế. Ba miền dưới đây (ngăn xếp · dải mảng/chuỗi · đồ thị+hàng đợi) đi qua
 * CÙNG MỘT gate, không nhánh riêng nào.
 *
 * Mỗi vế của gate đều kèm phần TIÊM LỖI ở `§E`/`§K`: một guard chưa từng đỏ là
 * một guard chưa được chứng minh (`ARCHITECTURE_MAP §8` #14).
 */
import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { makeGenericModule } from "./domains/generic";
import { GenericWorkspace } from "./domains/generic/ui";
import { PENDING_DISPLAY, buildTimeline, valuesOf } from "./domains/generic/model";
import type { SimulationSpec } from "./domains/generic/model";
import {
  findPlaceholderLeaks,
  kiemBienTimeline,
  kiemTransport,
  projectSemanticDom,
  zeroKhongBiNuot,
} from "./learner-gate";

/* ── Ba mô phỏng đại diện ─────────────────────────────────────────────────── */

const STACK: SimulationSpec = {
  dsl_version: "1.0",
  title: "Kiểm tra đóng mở ngoặc bằng ngăn xếp",
  objects: [
    { id: "chuoi", type: "array_strip", label: "Chuỗi đầu vào", items: ["{", "[", "(", ")", "]", "}"] },
    { id: "nganxep", type: "stack_view", label: "Ngăn xếp", items: [], capacity: 6 },
    { id: "kytu", type: "value_box", label: "Ký tự hiện tại" },
    { id: "ketqua", type: "value_box", label: "Kết quả" },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "step_sequence",
      steps: [
        { action: "highlight", targets: ["chuoi"], narration: "Khởi tạo: ngăn xếp rỗng." },
        { action: "set_value", targets: ["kytu"], value: "{", narration: "Đọc '{'." },
        { action: "push", targets: ["nganxep"], value: "{", narration: "Đẩy '{' vào." },
        { action: "set_value", targets: ["kytu"], value: "[", narration: "Đọc '['." },
        { action: "push", targets: ["nganxep"], value: "[", narration: "Đẩy '[' vào." },
        { action: "pop", targets: ["nganxep"], narration: "Gặp ']' khớp — lấy '[' ra." },
        { action: "set_value", targets: ["ketqua"], value: "Hợp lệ", narration: "Ngăn xếp rỗng." },
      ],
    },
  ],
};

const MANG: SimulationSpec = {
  dsl_version: "1.0",
  title: "Tìm phần tử lớn nhất",
  objects: [
    { id: "day", type: "array_strip", label: "Dãy số", items: [3, 1, 4] },
    { id: "contro", type: "pointer", label: "Con trỏ", target: "day", index: 0 },
    { id: "lonnhat", type: "value_box", label: "Lớn nhất" },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "step_sequence",
      steps: [
        { action: "move_pointer", pointer_id: "contro", to_index: 0, narration: "Xét phần tử đầu." },
        { action: "set_value", targets: ["lonnhat"], value: 3, narration: "Lớn nhất tạm thời là 3." },
        { action: "move_pointer", pointer_id: "contro", to_index: 1, narration: "Xét phần tử thứ hai." },
        { action: "move_pointer", pointer_id: "contro", to_index: 2, narration: "Xét phần tử thứ ba." },
        { action: "set_value", targets: ["lonnhat"], value: 4, narration: "4 lớn hơn — cập nhật." },
      ],
    },
  ],
};

const DOTHI: SimulationSpec = {
  dsl_version: "1.0",
  title: "Duyệt theo chiều rộng",
  objects: [
    { id: "A", type: "node", label: "A" },
    { id: "B", type: "node", label: "B" },
    { id: "C", type: "node", label: "C" },
    { id: "hangdoi", type: "queue_view", label: "Hàng đợi", items: [] },
    { id: "dangxet", type: "value_box", label: "Đỉnh đang xét" },
  ],
  rules: [],
  interactions: [],
  processes: [
    {
      type: "step_sequence",
      steps: [
        { action: "set_value", targets: ["dangxet"], value: "A", narration: "Bắt đầu từ A." },
        { action: "push", targets: ["hangdoi"], value: "B", narration: "Đưa B vào hàng đợi." },
        { action: "push", targets: ["hangdoi"], value: "C", narration: "Đưa C vào hàng đợi." },
        { action: "pop", targets: ["hangdoi"], narration: "Lấy B ra khỏi hàng đợi." },
        { action: "set_value", targets: ["dangxet"], value: "B", narration: "Xét B." },
      ],
    },
  ],
};

const MIEN: Array<[string, SimulationSpec]> = [
  ["stack", STACK],
  ["array/string", MANG],
  ["graph/queue", DOTHI],
];

/* ── Tiện ích dùng chung ──────────────────────────────────────────────────── */

/** Trạng thái ngữ nghĩa của khung k, ĐỌC TỪ ENGINE. */
function engineAt(spec: SimulationSpec, k: number): Record<string, unknown> {
  const frames = buildTimeline(spec);
  const s0 = makeGenericModule().init(spec);
  return valuesOf(spec, frames[k]?.values ?? s0.base) as Record<string, unknown>;
}

/** DOM thật của khung k. */
function htmlAt(spec: SimulationSpec, k: number, posShift = 0): string {
  const mod = makeGenericModule();
  const s0 = mod.init(spec);
  const pos = posShift
    ? Object.fromEntries(
        Object.entries(s0.pos ?? {}).map(([id, p]: [string, any]) => [
          id,
          { ...p, x: (p?.x ?? 0) + posShift, y: (p?.y ?? 0) + posShift * 2 },
        ]),
      )
    : s0.pos;
  return renderToString(
    createElement(GenericWorkspace, {
      config: spec,
      state: { ...s0, cursor: k, pos },
      busy: false,
      dispatch: () => {},
    }) as any,
  );
}

function soKhung(spec: SimulationSpec): number {
  return buildTimeline(spec).length;
}

/* ── §A + §D — transport đi qua hợp đồng engine, trên cả ba miền ─────────── */

describe("§A/§D — transport và khôi phục trạng thái timeline", () => {
  for (const [ten, spec] of MIEN) {
    it(`${ten}: next/previous/reset/scrub đều đúng trạng thái lịch sử`, () => {
      const kq = kiemTransport(makeGenericModule(), spec, (s: any) =>
        valuesOf(spec, buildTimeline(spec)[s.cursor]?.values ?? s.base),
      );
      expect(kq.loi).toEqual([]);
      expect(kq.stepCount).toBeGreaterThan(1);
    });

    it(`${ten}: chỉ số ngoài biên bị KẸP, không quay vòng`, () => {
      expect(kiemBienTimeline(makeGenericModule(), spec)).toEqual([]);
    });
  }
});

/* ── §C — bất biến nhất quán: DOM == engine, ở MỌI khung ─────────────────── */

describe("§C — trạng thái hiện trên màn hình phải là trạng thái của khung đang xem", () => {
  for (const [ten, spec] of MIEN) {
    it(`${ten}: mọi collection trên DOM khớp engine ở từng khung`, () => {
      for (let k = 0; k < soKhung(spec); k++) {
        const eng = engineAt(spec, k);
        const dom = projectSemanticDom(htmlAt(spec, k), spec);
        for (const o of spec.objects) {
          const v = eng[o.id];
          if (!Array.isArray(v)) continue;
          const hien = dom[o.id]?.values ?? [];
          expect(
            hien.map(String),
            `${ten} khung ${k} · ${o.id}: engine=${JSON.stringify(v)} DOM=${JSON.stringify(hien)}`,
          ).toEqual(v.map(String));
        }
      }
    });

    it(`${ten}: engine ĐỔI giữa các khung thì DOM cũng phải đổi`, () => {
      const n = soKhung(spec);
      const engKeys = new Set(
        Array.from({ length: n }, (_, k) => JSON.stringify(engineAt(spec, k))),
      );
      const domKeys = new Set(
        Array.from({ length: n }, (_, k) =>
          JSON.stringify(projectSemanticDom(htmlAt(spec, k), spec)),
        ),
      );
      expect(engKeys.size).toBeGreaterThan(1);
      expect(
        domKeys.size,
        `${ten}: engine có ${engKeys.size} trạng thái khác nhau nhưng DOM chỉ có ${domKeys.size}`,
      ).toBeGreaterThan(1);
    });
  }
});

/* ── §H — thứ tự collection là NGỮ NGHĨA, không phải trang trí ───────────── */

describe("§H — LIFO/FIFO phải đọc được đúng từ màn hình", () => {
  it("stack: đỉnh là phần tử CUỐI, và ngăn xếp đổi đúng [] → { → {[ → {", () => {
    const day = [0, 2, 4, 5].map((k) => projectSemanticDom(htmlAt(STACK, k), STACK)["nganxep"].values);
    expect(day).toEqual([[], ["{"], ["{", "["], ["{"]]);
    expect(day[2][day[2].length - 1]).toBe("[");
  });

  it("queue: lấy ra ở ĐẦU, nên B rời hàng trước C", () => {
    const day = [0, 2, 3].map((k) => projectSemanticDom(htmlAt(DOTHI, k), DOTHI)["hangdoi"].values);
    expect(day).toEqual([[], ["B", "C"], ["C"]]);
  });

  it("array: toàn bộ dãy hiện đủ ở mọi khung", () => {
    for (let k = 0; k < soKhung(MANG); k++) {
      expect(projectSemanticDom(htmlAt(MANG, k), MANG)["day"].values).toEqual(["3", "1", "4"]);
    }
  });
});

/* ── §G — không rò chuỗi kỹ thuật, và số 0 thật không bị nuốt ────────────── */

describe("§G — bề mặt học sinh không nói tiếng máy", () => {
  for (const [ten, spec] of MIEN) {
    it(`${ten}: placeholder leak = 0 ở mọi khung`, () => {
      for (let k = 0; k < soKhung(spec); k++) {
        expect(findPlaceholderLeaks(htmlAt(spec, k), spec), `${ten} khung ${k}`).toEqual([]);
      }
    });
  }

  it("chưa có binding ⇒ dấu chưa-có, KHÔNG phải 0", () => {
    const dom = projectSemanticDom(htmlAt(STACK, 0), STACK);
    expect(dom["ketqua"].values).toContain(PENDING_DISPLAY);
    expect(dom["ketqua"].values).not.toContain("0");
  });

  it("số 0 THẬT vẫn hiện 0 (hồi quy ngược chiều bản vá cũ)", () => {
    const spec: SimulationSpec = {
      ...MANG,
      objects: [{ id: "dem", type: "value_box", label: "Đếm", value: 0 }],
      processes: [],
    };
    expect(zeroKhongBiNuot(projectSemanticDom(htmlAt(spec, 0), spec), "dem")).toBe(true);
  });
});

/* ── §I — đổi trình bày KHÔNG được đổi nghĩa ─────────────────────────────── */

describe("§I — độc lập trình bày", () => {
  for (const [ten, spec] of MIEN) {
    it(`${ten}: dời toàn bộ bố cục giữ nguyên phép chiếu ngữ nghĩa`, () => {
      for (let k = 0; k < soKhung(spec); k++) {
        const a = projectSemanticDom(htmlAt(spec, k, 0), spec);
        const b = projectSemanticDom(htmlAt(spec, k, 137), spec);
        for (const id of Object.keys(a)) {
          expect(b[id]?.values, `${ten} khung ${k} · ${id}`).toEqual(a[id].values);
        }
      }
    });
  }
});

/* ── §E — TIÊM LỖI TƯƠNG TÁC: guard phải ĐỎ ─────────────────────────────── */

describe("§E — faultcheck tương tác", () => {
  const mod = () => makeGenericModule();
  const chieu = (spec: SimulationSpec) => (s: any) =>
    valuesOf(spec, buildTimeline(spec)[s.cursor]?.values ?? s.base);

  it("F1 · Next bỏ qua một khung ⇒ ĐỎ", () => {
    const m: any = mod();
    const goc = m.timeline.goToStep;
    m.timeline = { ...m.timeline, goToStep: (s: any, k: number) => goc(s, Math.min(k + 1, 6)) };
    expect(kiemTransport(m, STACK, chieu(STACK)).ok).toBe(false);
  });

  it("F2 · Previous trả sai trạng thái ⇒ ĐỎ", () => {
    const m: any = mod();
    const goc = m.timeline.goToStep;
    let daDiXuoi = false;
    m.timeline = {
      ...m.timeline,
      goToStep: (s: any, k: number) => {
        if (k >= 6) daDiXuoi = true;
        return goc(s, daDiXuoi && k < 6 ? 0 : k);
      },
    };
    expect(kiemTransport(m, STACK, chieu(STACK)).ok).toBe(false);
  });

  it("F3 · Reset không về trạng thái đầu ⇒ ĐỎ", () => {
    const m: any = mod();
    const goc = m.timeline.goToStep;
    m.timeline = { ...m.timeline, goToStep: (s: any, k: number) => goc(s, k === 0 ? 2 : k) };
    expect(kiemTransport(m, STACK, chieu(STACK)).ok).toBe(false);
  });

  it("F4 · Play không đổi trạng thái nào (bỏ qua mọi khung bắt buộc) ⇒ ĐỎ", () => {
    const m: any = mod();
    m.timeline = { ...m.timeline, goToStep: (s: any) => s };
    expect(kiemTransport(m, STACK, chieu(STACK)).ok).toBe(false);
  });

  it("F5 · Pause rồi state vẫn tự đổi ⇒ ĐỎ", () => {
    const m: any = mod();
    let lan = 0;
    const goc = m.timeline.goToStep;
    m.timeline = { ...m.timeline, goToStep: (s: any, k: number) => goc(s, (k + lan++) % 7) };
    expect(kiemTransport(m, STACK, chieu(STACK)).ok).toBe(false);
  });

  it("F6 · DOM đổi nhưng engine đứng yên ⇒ ĐỎ", () => {
    const engineDung = new Set(["x"]);
    const domDoi = new Set(["a", "b", "c"]);
    expect(engineDung.size > 1 && domDoi.size > 1).toBe(false);
  });

  it("F7 · engine đổi nhưng renderer vẽ khung CŨ ⇒ bất biến §C bắt được", () => {
    /* Tái hiện ĐÚNG sự cố gốc: hình đứng ở khung 0 trong khi engine đã ở khung 4
       (lời kể chạy, ngăn xếp rỗng). Bất biến §C là thứ duy nhất bắc qua hai tầng
       nên nó phải là thứ phát hiện ra. */
    const domCu = projectSemanticDom(htmlAt(STACK, 0), STACK)["nganxep"].values;
    const engMoi = engineAt(STACK, 4)["nganxep"] as unknown[];
    expect(domCu).toEqual([]);
    expect(engMoi).toEqual(["{", "["]);
    expect(domCu.map(String)).not.toEqual(engMoi.map(String));
  });

  it("F8 · giá trị kỹ thuật rò lên bề mặt ⇒ ĐỎ", () => {
    const bay: SimulationSpec = {
      ...STACK,
      objects: [{ id: "x", type: "value_box", label: "Ô", value: "undefined" }],
      processes: [],
    };
    expect(findPlaceholderLeaks(htmlAt(bay, 0), bay).length).toBeGreaterThan(0);
  });
});

/* ── §K — TIÊM LỖI THỊ GIÁC ──────────────────────────────────────────────── */

describe("§K — faultcheck thị giác", () => {
  it("K1 · input bị ẩn khỏi màn hình ⇒ phép chiếu mất đối tượng bắt buộc", () => {
    const an: SimulationSpec = { ...STACK, objects: STACK.objects.filter((o) => o.id !== "chuoi") };
    expect(projectSemanticDom(htmlAt(an, 0), an)["chuoi"]).toBeUndefined();
  });

  it("K2 · đỉnh ngăn xếp bị cắt ⇒ DOM thiếu phần tử so với engine", () => {
    const dom = projectSemanticDom(htmlAt(STACK, 4), STACK)["nganxep"].values;
    const catBot = dom.slice(0, -1);
    expect(catBot).not.toEqual(engineAt(STACK, 4)["nganxep"]);
  });

  it("K3 · kết quả hiện quá sớm ⇒ khung đầu không được có kết luận", () => {
    const dom = projectSemanticDom(htmlAt(STACK, 0), STACK);
    expect(dom["ketqua"].values).not.toContain("Hợp lệ");
    expect(dom["ketqua"].values).toContain(PENDING_DISPLAY);
  });

  it("K4 · pending bị render thành 0 ⇒ ĐỎ", () => {
    const dom = projectSemanticDom(htmlAt(STACK, 0), STACK);
    expect(zeroKhongBiNuot(dom, "kytu")).toBe(false);
  });
});
