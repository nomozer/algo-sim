import { describe, expect, it } from "vitest";
import {
  narrationAt,
  objectsAt,
  stepCount,
  type Scene3D,
} from "./scene3d-model";

const scene = {
  objects: [
    { id: "A", label: "Điểm A", notation: "A", type: "point3", render: "point_marker",
      origin: "free", producer: null, depends: [], xyz: ["0", "0", "0"] },
    { id: "day_ABC", label: "Tam giác đáy ABC", notation: "ABC", type: "polygon3",
      render: "polygon", origin: "derived", producer: "construct_polygon", depends: ["A"],
      vertices: [["0", "0", "0"], ["1", "0", "0"], ["0", "1", "0"]] },
    { id: "the_tich_khoi", label: "Thể tích khối", notation: "V", type: "quantity",
      render: "readout", origin: "derived", producer: "measure.volume", depends: ["day_ABC"],
      value: "5" },
  ],
  events: [
    { step_index: 0, action: "INIT", object: null, depends: [], explanation: "Khởi tạo." },
    { step_index: 1, action: "CREATE", object: "day_ABC", depends: ["A"],
      explanation: "Dựng day_ABC." },
    { step_index: 2, action: "MEASURE", object: "the_tich_khoi", depends: ["day_ABC"],
      explanation: "Gán the_tich_khoi = 5." },
  ],
  formation: {
    steps: [
      { step_index: 0, visible_ids: ["A"], focus_ids: [], readout_ids: [],
        learner_text: "Khởi tạo điểm đã cho." },
      { step_index: 1, visible_ids: ["A", "day_ABC"], focus_ids: ["day_ABC"],
        readout_ids: [], learner_text: "Dựng tam giác đáy ABC." },
      { step_index: 2, visible_ids: ["A", "day_ABC", "the_tich_khoi"],
        focus_ids: ["the_tich_khoi"], readout_ids: ["the_tich_khoi"],
        learner_text: "Tính thể tích khối." },
    ],
  },
  free_objects: ["A", "the_tich_khoi"],
} as unknown as Scene3D;

describe("learner surface và explicit formation", () => {
  it("formation snapshot là thẩm quyền visibility khi tua tiến và lùi", () => {
    expect(stepCount(scene)).toBe(3);
    expect(objectsAt(scene, 0).map((o) => o.id)).toEqual(["A"]);
    expect(objectsAt(scene, 2).map((o) => o.id)).toEqual([
      "A", "day_ABC", "the_tich_khoi",
    ]);
    expect(objectsAt(scene, 1).map((o) => o.id)).toEqual(["A", "day_ABC"]);
  });

  it("narration ưu tiên learner_text, không đọc raw explanation", () => {
    expect(narrationAt(scene, 1)).toBe("Dựng tam giác đáy ABC.");
    expect(narrationAt(scene, 1)).not.toContain("day_ABC");
    expect(narrationAt(scene, 2)).not.toContain("the_tich_khoi");
  });

  it("payload legacy thiếu learner_text không được fallback sang machine id", () => {
    const legacy = {
      ...scene,
      formation: undefined,
      events: scene.events.map((event) => ({ ...event })),
    } as unknown as Scene3D;
    expect(narrationAt(legacy, 1)).not.toContain("day_ABC");
    expect(narrationAt(legacy, 2)).not.toContain("the_tich_khoi");
  });
});
