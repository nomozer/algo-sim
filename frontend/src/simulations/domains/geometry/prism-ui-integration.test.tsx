/**
 * KIỂM CHỨNG TÍCH HỢP UI CHO LĂNG TRỤ (PRISM_P01).
 *
 * Kiểm tra:
 * 1. store.loadEnvelope nhận envelope lăng trụ sinh từ production pipeline.
 * 2. scene3d hợp lệ theo schema Three.js / scene3d-model (hopLeScene3D === true).
 * 3. 6 đỉnh A, B, C, D, E, F hiển thị đầy đủ nhãn.
 * 4. 1 solid lăng trụ có 6 đỉnh, 5 mặt, 9 cạnh.
 * 5. Đáp số 30 xuất hiện tại bước đo cuối cùng (readout).
 * 6. semanticTree dựng thành công cây thực thể chứa solid lăng trụ và các đỉnh.
 * 7. Scene3DExplorer renderToString hoàn tất mà không lỗi.
 */
import { beforeEach, describe, expect, it } from "vitest";
import { renderToString } from "react-dom/server";
import { Scene3DExplorer } from "./Scene3DExplorer";
import { registerSemanticDomain } from "../semantic";
import { clearRegistryForTest } from "../../registry";
import { useAppStore } from "../../../state/store";
import { __resetHistoryForTest } from "../../../state/history";
import type { SimulationEnvelope } from "../../types";
import { hienSo, hopLeScene3D, objectsAt, stepCount, type Scene3D } from "./scene3d-model";
import { semanticTree } from "./interaction-state";
import { withSubEntities } from "./scene3d-subentities";

const PRISM_ENVELOPE = {
  "status": "ok",
  "simulation_id": "generic.semantic_program",
  "domain": "geometry",
  "visual_mode": "2d",
  "title": "Thể tích khối lăng trụ đứng có đáy là tam giác vuông",
  "description": "Thể tích khối lăng trụ đứng có đáy là tam giác vuông",
  "config": {
    "spec_version": "1.0",
    "title": "Thể tích khối lăng trụ đứng có đáy là tam giác vuông",
    "frames": [
      {
        "step_index": 0,
        "narration": "Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 1,
        "narration": "Dựng đa giác Tam giác đáy dưới qua 3 đỉnh A, B, C.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 2,
        "narration": "Dựng khối solid_ABCDEF từ 6 đỉnh và 5 mặt.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 3,
        "narration": "Gán dien_tich_day_ABC = 6.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 4,
        "narration": "Gán the_tich_solid_ABCDEF = 30.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 5,
        "narration": "Gán the_tich_lang_tru = 30.",
        "objects": [],
        "highlighted_object_ids": []
      }
    ],
    "view_steps": [
      {
        "view_index": 0,
        "frame_lo": 0,
        "frame_hi": 0,
        "narration": "Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ."
      },
      {
        "view_index": 1,
        "frame_lo": 1,
        "frame_hi": 1,
        "narration": "Dựng đa giác Tam giác đáy dưới qua 3 đỉnh A, B, C."
      },
      {
        "view_index": 2,
        "frame_lo": 2,
        "frame_hi": 2,
        "narration": "Dựng khối solid_ABCDEF từ 6 đỉnh và 5 mặt."
      },
      {
        "view_index": 3,
        "frame_lo": 3,
        "frame_hi": 3,
        "narration": "Gán dien_tich_day_ABC = 6."
      },
      {
        "view_index": 4,
        "frame_lo": 4,
        "frame_hi": 4,
        "narration": "Gán the_tich_solid_ABCDEF = 30."
      },
      {
        "view_index": 5,
        "frame_lo": 5,
        "frame_hi": 5,
        "narration": "Gán the_tich_lang_tru = 30."
      }
    ],
    "grouping_level": "step",
    "presentation_overflow": false,
    "execution_truncated": false
  },
  "notes": null,
  "analysis": {},
  "representation_plan": {},
  "source": "semantic_program",
  "scene3d": {
    "objects": [
      {
        "id": "A",
        "label": "Điểm A",
        "notation": "A",
        "reference": "A",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "solid_ABCDEF",
        "display_group": [
          "given"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "xyz": [
          "0",
          "0",
          "0"
        ]
      },
      {
        "id": "B",
        "label": "Điểm B",
        "notation": "B",
        "reference": "B",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "solid_ABCDEF",
        "display_group": [
          "given"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "xyz": [
          "3",
          "0",
          "0"
        ]
      },
      {
        "id": "C",
        "label": "Điểm C",
        "notation": "C",
        "reference": "C",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "solid_ABCDEF",
        "display_group": [
          "given"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "xyz": [
          "0",
          "4",
          "0"
        ]
      },
      {
        "id": "D",
        "label": "Điểm D",
        "notation": "D",
        "reference": "D",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "solid_ABCDEF",
        "display_group": [
          "given"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "xyz": [
          "0",
          "0",
          "5"
        ]
      },
      {
        "id": "E",
        "label": "Điểm E",
        "notation": "E",
        "reference": "E",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "solid_ABCDEF",
        "display_group": [
          "given"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "xyz": [
          "3",
          "0",
          "5"
        ]
      },
      {
        "id": "F",
        "label": "Điểm F",
        "notation": "F",
        "reference": "F",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "solid_ABCDEF",
        "display_group": [
          "given"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "xyz": [
          "0",
          "4",
          "5"
        ]
      },
      {
        "id": "day_ABC",
        "label": "Tam giác đáy dưới",
        "notation": "ABC",
        "reference": "ABC",
        "role": "Đa giác A, B, C",
        "type": "polygon3",
        "render": "polygon",
        "origin": "derived",
        "producer": "construct_polygon",
        "depends": [
          "A",
          "B",
          "C"
        ],
        "parent": "solid_ABCDEF",
        "display_group": [
          "construction",
          "face"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {
          "instruction": "construct_polygon"
        },
        "vertices": [
          [
            "0",
            "0",
            "0"
          ],
          [
            "3",
            "0",
            "0"
          ],
          [
            "0",
            "4",
            "0"
          ]
        ],
        "vertex_ids": [
          "A",
          "B",
          "C"
        ]
      },
      {
        "id": "solid_ABCDEF",
        "label": "Khối đa diện dựng từ A, B, C, D, E, F",
        "notation": null,
        "reference": "Khối đa diện dựng từ A, B, C, D, E, F",
        "role": "Khối đa diện",
        "type": "solid",
        "render": "mesh",
        "origin": "derived",
        "producer": "construct_solid",
        "depends": [
          "A",
          "B",
          "C",
          "D",
          "E",
          "F"
        ],
        "parent": null,
        "display_group": [
          "construction",
          "solid",
          "target"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {
          "instruction": "construct_solid"
        },
        "vertices": [
          [
            "0",
            "0",
            "0"
          ],
          [
            "3",
            "0",
            "0"
          ],
          [
            "0",
            "4",
            "0"
          ],
          [
            "0",
            "0",
            "5"
          ],
          [
            "3",
            "0",
            "5"
          ],
          [
            "0",
            "4",
            "5"
          ]
        ],
        "vertex_ids": [
          "A",
          "B",
          "C",
          "D",
          "E",
          "F"
        ],
        "faces": [
          [
            0,
            1,
            2
          ],
          [
            3,
            4,
            5
          ],
          [
            0,
            1,
            4,
            3
          ],
          [
            1,
            2,
            5,
            4
          ],
          [
            2,
            0,
            3,
            5
          ]
        ]
      },
      {
        "id": "dien_tich_day_ABC",
        "label": "Diện tích ABC",
        "notation": "S(ABC)",
        "reference": "S(ABC)",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": "measure.area",
        "depends": [
          "day_ABC"
        ],
        "parent": null,
        "display_group": [
          "construction",
          "measurement"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {
          "instruction": "measure.area"
        },
        "value": "6",
        "exact": {
          "kind": "rational",
          "value": "6"
        }
      },
      {
        "id": "the_tich_solid_ABCDEF",
        "label": "Thể tích «Khối đa diện dựng từ A, B, C, D, E, F»",
        "notation": null,
        "reference": "Thể tích khối",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": "measure.volume",
        "depends": [
          "solid_ABCDEF"
        ],
        "parent": null,
        "display_group": [
          "construction",
          "measurement"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {
          "instruction": "measure.volume"
        },
        "value": "30",
        "exact": {
          "kind": "rational",
          "value": "30"
        }
      },
      {
        "id": "the_tich_lang_tru",
        "label": "Đại lượng đo",
        "notation": null,
        "reference": "đại lượng",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": null,
        "depends": [
          "the_tich_solid_ABCDEF"
        ],
        "parent": null,
        "display_group": [
          "construction",
          "measurement",
          "target"
        ],
        "visual_transform": {
          "translate": [
            0,
            0,
            0
          ],
          "scale": 1
        },
        "source": {},
        "value": "30",
        "exact": {
          "kind": "rational",
          "value": "30"
        }
      }
    ],
    "events": [
      {
        "step_index": 0,
        "action": "INIT",
        "object": null,
        "depends": [],
        "explanation": "Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ."
      },
      {
        "step_index": 1,
        "action": "STEP",
        "object": "day_ABC",
        "depends": [
          "A",
          "B",
          "C"
        ],
        "explanation": "Dựng đa giác Tam giác đáy dưới qua 3 đỉnh A, B, C."
      },
      {
        "step_index": 2,
        "action": "CREATE",
        "object": "solid_ABCDEF",
        "depends": [
          "A",
          "B",
          "C",
          "D",
          "E",
          "F"
        ],
        "explanation": "Dựng khối solid_ABCDEF từ 6 đỉnh và 5 mặt."
      },
      {
        "step_index": 3,
        "action": "MEASURE",
        "object": "dien_tich_day_ABC",
        "depends": [
          "day_ABC"
        ],
        "explanation": "Gán dien_tich_day_ABC = 6."
      },
      {
        "step_index": 4,
        "action": "MEASURE",
        "object": "the_tich_solid_ABCDEF",
        "depends": [
          "solid_ABCDEF"
        ],
        "explanation": "Gán the_tich_solid_ABCDEF = 30."
      },
      {
        "step_index": 5,
        "action": "MEASURE",
        "object": "the_tich_lang_tru",
        "depends": [],
        "explanation": "Gán the_tich_lang_tru = 30."
      }
    ],
    "free_objects": [
      "A",
      "B",
      "C",
      "D",
      "E",
      "F"
    ],
    "khai": "Dữ liệu CẢNH cho renderer. Mọi số là chuỗi phân số CHÍNH XÁC; hoá float là việc của renderer, ở bước cuối trước GPU. Mặt phẳng và đường thẳng KHÔNG có biên — renderer tự quyết kích thước dựa trên `depends`."
  }
} as unknown as SimulationEnvelope & { scene3d: Scene3D };

beforeEach(() => {
  clearRegistryForTest();
  registerSemanticDomain();
  __resetHistoryForTest();
  useAppStore.getState().reset();
});

describe("PRISM_P01 UI End-to-End Integration", () => {
  const env = PRISM_ENVELOPE;
  const scene = env.scene3d;

  it("loadEnvelope tải thành công vào store mà không rơi vào unsupported", () => {
    const store = useAppStore.getState();
    store.loadEnvelope(env);
    const s = useAppStore.getState();
    expect(s.analysisError).toBeNull();
    expect(s.active).not.toBeNull();
    expect(s.active!.moduleId).toBe("generic.semantic_program");
    expect(s.unsupported).toBeNull();
  });

  it("scene3d lăng trụ đạt chuẩn hopLeScene3D", () => {
    expect(hopLeScene3D(scene)).toBe(true);
  });

  it("scene3d có đúng 6 điểm với nhãn A, B, C, D, E, F", () => {
    const points = scene.objects.filter((o) => o.type === "point3");
    expect(points).toHaveLength(6);
    const ids = points.map((p) => p.id).sort();
    expect(ids).toEqual(["A", "B", "C", "D", "E", "F"]);
    const notations = points.map((p) => p.notation || p.id).sort();
    expect(notations).toEqual(["A", "B", "C", "D", "E", "F"]);
  });

  it("scene3d có đúng 1 solid với tô-pô lăng trụ: 6 đỉnh, 5 mặt, 9 cạnh", () => {
    const solids = scene.objects.filter((o) => o.type === "solid");
    expect(solids).toHaveLength(1);
    const prism = solids[0];
    expect(prism.vertices).toHaveLength(6);
    expect(prism.faces).toHaveLength(5);

    // Tính số cạnh từ các mặt
    const edges = new Set<string>();
    for (const face of prism.faces!) {
      for (let i = 0; i < face.length; i++) {
        const u = face[i];
        const v = face[(i + 1) % face.length];
        edges.add(`${Math.min(u, v)}_${Math.max(u, v)}`);
      }
    }
    expect(edges.size).toBe(9);
  });

  it("đáp số 30 xuất hiện trong readout tại bước cuối", () => {
    const lastStep = stepCount(scene) - 1;
    expect(lastStep).toBe(5);
    const readouts = objectsAt(scene, lastStep).filter((o) => o.render === "readout");
    expect(readouts.length).toBeGreaterThanOrEqual(1);
    const target = readouts.find((r) => r.id === "the_tich_lang_tru" || r.value === "30");
    expect(target).toBeDefined();
    expect(hienSo(target!.exact, target!.value)).toBe("30");
  });

  it("cây phân rã ngữ nghĩa (semanticTree) có đủ Điểm, Cạnh, Mặt cho lăng trụ", () => {
    const day = withSubEntities(scene);
    const tree = semanticTree(day);
    const labels = new Set<string>();
    const walk = (nodes: typeof tree) => {
      for (const n of nodes) {
        labels.add(n.label);
        walk(n.children);
      }
    };
    walk(tree);
    expect(labels.has("Điểm")).toBe(true);
    expect(labels.has("Cạnh")).toBe(true);
    expect(labels.has("Mặt")).toBe(true);
  });

  it("Scene3DExplorer renderToString hoàn tất với 6 nhãn điểm A-F và 6 bước dựng", () => {
    const html = renderToString(
      <Scene3DExplorer
        scene={scene}
      />
    );
    expect(html).toContain("geo3d");
    expect(html).toContain("Bước 1/6");
    expect(html).toContain("Thành phần");
    // 6 nhãn điểm A, B, C, D, E, F trong geo3d-labels
    for (const label of ["A", "B", "C", "D", "E", "F"]) {
      expect(html).toContain(`>${label}</span>`);
    }
  });
});
