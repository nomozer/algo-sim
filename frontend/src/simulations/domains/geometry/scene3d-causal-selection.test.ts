/**
 * TRUY NGƯỢC NHÂN QUẢ khi học sinh CHỌN một vật. **0 mạng, 0 LLM.**
 *
 * Cảnh là **đầu ra thật của backend** — `scene3d-circumsphere-fixture.json`,
 * sinh từ chương trình mà mô hình đã viết ở `probe-contract-waves-2`, chạy qua
 * interpreter thật. Viết tay một cảnh thì test xanh cả khi phép dẫn xuất hỏng,
 * và chỗ hỏng ở đây nằm ĐÚNG trong phép dẫn xuất ấy.
 *
 * ─── LỖI ĐƯỢC CANH ─────────────────────────────────────────────────────────
 *
 * `simulation_state.dependency_graph` từng lọc cạnh qua `memory_declarations`.
 * Vật dựng bằng `construct_*` không cần khai báo, nên **mọi cạnh trỏ tới một
 * vật dẫn xuất bị lọc mất**. Hậu quả ở đúng bề mặt này: bấm vào đáp số `R` thì
 * `dependencyClosure` trả về **rỗng** — học sinh không thấy `R` đến từ đâu.
 *
 * ─── HAI TẬP, VÀ VÌ SAO PHẢI TÁCH ──────────────────────────────────────────
 *
 *   SEMANTIC_CLOSURE   mọi vật chuỗi dựng đi qua, kể cả vật KHÔNG VẼ ĐƯỢC
 *                      (`render: "non_visual"` — vectơ chẳng hạn)
 *   RENDERABLE_CLOSURE = SEMANTIC_CLOSURE ∩ id có trong cảnh
 *
 * Đòi renderer tô sáng một vectơ là đòi một thứ không có hình. Nhưng vectơ vẫn
 * phải nằm trong closure ngữ nghĩa, nếu không chuỗi **đứt** ở đó và mọi vật
 * phía sau nó biến mất khỏi kết quả — đúng lỗi vừa sửa, chỉ khác nguyên nhân.
 *
 * Kỳ vọng dựng ĐỘC LẬP từ `events` (thẩm quyền khác với `objects[].depends`),
 * nên test không thể xanh nhờ hai bên cùng sai một kiểu.
 */
import { describe, expect, it } from "vitest";
import type { Scene3D } from "./scene3d-model";
import { dependencyClosure, directDependencies, highlightSet } from "./interaction-state";
import fixture from "./scene3d-circumsphere-fixture.json";

const CANH = fixture as unknown as Scene3D;
const ID = new Set(CANH.objects.map((o) => o.id));

/** Bao đóng dựng từ `events` — nguồn sự thật ĐỘC LẬP với `objects[].depends`. */
function closureTuSuKien(id: string): string[] {
  const canh = new Map<string, string[]>();
  for (const e of CANH.events) if (e.object) canh.set(e.object, e.depends);
  const daTham = new Set<string>();
  const hangDoi = [...(canh.get(id) ?? [])];
  while (hangDoi.length > 0) {
    const x = hangDoi.shift()!;
    if (daTham.has(x) || x === id) continue;
    daTham.add(x);
    hangDoi.push(...(canh.get(x) ?? []));
  }
  return [...daTham].sort();
}

const renderable = (ids: string[]) => ids.filter((i) => ID.has(i)).sort();

describe("A · cạnh trực tiếp của vật dẫn xuất", () => {
  it.each([
    ["D", ["A_prime", "vec_OC"]],
    ["M", ["D", "O"]],
    ["circumsphere", ["M", "O"]],
    ["R", ["circumsphere"]],
  ])("%s giữ đủ phụ thuộc trực tiếp", (id, mong) => {
    expect(directDependencies(CANH, id).sort()).toEqual(mong);
  });
});

describe("B · bao đóng phía học sinh", () => {
  it("khớp bao đóng dựng độc lập từ events", () => {
    for (const o of CANH.objects) {
      expect(dependencyClosure(CANH, o.id)).toEqual(closureTuSuKien(o.id));
    }
  });

  it("chọn R thì truy ngược tới tận điểm gốc", () => {
    const dong = dependencyClosure(CANH, "R");
    // Nút BẮT BUỘC — chuỗi đứt ở bất kỳ mắt nào cũng làm mất phần sau nó.
    for (const nut of ["circumsphere", "M", "O"]) expect(dong).toContain(nut);
    expect(dong).toEqual([
      "A", "A_prime", "B", "C", "D", "M", "O", "circumsphere", "vec_OB", "vec_OC",
    ]);
  });

  it("chọn mặt cầu thì thấy tâm và điểm nó đi qua", () => {
    const dong = dependencyClosure(CANH, "circumsphere");
    for (const nut of ["M", "O"]) expect(dong).toContain(nut);
  });
});

describe("C · SEMANTIC_CLOSURE ⊇ RENDERABLE_CLOSURE", () => {
  it("mọi vật vẽ được trong bao đóng đều được tô sáng", () => {
    for (const id of ["R", "circumsphere", "M", "D"]) {
      const nguNghia = dependencyClosure(CANH, id);
      expect(highlightSet(CANH, id, true).sort()).toEqual(
        [...new Set([id, ...renderable(nguNghia)])].sort(),
      );
    }
  });

  it("vật KHÔNG VẼ ĐƯỢC vẫn ở trong bao đóng ngữ nghĩa", () => {
    const khongVe = CANH.objects
      .filter((o) => o.render === "non_visual")
      .map((o) => o.id);
    expect(khongVe).toContain("vec_OB");
    // Nếu lọc chúng khỏi closure thì chuỗi đứt ở A_prime và mất luôn A.
    expect(dependencyClosure(CANH, "R")).toEqual(
      expect.arrayContaining(khongVe),
    );
  });
});

describe("D · fixture đúng là đầu ra backend", () => {
  it("13 sự kiện, 16 vật, R = √3", () => {
    expect(CANH.events).toHaveLength(13);
    expect(CANH.objects).toHaveLength(16);
    const r = CANH.objects.find((o) => o.id === "R")!;
    expect((r as unknown as { value: string }).value).toBe("√3");
  });

  it("không cạnh nào trỏ ra ngoài cảnh", () => {
    for (const o of CANH.objects) {
      for (const d of o.depends) expect(ID.has(d)).toBe(true);
    }
  });
});
