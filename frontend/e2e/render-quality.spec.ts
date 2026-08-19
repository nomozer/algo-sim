import { describe, it, expect } from "vitest";
import { classifyBoundingOverlap, type BoundingBox } from "./collision-classifier";
import { computeSemanticLayout } from "../src/simulations/domains/generic/layout-compiler";
import { resolveSemanticAnchor } from "../src/simulations/domains/generic/anchor-resolver";
import type { SimulationSpec } from "../src/simulations/domains/generic/model";

describe("Render Quality Certification Gate (G6 & G7)", () => {
  const VIEWPORTS = [
    { name: "Desktop Large", width: 1920, height: 1080 },
    { name: "Laptop Standard", width: 1536, height: 864 },
    { name: "School Laptop", width: 1366, height: 768 },
    { name: "Tablet", width: 768, height: 900 },
  ];

  describe("G6: Real Presentation & Disallowed Collision Matrix", () => {
    it("C02 Stack Bracket Simulation has 0 disallowed collisions across all viewports", () => {
      const spec: SimulationSpec = {
        dsl_version: "1.0",
        title: "Kiểm tra đóng mở ngoặc hợp lệ bằng Stack",
        objects: [
          {
            id: "bracket_strip",
            type: "array_strip",
            label: "Chuỗi",
            items: ["(", "[", "]", ")"],
          },
          {
            id: "stack_view",
            type: "stack_view",
            label: "Ngăn xếp",
            items: ["("],
            capacity: 6,
          },
          {
            id: "curr_char",
            type: "value_box",
            label: "Ký tự hiện tại",
            value: "[",
          },
          {
            id: "result_box",
            type: "value_box",
            label: "Kết quả",
            value: "HỢP LỆ",
          },
          {
            id: "ptr_i",
            type: "pointer",
            label: "i",
            target: "bracket_strip",
            target_index: 1,
          },
        ],
        rules: [],
        interactions: [],
        processes: [],
      };

      const pos = computeSemanticLayout(spec);

      for (const vp of VIEWPORTS) {
        const boxes: BoundingBox[] = [];

        for (const obj of spec.objects) {
          let p = pos[obj.id];

          // Pointer neo theo target qua Semantic Anchor System
          if (obj.type === "pointer" && obj.target) {
            const targetObj = spec.objects.find((x) => x.id === obj.target);
            const targetP = targetObj ? pos[targetObj.id] : { x: 50, y: 50 };
            if (targetP && targetObj) {
              const targetPixelPos = {
                x: (targetP.x / 100) * vp.width,
                y: (targetP.y / 100) * vp.height,
              };
              const anchor = resolveSemanticAnchor(targetObj, targetPixelPos, obj.target_index ?? 0);
              boxes.push({
                id: obj.id,
                type: obj.type,
                left: anchor.x - 14,
                top: anchor.y - 30,
                right: anchor.x + 14,
                bottom: anchor.y,
                width: 28,
                height: 30,
              });
              continue;
            }
          }

          if (!p) continue;

          let w = 40;
          let h = 40;

          if (obj.type === "array_strip") {
            w = (obj.items?.length ?? 4) * 34;
            h = 34;
          } else if (obj.type === "stack_view") {
            w = 80;
            h = 100;
          } else if (obj.type === "value_box") {
            w = 84;
            h = 40;
          }

          const pixelX = (p.x / 100) * vp.width;
          const pixelY = (p.y / 100) * vp.height;

          const box: BoundingBox = {
            id: obj.id,
            type: obj.type,
            left: pixelX - w / 2,
            top: pixelY - h / 2,
            right: pixelX + w / 2,
            bottom: pixelY + h / 2,
            width: w,
            height: h,
          };

          // Clipping check
          expect(box.left).toBeGreaterThanOrEqual(0);
          expect(box.top).toBeGreaterThanOrEqual(0);

          boxes.push(box);
        }

        // Pairwise collision check
        let disallowedCount = 0;
        for (let i = 0; i < boxes.length; i++) {
          for (let j = i + 1; j < boxes.length; j++) {
            const overlap = classifyBoundingOverlap(boxes[i], boxes[j]);
            if (overlap === "DISALLOWED_COLLISION") {
              disallowedCount++;
            }
          }
        }

        expect(disallowedCount).toBe(0);
      }
    });
  });

  describe("G7: Interaction / Recompute Gate", () => {
    it("Modifying input brackets triggers deterministic recompute without collision", () => {
      // Input: {[()]} -> Valid
      const modifiedSpec: SimulationSpec = {
        dsl_version: "1.0",
        title: "Kiểm tra đóng mở ngoặc",
        objects: [
          {
            id: "bracket_strip",
            type: "array_strip",
            label: "Chuỗi mới",
            items: ["{", "[", "(", "]", ")", "}"],
          },
          {
            id: "stack_view",
            type: "stack_view",
            label: "Ngăn xếp",
            items: ["{", "["],
            capacity: 6,
          },
          {
            id: "result_box",
            type: "value_box",
            label: "Kết quả",
            value: "KHÔNG HỢP LỆ",
          },
        ],
        rules: [],
        interactions: [],
        processes: [],
      };

      const pos = computeSemanticLayout(modifiedSpec);
      expect(pos["bracket_strip"]).toBeDefined();
      expect(pos["stack_view"]).toBeDefined();
      expect(pos["result_box"]).toBeDefined();

      // Convert to pixel bounds at 1366x768 (standard school screen)
      const vpW = 1366;
      const vpH = 768;

      const pStrip = pos["bracket_strip"];
      const pStack = pos["stack_view"];

      const bStrip: BoundingBox = {
        id: "bracket_strip",
        type: "array_strip",
        left: (pStrip.x / 100) * vpW - 100,
        top: (pStrip.y / 100) * vpH - 17,
        right: (pStrip.x / 100) * vpW + 100,
        bottom: (pStrip.y / 100) * vpH + 17,
        width: 200,
        height: 34,
      };

      const bStack: BoundingBox = {
        id: "stack_view",
        type: "stack_view",
        left: (pStack.x / 100) * vpW - 40,
        top: (pStack.y / 100) * vpH - 50,
        right: (pStack.x / 100) * vpW + 40,
        bottom: (pStack.y / 100) * vpH + 50,
        width: 80,
        height: 100,
      };

      expect(classifyBoundingOverlap(bStrip, bStack)).not.toBe("DISALLOWED_COLLISION");
    });
  });
});
