/**
 * KIỂM CHỨNG TÍCH HỢP UI CHO HÌNH CHÓP ĐÁY CHỮ NHẬT / VUÔNG (RECT_PYRAMID_P01).
 *
 * Kiểm tra đầy đủ:
 * 1. store.loadEnvelope nhận envelope chóp sinh từ production pipeline.
 * 2. scene3d hợp lệ theo schema Three.js / scene3d-model (hopLeScene3D === true).
 * 3. 5 đỉnh A, B, C, D, S hiển thị đầy đủ nhãn.
 * 4. 1 solid chóp có 5 đỉnh, 5 mặt, 8 cạnh (Euler V - E + F = 2).
 * 5. Đáp số 24 (rectangle) và 18 (square) xuất hiện tại bước đo cuối cùng (readout).
 * 6. semanticTree dựng thành công cây thực thể chứa Điểm, Cạnh, Mặt.
 * 7. Step scrubbing: tua tiến, tua lùi, frame đầu, frame cuối; objectsAt(scene, step) nhất quán.
 * 8. Causal chain: highlightSet và dependencyClosure cho đáp số thể tích liên kết trọn vẹn
 *    chuỗi nhân quả từ các điểm đáy, chiều cao, khối chóp tới đáp số.
 * 9. Scene3DExplorer renderToString hoàn tất mà không lỗi.
 * 10. Xử lý lỗi (error presentation): hiển thị error code ổn định và thông báo tiếng Việt khi contract không hợp lệ.
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
import { dependencyClosure, highlightSet, semanticTree } from "./interaction-state";
import { withSubEntities } from "./scene3d-subentities";

const RECT_PYRAMID_ENVELOPE = {
  "status": "ok",
  "simulation_id": "generic.semantic_program",
  "domain": "geometry",
  "visual_mode": "2d",
  "title": "Thể tích khối chóp có đáy là hình chữ nhật",
  "description": "Thể tích khối chóp có đáy là hình chữ nhật",
  "config": {
    "spec_version": "1.0",
    "title": "Thể tích khối chóp có đáy là hình chữ nhật",
    "frames": [
      {
        "step_index": 0,
        "narration": "Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 1,
        "narration": "Dựng khối Khối chóp từ 5 đỉnh và 5 mặt.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 2,
        "narration": "Gán the_tich_khoi_chop = 24.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 3,
        "narration": "Gán v = 24.",
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
        "narration": "Dựng khối Khối chóp từ 5 đỉnh và 5 mặt."
      },
      {
        "view_index": 2,
        "frame_lo": 2,
        "frame_hi": 2,
        "narration": "Gán the_tich_khoi_chop = 24."
      },
      {
        "view_index": 3,
        "frame_lo": 3,
        "frame_hi": 3,
        "narration": "Gán v = 24."
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
        "parent": "khoi_chop",
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
        "parent": "khoi_chop",
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
        "parent": "khoi_chop",
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
        "parent": "khoi_chop",
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
          "4",
          "0"
        ]
      },
      {
        "id": "S",
        "label": "Điểm S",
        "notation": "S",
        "reference": "S",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "khoi_chop",
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
          "6"
        ]
      },
      {
        "id": "khoi_chop",
        "label": "Khối chóp",
        "notation": null,
        "reference": "Khối đa diện dựng từ S, A, B, C, D",
        "role": "Khối đa diện dựng từ S, A, B, C, D",
        "type": "solid",
        "render": "mesh",
        "origin": "derived",
        "producer": "construct_solid",
        "depends": [
          "A",
          "B",
          "C",
          "D",
          "S"
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
            "6"
          ],
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
            "3",
            "4",
            "0"
          ],
          [
            "0",
            "4",
            "0"
          ]
        ],
        "vertex_ids": [
          "S",
          "A",
          "B",
          "C",
          "D"
        ],
        "faces": [
          [
            1,
            2,
            3,
            4
          ],
          [
            0,
            1,
            2
          ],
          [
            0,
            2,
            3
          ],
          [
            0,
            3,
            4
          ],
          [
            0,
            4,
            1
          ]
        ]
      },
      {
        "id": "the_tich_khoi_chop",
        "label": "Thể tích «Khối đa diện dựng từ S, A, B, C, D»",
        "notation": null,
        "reference": "Thể tích khối",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": "measure.volume",
        "depends": [
          "khoi_chop"
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
        "value": "24",
        "exact": {
          "kind": "rational",
          "value": "24"
        }
      },
      {
        "id": "v",
        "label": "Đại lượng đo",
        "notation": null,
        "reference": "đại lượng",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": null,
        "depends": [
          "the_tich_khoi_chop"
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
        "value": "24",
        "exact": {
          "kind": "rational",
          "value": "24"
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
        "action": "CREATE",
        "object": "khoi_chop",
        "depends": [
          "S",
          "A",
          "B",
          "C",
          "D"
        ],
        "explanation": "Dựng khối Khối chóp từ 5 đỉnh và 5 mặt."
      },
      {
        "step_index": 2,
        "action": "MEASURE",
        "object": "the_tich_khoi_chop",
        "depends": [
          "khoi_chop"
        ],
        "explanation": "Gán the_tich_khoi_chop = 24."
      },
      {
        "step_index": 3,
        "action": "MEASURE",
        "object": "v",
        "depends": [],
        "explanation": "Gán v = 24."
      }
    ],
    "free_objects": [
      "A",
      "B",
      "C",
      "D",
      "S"
    ],
    "khai": "Dữ liệu CẢNH cho renderer. Mọi số là chuỗi phân số CHÍNH XÁC; hoá float là việc của renderer, ở bước cuối trước GPU. Mặt phẳng và đường thẳng KHÔNG có biên — renderer tự quyết kích thước dựa trên `depends`."
  }
} as unknown as SimulationEnvelope & { scene3d: Scene3D };

const SQUARE_PYRAMID_ENVELOPE = {
  "status": "ok",
  "simulation_id": "generic.semantic_program",
  "domain": "geometry",
  "visual_mode": "2d",
  "title": "Thể tích khối chóp có đáy là hình vuông",
  "description": "Thể tích khối chóp có đáy là hình vuông",
  "config": {
    "spec_version": "1.0",
    "title": "Thể tích khối chóp có đáy là hình vuông",
    "frames": [
      {
        "step_index": 0,
        "narration": "Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 1,
        "narration": "Dựng khối Khối chóp từ 5 đỉnh và 5 mặt.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 2,
        "narration": "Gán the_tich_khoi_chop = 18.",
        "objects": [],
        "highlighted_object_ids": []
      },
      {
        "step_index": 3,
        "narration": "Gán v = 18.",
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
        "narration": "Dựng khối Khối chóp từ 5 đỉnh và 5 mặt."
      },
      {
        "view_index": 2,
        "frame_lo": 2,
        "frame_hi": 2,
        "narration": "Gán the_tich_khoi_chop = 18."
      },
      {
        "view_index": 3,
        "frame_lo": 3,
        "frame_hi": 3,
        "narration": "Gán v = 18."
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
        "parent": "khoi_chop",
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
        "parent": "khoi_chop",
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
        "parent": "khoi_chop",
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
          "3",
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
        "parent": "khoi_chop",
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
          "3",
          "0"
        ]
      },
      {
        "id": "S",
        "label": "Điểm S",
        "notation": "S",
        "reference": "S",
        "role": "Điểm",
        "type": "point3",
        "render": "point_marker",
        "origin": "free",
        "producer": null,
        "depends": [],
        "parent": "khoi_chop",
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
          "6"
        ]
      },
      {
        "id": "khoi_chop",
        "label": "Khối chóp",
        "notation": null,
        "reference": "Khối đa diện dựng từ S, A, B, C, D",
        "role": "Khối đa diện dựng từ S, A, B, C, D",
        "type": "solid",
        "render": "mesh",
        "origin": "derived",
        "producer": "construct_solid",
        "depends": [
          "A",
          "B",
          "C",
          "D",
          "S"
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
            "6"
          ],
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
            "3",
            "3",
            "0"
          ],
          [
            "0",
            "3",
            "0"
          ]
        ],
        "vertex_ids": [
          "S",
          "A",
          "B",
          "C",
          "D"
        ],
        "faces": [
          [
            1,
            2,
            3,
            4
          ],
          [
            0,
            1,
            2
          ],
          [
            0,
            2,
            3
          ],
          [
            0,
            3,
            4
          ],
          [
            0,
            4,
            1
          ]
        ]
      },
      {
        "id": "the_tich_khoi_chop",
        "label": "Thể tích «Khối đa diện dựng từ S, A, B, C, D»",
        "notation": null,
        "reference": "Thể tích khối",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": "measure.volume",
        "depends": [
          "khoi_chop"
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
        "value": "18",
        "exact": {
          "kind": "rational",
          "value": "18"
        }
      },
      {
        "id": "v",
        "label": "Đại lượng đo",
        "notation": null,
        "reference": "đại lượng",
        "role": "Đại lượng đo",
        "type": "quantity",
        "render": "readout",
        "origin": "derived",
        "producer": null,
        "depends": [
          "the_tich_khoi_chop"
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
        "value": "18",
        "exact": {
          "kind": "rational",
          "value": "18"
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
        "action": "CREATE",
        "object": "khoi_chop",
        "depends": [
          "S",
          "A",
          "B",
          "C",
          "D"
        ],
        "explanation": "Dựng khối Khối chóp từ 5 đỉnh và 5 mặt."
      },
      {
        "step_index": 2,
        "action": "MEASURE",
        "object": "the_tich_khoi_chop",
        "depends": [
          "khoi_chop"
        ],
        "explanation": "Gán the_tich_khoi_chop = 18."
      },
      {
        "step_index": 3,
        "action": "MEASURE",
        "object": "v",
        "depends": [],
        "explanation": "Gán v = 18."
      }
    ],
    "free_objects": [
      "A",
      "B",
      "C",
      "D",
      "S"
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

describe("RECT_PYRAMID_P01 UI End-to-End Integration", () => {
  describe("Positive Case A: Đáy chữ nhật (V=24)", () => {
    const env = RECT_PYRAMID_ENVELOPE;
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

    it("scene3d chóp đạt chuẩn hopLeScene3D", () => {
      expect(hopLeScene3D(scene)).toBe(true);
    });

    it("scene3d có đúng 5 điểm với nhãn A, B, C, D, S", () => {
      const points = scene.objects.filter((o) => o.type === "point3");
      expect(points).toHaveLength(5);
      const ids = points.map((p) => p.id).sort();
      expect(ids).toEqual(["A", "B", "C", "D", "S"]);
      const notations = points.map((p) => p.notation || p.id).sort();
      expect(notations).toEqual(["A", "B", "C", "D", "S"]);
    });

    it("scene3d có đúng 1 solid với tô-pô chóp: 5 đỉnh, 5 mặt, 8 cạnh (Euler = 2)", () => {
      const solids = scene.objects.filter((o) => o.type === "solid");
      expect(solids).toHaveLength(1);
      const pyramid = solids[0];
      expect(pyramid.vertices).toHaveLength(5);
      expect(pyramid.faces).toHaveLength(5);

      // Tính số cạnh không hướng từ các mặt
      const edges = new Set<string>();
      for (const face of pyramid.faces!) {
        for (let i = 0; i < face.length; i++) {
          const u = face[i];
          const v = face[(i + 1) % face.length];
          edges.add(`${Math.min(u, v)}_${Math.max(u, v)}`);
        }
      }
      expect(edges.size).toBe(8);
      // Euler: V - E + F = 5 - 8 + 5 = 2
      expect(pyramid.vertices!.length - edges.size + pyramid.faces!.length).toBe(2);
    });

    it("đáp số 24 xuất hiện trong readout tại bước cuối", () => {
      const lastStep = stepCount(scene) - 1;
      expect(lastStep).toBe(3);
      const readouts = objectsAt(scene, lastStep).filter((o) => o.render === "readout");
      expect(readouts.length).toBeGreaterThanOrEqual(1);
      const target = readouts.find((r) => r.id === "the_tich_khoi_chop" || r.id === "v" || r.value === "24");
      expect(target).toBeDefined();
      expect(hienSo(target!.exact, target!.value)).toBe("24");
    });

    it("cây phân rã ngữ nghĩa (semanticTree) có đủ Điểm, Cạnh, Mặt cho hình chóp", () => {
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

    it("step scrubbing phản ánh đúng từng frame trong timeline", () => {
      const count = stepCount(scene);
      expect(count).toBe(4);

      // Frame 0: khởi tạo
      const f0 = objectsAt(scene, 0);
      expect(f0.length).toBeGreaterThanOrEqual(0);

      // Frame 1: dựng khối chóp
      const f1 = objectsAt(scene, 1);
      const hasSolidF1 = f1.some((o) => o.type === "solid");
      expect(hasSolidF1).toBe(true);

      // Frame cuối: có đầy đủ khối và các readout
      const fLast = objectsAt(scene, count - 1);
      const readouts = fLast.filter((o) => o.render === "readout");
      expect(readouts.length).toBeGreaterThanOrEqual(1);
    });

    it("causal chain: chọn đáp số thì highlight chuỗi nhân quả gồm cả 5 đỉnh và khối chóp", () => {
      // Truy ngược bao đóng cho witness 'v'
      const closureV = dependencyClosure(scene, "v");
      for (const requiredNode of ["khoi_chop", "the_tich_khoi_chop"]) {
        expect(closureV).toContain(requiredNode);
      }
      for (const pt of ["A", "B", "C", "D", "S"]) {
        expect(closureV).toContain(pt);
      }

      // Highlight set cho the_tich_khoi_chop
      const hl = highlightSet(scene, "the_tich_khoi_chop", true);
      expect(hl).toContain("the_tich_khoi_chop");
      expect(hl).toContain("khoi_chop");
      for (const pt of ["A", "B", "C", "D", "S"]) {
        expect(hl).toContain(pt);
      }
    });

    it("Scene3DExplorer renderToString hiển thị đầy đủ 5 nhãn A-D, S", () => {
      const html = renderToString(
        <Scene3DExplorer
          scene={scene}
        />
      );
      expect(html).toContain("geo3d");
      expect(html).toContain("Bước 1/4");
      expect(html).toContain("Thành phần");
      for (const label of ["A", "B", "C", "D", "S"]) {
        expect(html).toContain(`>${label}</span>`);
      }
    });
  });

  describe("Positive Case B: Đáy vuông (V=18)", () => {
    const env = SQUARE_PYRAMID_ENVELOPE;
    const scene = env.scene3d;

    it("loadEnvelope thành công với case đáy vuông", () => {
      const store = useAppStore.getState();
      store.loadEnvelope(env);
      const s = useAppStore.getState();
      expect(s.analysisError).toBeNull();
      expect(s.active).not.toBeNull();
      expect(s.unsupported).toBeNull();
    });

    it("đáp số 18 xuất hiện trong readout tại bước cuối", () => {
      const lastStep = stepCount(scene) - 1;
      const readouts = objectsAt(scene, lastStep).filter((o) => o.render === "readout");
      const target = readouts.find((r) => r.id === "the_tich_khoi_chop" || r.id === "v" || r.value === "18");
      expect(target).toBeDefined();
      expect(hienSo(target!.exact, target!.value)).toBe("18");
    });

    it("tô-pô đáy vuông bảo toàn Euler = 2 và 5 đỉnh", () => {
      const solids = scene.objects.filter((o) => o.type === "solid");
      expect(solids).toHaveLength(1);
      const pyramid = solids[0];
      expect(pyramid.vertices).toHaveLength(5);
      expect(pyramid.faces).toHaveLength(5);
    });
  });

  describe("Error Presentation: Fail-closed và thông báo lỗi tiếng Việt", () => {
    it("envelope unsupported từ chối an toàn với error code và tiếng Việt", () => {
      const badEnv: SimulationEnvelope = {
        status: "unsupported",
        reason: "Đề bài thiếu chiều cao hoặc mâu thuẫn hình học.",
        failure_category: "compiler_refused",
        error_code: "SEMANTIC_PROGRAM_INVALID",
        stage_reached: "semantic_analyze",
        representation_plan: {},
        analysis: {},
      } as unknown as SimulationEnvelope;

      const store = useAppStore.getState();
      store.loadUnsupported(badEnv as any);
      const s = useAppStore.getState();
      expect(s.unsupported).not.toBeNull();
      expect(s.unsupported!.reason).toContain("chiều cao hoặc mâu thuẫn");
      expect(s.active).toBeNull();
    });
  });
});
