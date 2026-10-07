import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { canChup, datChinhSach, phanLoaiLoi } from "./capture-policy.mjs";

test("tối thiểu: chỉ ảnh oracle, tập duyệt và ảnh lỗi được chụp", () => {
  const run = mkdtempSync(join(tmpdir(), "cap-"));
  mkdirSync(join(run, "inputs"));
  writeFileSync(join(run, "inputs", "REVIEW_SET.json"), JSON.stringify({ items: [
    { path: "images/regular-triangular-pyramid/desktop/detail_*.png" }] }));
  datChinhSach({ mode: "toi-thieu", reviewSet: join(run, "inputs", "REVIEW_SET.json") });
  const anh = (p) => join(run, "images", p);
  assert.equal(canChup(anh("cube/desktop/neutral_final.png")), true);           // oracle crop cạnh khuất
  assert.equal(canChup(anh("cube/desktop/rotated_neutral.png")), true);
  assert.equal(canChup(anh("cube/desktop/show_all.png")), false);                // không ai đọc ⇒ không chụp
  assert.equal(canChup(anh("regular-triangular-pyramid/desktop/detail_volume.png")), true);   // tập duyệt
  assert.equal(canChup(anh("regular-triangular-pyramid/desktop/formation/formation_step_3.png")), false);
  assert.equal(canChup(anh("cube/desktop/show_all.png"), { loi: true }), true);  // trạng thái lỗi
  assert.equal(canChup(anh("cube/playback/desktop/neutral_final.png"), { oracle: false }), false);   // trùng tên, không vào bộ dựng
  datChinhSach({ mode: "day-du" });
  assert.equal(canChup(anh("cube/desktop/show_all.png")), true);
  assert.throws(() => datChinhSach({ mode: "tat-ca" }), /CAPTURE_MODE_UNKNOWN/);
  datChinhSach({ mode: "toi-thieu" });
});

test("ba lớp lỗi tách nhau: môi trường · bộ đo · phép kiểm sản phẩm", () => {
  assert.equal(phanLoaiLoi("Error: POLL_TIMEOUT:false", false), "ENVIRONMENT");
  assert.equal(phanLoaiLoi("Error: CDP_TIMEOUT: Runtime.evaluate", false), "ENVIRONMENT");
  assert.equal(phanLoaiLoi("TypeError: Cannot read properties of null", false), "HARNESS");
  assert.equal(phanLoaiLoi(null, false), "PRODUCT_ASSERTION");
  assert.equal(phanLoaiLoi(null, true), null);
});
