/**
 * `InteractionState` — mười hai ca A–L. **0 lời gọi mạng, 0 LLM.**
 *
 * Ca quan trọng nhất là E: **bung hình không đổi một con số nào**. Nếu nó đỏ
 * thì "mô phỏng" đang nói dối về hình — hiệu ứng nhìn đã rò vào toán học, và
 * mọi phép đo sau đó nói về một hình khác hình đề bài.
 */
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { objectsAt, stepCount } from "./scene3d-model";
import {
  TRANG_THAI_DAU,
  collapse,
  collapseAll,
  dependencyClosure,
  deserialize,
  directDependencies,
  explode,
  hide,
  highlightSet,
  isVisible,
  isolate,
  isolateGroup,
  reset,
  select,
  selectableIds,
  semanticTree,
  serialize,
  setStep,
  show,
  showAll,
  taoTrangThai,
  visualTransformOf,
} from "./interaction-state";

/** Tứ diện `ABCS` + trung điểm M của AB + thể tích. Đủ sáu thao tác. */
const CANH: Scene3D = {
  objects: [
    {
      id: "A", label: "A", type: "point3", render: "point_marker",
      origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"],
      parent: "chop", display_group: ["given"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: { assumption: "chọn A làm gốc" },
    },
    {
      id: "B", label: "B", type: "point3", render: "point_marker",
      origin: "free", producer: null, depends: [], xyz: ["1", "0", "0"],
      parent: "chop", display_group: ["given"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: { fact_id: "ab_length" },
    },
    {
      id: "C", label: "C", type: "point3", render: "point_marker",
      origin: "free", producer: null, depends: [], xyz: ["0", "1", "0"],
      parent: "chop", display_group: ["given"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: {},
    },
    {
      id: "S", label: "S", type: "point3", render: "point_marker",
      origin: "free", producer: null, depends: [], xyz: ["0", "0", "1"],
      parent: "chop", display_group: ["given"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: {},
    },
    {
      id: "M", label: "M", type: "point3", render: "point_marker",
      origin: "derived", producer: "construct_point.midpoint",
      depends: ["A", "B"], xyz: ["1/2", "0", "0"],
      parent: null, display_group: ["construction"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: { instruction: "construct_point.midpoint" },
    },
    {
      id: "chop", label: "S.ABC", type: "solid", render: "mesh",
      origin: "derived", producer: "construct_solid",
      depends: ["A", "B", "C", "S"],
      vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
      faces: [[0, 1, 2], [0, 1, 3], [1, 2, 3], [0, 2, 3]],
      parent: null, display_group: ["construction", "solid", "target"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: { instruction: "construct_solid" },
    },
    {
      id: "V", label: "V", type: "quantity", render: "readout",
      origin: "derived", producer: "measure.volume", depends: ["chop"],
      value: "1/6",
      parent: null, display_group: ["construction", "measurement", "target"],
      visual_transform: { translate: ["0", "0", "0"], scale: "1" },
      source: { instruction: "measure.volume" },
    },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Đặt hệ trục." },
    { step_index: 1, action: "CREATE", object: "M", depends: ["A", "B"], explanation: "Dựng M là trung điểm AB." },
    { step_index: 2, action: "CREATE", object: "chop", depends: ["A", "B", "C", "S"], explanation: "Dựng khối chóp." },
    { step_index: 3, action: "MEASURE", object: "V", depends: ["chop"], explanation: "Đo thể tích." },
  ],
  free_objects: ["A", "B", "C", "S"],
};

const idsOf = (s: Scene3D) => s.objects.map((o) => o.id);
const banSao = () => JSON.parse(JSON.stringify(CANH)) as Scene3D;

// ══ A · bốn trường mới có mặt ═══════════════════════════════════════════
describe("A · hợp đồng thực thể", () => {
  it("mọi thực thể mang đủ bốn trường tương tác", () => {
    for (const o of CANH.objects) {
      expect(o).toHaveProperty("parent");
      expect(Array.isArray(o.display_group)).toBe(true);
      expect(o.visual_transform).toBeDefined();
      expect(o.source).toBeDefined();
    }
  });
});

// ══ B · parent KHÔNG thay depends ═══════════════════════════════════════
describe("B · parent và depends là hai quan hệ khác nhau", () => {
  it("M phụ thuộc A,B nhưng KHÔNG nằm trong A hay B", () => {
    expect(directDependencies(CANH, "M")).toEqual(["A", "B"]);
    const m = CANH.objects.find((o) => o.id === "M")!;
    expect(m.parent).toBeNull();
  });

  it("A nằm trong khối nhưng KHÔNG phụ thuộc khối", () => {
    const a = CANH.objects.find((o) => o.id === "A")!;
    expect(a.parent).toBe("chop");
    expect(directDependencies(CANH, "A")).toEqual([]);
    // Chiều ngược lại: khối phụ thuộc A, mà A không phải con của quan hệ ấy.
    expect(directDependencies(CANH, "chop")).toContain("A");
  });
});

// ══ C · display_group ổn định ═══════════════════════════════════════════
describe("C · nhóm hiển thị", () => {
  it("cùng cảnh cho cùng nhóm, không phụ thuộc thứ tự gọi", () => {
    const a = isolateGroup(taoTrangThai(), CANH, "given").isolated_ids;
    const b = isolateGroup(select(taoTrangThai(), "M"), CANH, "given").isolated_ids;
    expect(a).toEqual(b);
    expect(a).toEqual(["A", "B", "C", "S"]);
  });

  it("nhóm không tồn tại ⇒ tập rỗng, không ném", () => {
    expect(isolateGroup(taoTrangThai(), CANH, "base").isolated_ids).toEqual([]);
  });
});

// ══ D · visual_transform mặc định là đồng nhất thức ═════════════════════
describe("D · biến đổi trình bày mặc định", () => {
  it("chưa bung ⇒ đồng nhất thức cho mọi vật", () => {
    for (const o of CANH.objects) {
      expect(visualTransformOf(taoTrangThai(), CANH, o.id)).toEqual({
        translate: ["0", "0", "0"], scale: "1",
      });
    }
  });

  it("vật không tồn tại ⇒ đồng nhất thức, không ném", () => {
    expect(visualTransformOf(taoTrangThai(), CANH, "khong-co").scale).toBe("1");
  });
});

// ══ E · BUNG KHÔNG ĐỔI TOÁN HỌC — ca quan trọng nhất ════════════════════
describe("E · bung hình không chạm GeometryState", () => {
  it("mọi toạ độ, phương, pháp tuyến và SỐ ĐO nguyên vẹn sau khi bung", () => {
    const truoc = banSao();
    const s = explode(explode(taoTrangThai(), "given"), "solid");
    for (const o of CANH.objects) visualTransformOf(s, CANH, o.id);
    expect(CANH).toEqual(truoc);
  });

  it("số đo V vẫn là 1/6 sau khi bung", () => {
    const s = explode(taoTrangThai(), "measurement");
    visualTransformOf(s, CANH, "V");
    expect(CANH.objects.find((o) => o.id === "V")!.value).toBe("1/6");
  });

  it("bung sinh một dịch chuyển THẬT cho vật có nhóm ấy", () => {
    const s = explode(taoTrangThai(), "given");
    const t = visualTransformOf(s, CANH, "B");
    expect(t.translate).not.toEqual(["0", "0", "0"]);
  });

  it("tất định: bung hai lần cho cùng một kết quả", () => {
    const s = explode(taoTrangThai(), "given");
    expect(visualTransformOf(s, CANH, "B")).toEqual(
      visualTransformOf(s, CANH, "B"),
    );
  });
});

// ══ F · gộp trả về đồng nhất thức ══════════════════════════════════════
describe("F · gộp", () => {
  it("collapse trả biến đổi về đồng nhất thức", () => {
    const s = collapse(explode(taoTrangThai(), "given"), "given");
    expect(visualTransformOf(s, CANH, "B")).toEqual({
      translate: ["0", "0", "0"], scale: "1",
    });
  });

  it("collapseAll xoá mọi nhóm đang bung", () => {
    const s = collapseAll(explode(explode(taoTrangThai(), "given"), "solid"));
    expect(s.exploded_groups).toEqual([]);
  });
});

// ══ G · xuất xứ giữ được ═══════════════════════════════════════════════
describe("G · xuất xứ cho ô soi", () => {
  it("giữ đủ ba mẩu: dữ kiện, giả thiết, câu lệnh", () => {
    const g = (id: string) => CANH.objects.find((o) => o.id === id)!.source!;
    expect(g("B").fact_id).toBe("ab_length");
    expect(g("A").assumption).toContain("gốc");
    expect(g("M").instruction).toBe("construct_point.midpoint");
  });

  it("ô soi của M đủ trả lời 'nó ở đâu ra' mà không gọi gì", () => {
    const m = CANH.objects.find((o) => o.id === "M")!;
    expect([m.label, m.type, m.producer, m.depends.join(",")]).toEqual([
      "M", "point3", "construct_point.midpoint", "A,B",
    ]);
  });
});

// ══ H · tô sáng phụ thuộc TRỰC TIẾP ════════════════════════════════════
describe("H · tô sáng phụ thuộc", () => {
  it("chọn M ⇒ tô M, A, B", () => {
    expect(highlightSet(CANH, "M")).toEqual(["A", "B", "M"]);
  });

  it("chọn V ⇒ tô V và khối, KHÔNG tô các đỉnh (gián tiếp)", () => {
    expect(highlightSet(CANH, "V")).toEqual(["V", "chop"]);
  });
});

// ══ I · bao đóng không lặp vô hạn ══════════════════════════════════════
describe("I · bao đóng phụ thuộc", () => {
  it("V kéo theo cả khối lẫn bốn đỉnh", () => {
    expect(dependencyClosure(CANH, "V")).toEqual(["A", "B", "C", "S", "chop"]);
  });

  it("đồ thị có CHU TRÌNH vẫn dừng", () => {
    const vong: Scene3D = {
      ...CANH,
      objects: [
        { ...CANH.objects[0], id: "X", depends: ["Y"] },
        { ...CANH.objects[0], id: "Y", depends: ["X"] },
      ],
    };
    expect(dependencyClosure(vong, "X")).toEqual(["Y"]);
  });

  it("tự phụ thuộc không làm treo", () => {
    const tu: Scene3D = {
      ...CANH,
      objects: [{ ...CANH.objects[0], id: "X", depends: ["X"] }],
    };
    expect(dependencyClosure(tu, "X")).toEqual([]);
  });
});

// ══ J · tua bước tất định ══════════════════════════════════════════════
describe("J · phát lại theo timeline", () => {
  it("mỗi bước cho đúng một tập vật, và tập ấy chỉ lớn dần", () => {
    const tap = [0, 1, 2, 3].map((k) => objectsAt(CANH, k).map((o) => o.id));
    expect(tap[0].sort()).toEqual(["A", "B", "C", "S"]);
    expect(tap[1]).toContain("M");
    expect(tap[2]).toContain("chop");
    expect(tap[3]).toContain("V");
    for (let i = 1; i < tap.length; i++) {
      expect(tap[i].length).toBeGreaterThanOrEqual(tap[i - 1].length);
    }
  });

  it("bước ngoài biên bị kẹp, không ném", () => {
    const s = taoTrangThai();
    expect(setStep(s, CANH, -5).current_step).toBe(0);
    expect(setStep(s, CANH, 99).current_step).toBe(stepCount(CANH) - 1);
  });

  it("cùng bước ⇒ cùng kết quả (không có ngẫu nhiên, không có thời gian)", () => {
    expect(objectsAt(CANH, 2).map((o) => o.id)).toEqual(
      objectsAt(CANH, 2).map((o) => o.id),
    );
  });
});

// ══ K · reset sạch ═════════════════════════════════════════════════════
describe("K · reset", () => {
  it("trả về đúng trạng thái đầu sau một chuỗi thao tác", () => {
    let s = taoTrangThai();
    s = select(s, "M");
    s = hide(s, "C");
    s = isolate(s, ["A", "B"]);
    s = explode(s, "given");
    s = setStep(s, CANH, 2);
    expect(reset()).toEqual(TRANG_THAI_DAU);
  });

  it("show/showAll gỡ đúng thứ nó gỡ", () => {
    let s = hide(hide(taoTrangThai(), "C"), "S");
    s = show(s, "C");
    expect(s.hidden_ids).toEqual(["S"]);
    expect(isolate(s, ["A"]).hidden_ids).toEqual(["S"]);
    expect(showAll(s).hidden_ids).toEqual([]);
  });
});

// ══ L · tuần tự hoá không mất semantic id ══════════════════════════════
describe("L · tuần tự hoá", () => {
  it("vòng đi–về giữ nguyên mọi trường", () => {
    let s = taoTrangThai();
    s = select(s, "chop");
    s = hide(s, "C");
    s = isolate(s, ["A", "B", "M"]);
    s = explode(s, "solid");
    s = setStep(s, CANH, 2);
    expect(deserialize(serialize(s))).toEqual(s);
  });

  it("chuỗi hỏng ⇒ trạng thái đầu, KHÔNG ném", () => {
    expect(deserialize("{{{")).toEqual(TRANG_THAI_DAU);
  });

  it("phiên lưu bằng bản CŨ (thiếu trường) vẫn mở được", () => {
    expect(deserialize('{"selected_id":"M"}')).toEqual({
      ...TRANG_THAI_DAU, selected_id: "M",
    });
  });
});

// ══ ẨN / CÔ LẬP — hai ý định khác nhau ═════════════════════════════════
describe("ẩn và cô lập không được gộp", () => {
  const tonTai = new Set(idsOf(CANH));

  it("cô lập giữ đúng tập được nêu", () => {
    const s = isolate(taoTrangThai(), ["A", "B"]);
    expect(isVisible(s, "A", tonTai)).toBe(true);
    expect(isVisible(s, "chop", tonTai)).toBe(false);
  });

  it("bỏ cô lập KHÔNG hiện lại vật người dùng đã chủ động ẩn", () => {
    let s = hide(taoTrangThai(), "C");
    s = isolate(s, ["A", "C"]);
    s = { ...s, isolated_ids: [] };
    expect(isVisible(s, "C", tonTai)).toBe(false);
    expect(isVisible(s, "A", tonTai)).toBe(true);
  });

  it("vật chưa tồn tại ở bước này thì không hiện dù không bị ẩn", () => {
    const daCo = new Set(objectsAt(CANH, 0).map((o) => o.id));
    expect(isVisible(taoTrangThai(), "chop", daCo)).toBe(false);
    expect(isVisible(taoTrangThai(), "A", daCo)).toBe(true);
  });
});

// ══ CÂY PHÂN RÃ ═══════════════════════════════════════════════════════
describe("cây phân rã ngữ nghĩa", () => {
  it("KHỐI là nút gốc; đỉnh của nó gom theo HẠNG MỤC bên dưới", () => {
    const cay = semanticTree(CANH);
    const khoi = cay.find((n) => n.id === "chop")!;
    expect(khoi.label).toBe("S.ABC");
    const hm = khoi.children.map((c) => c.label);
    expect(hm).toEqual(["Điểm"]);
    expect(khoi.children[0].children.map((c) => c.id).sort()).toEqual([
      "A", "B", "C", "S",
    ]);
  });

  it("vật không có cha lên hạng mục ở GỐC, không bị đoán một cái cha", () => {
    const cay = semanticTree(CANH);
    const gocHM = Object.fromEntries(
      cay.filter((n) => n.isCategory).map((n) => [n.label, n]),
    );
    expect(gocHM["Điểm"].children.map((c) => c.id)).toEqual(["M"]);
    expect(gocHM["Đại lượng"].children.map((c) => c.id)).toEqual(["V"]);
  });

  it("KHÔNG dựng hạng mục rỗng", () => {
    const cay = semanticTree(CANH);
    const di = (ns: ReturnType<typeof semanticTree>): boolean =>
      ns.every((n) => (n.isCategory ? n.children.length > 0 : true) && di(n.children));
    expect(di(cay)).toBe(true);
    // Cảnh không có mặt nào ⇒ không có hạng mục "Mặt".
    const nhan = new Set<string>();
    const gom = (ns: ReturnType<typeof semanticTree>) => {
      for (const n of ns) { nhan.add(n.label); gom(n.children); }
    };
    gom(cay);
    expect(nhan.has("Mặt")).toBe(false);
  });

  it("mọi thực thể xuất hiện ĐÚNG MỘT LẦN trong cây", () => {
    const dem = new Map<string, number>();
    const di = (ns: ReturnType<typeof semanticTree>) => {
      for (const n of ns) {
        if (!n.isCategory) dem.set(n.id, (dem.get(n.id) ?? 0) + 1);
        di(n.children);
      }
    };
    di(semanticTree(CANH));
    expect([...dem.values()].every((v) => v === 1)).toBe(true);
    expect(dem.size).toBe(CANH.objects.length);
  });

  it("selectableIds bỏ nút gộp, giữ mọi thực thể thật", () => {
    expect(selectableIds(semanticTree(CANH)).sort()).toEqual(
      CANH.objects.map((o) => o.id).sort(),
    );
  });
});
