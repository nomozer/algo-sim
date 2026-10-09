/**
 * browser-runner.node-test.mjs — vòng đời thư mục phiên Chrome (browser-temp-lifecycle), KHÔNG mở Chrome.
 * Phán quyết orphan là hàm thuần; `donOrphan` chạy trên một gốc giả trong thư mục tạm của test.
 * Kiểm có Chrome thật (tuần tự, song song, lỗi khởi động, lỗi trong phiên): run `browser-temp-lifecycle`.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { CHU_SO_HUU, conSong, donOrphan, laOrphan, ungVienGoc } from "./browser-runner.mjs";

/** pid chắc chắn đã chết: một tiến trình con vừa thoát. */
const pidChet = () => spawnSync(process.execPath, ["-e", ""]).pid;

test("laOrphan: thiếu/sai chứng nhận hoặc chủ sở hữu còn sống ⇒ GIU", () => {
  const song = { runnerSong: () => true, chromeDungThuMuc: () => false };
  const chet = { runnerSong: () => false, chromeDungThuMuc: () => false };
  assert.equal(laOrphan(null, chet), "GIU");
  assert.equal(laOrphan({ owner: "khác", runner_pid: 1 }, chet), "GIU");
  assert.equal(laOrphan({ owner: CHU_SO_HUU }, chet), "GIU");
  assert.equal(laOrphan({ owner: CHU_SO_HUU, runner_pid: 7, chrome_pid: 9 }, song), "GIU");
});

test("laOrphan: chủ sở hữu chết ⇒ DON; Chrome của phiên còn chạy ⇒ DIET_ROI_DON", () => {
  const o = { owner: CHU_SO_HUU, runner_pid: 7, chrome_pid: 9 };
  assert.equal(laOrphan(o, { runnerSong: () => false, chromeDungThuMuc: () => false }), "DON");
  assert.equal(laOrphan(o, { runnerSong: () => false, chromeDungThuMuc: () => true }), "DIET_ROI_DON");
  assert.equal(laOrphan({ ...o, chrome_pid: null }, { runnerSong: () => false, chromeDungThuMuc: () => true }), "DON");
});

test("ungVienGoc: biến môi trường trước, D: trên Windows, rồi thư mục tạm của hệ", () => {
  assert.deepEqual(ungVienGoc({ ALGOSIM_BROWSER_TMP: "X:/r" }, "win32"),
    ["X:/r", "D:/tmp/algosim-browser", join(tmpdir(), "algosim-browser")]);
  assert.deepEqual(ungVienGoc({}, "linux"), [join(tmpdir(), "algosim-browser")]);
});

test("conSong: tiến trình này sống, tiến trình đã thoát thì không", () => {
  assert.equal(conSong(process.pid), true);
  assert.equal(conSong(pidChet()), false);
  assert.equal(conSong(null), false);
});

test("donOrphan: chỉ xoá thư mục có chứng nhận và chủ sở hữu đã chết; không đụng phiên sống, thư mục lạ", () => {
  const goc = mkdtempSync(join(tmpdir(), "brt-"));
  try {
    const tao = (ten, owner) => {
      const d = join(goc, ten);
      mkdirSync(join(d, "profile"), { recursive: true });
      if (owner) writeFileSync(join(d, "owner.json"), JSON.stringify(owner));
      return d;
    };
    const mo = tao("w12-orphan", { owner: CHU_SO_HUU, runner_pid: pidChet(), chrome_pid: null });
    const song = tao("w12-live", { owner: CHU_SO_HUU, runner_pid: process.pid, chrome_pid: null });
    const khongChu = tao("w12-noowner", null);
    const la = tao("w12-foreign", { owner: "người khác", runner_pid: pidChet() });
    const khac = tao("scoped_dir123_456", { owner: CHU_SO_HUU, runner_pid: pidChet() });
    assert.deepEqual(donOrphan(goc), { don: 1, giu: 3, loi: 0 });
    assert.equal(existsSync(mo), false);
    for (const d of [song, khongChu, la, khac]) assert.equal(existsSync(d), true, d);
  } finally {
    rmSync(goc, { recursive: true, force: true });
  }
});
