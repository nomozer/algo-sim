/**
 * capture-w4b2b-experiment.mjs — W4B-2B §15/§22: LUỒNG HỌC SINH THẬT của cổng
 * Thí nghiệm, chạy trong Chrome thật qua CDP.
 *
 * Vì sao cần script riêng: `diagnose-responsive.mjs` là runner ĐO hình học, nó
 * không bấm nút. Ở đây phải chứng minh một chuỗi HÀNH VI (mở cổng → cam kết sai
 * → phản hồi → cam kết đúng → đóng cổng) và chứng minh trạng thái canonical
 * KHÔNG đổi qua các lần bật/tắt trình bày. Hạ tầng CDP dùng lại khuôn của
 * `capture-w2c-program.mjs` (repo chưa có module CDP dùng chung — nợ có sẵn,
 * không refactor 7 script giữa wave này).
 *
 * KHÔNG sửa mã sản phẩm để chụp được. Mọi thao tác đi qua đúng DOM mà học sinh
 * thấy; mọi phán quyết đọc từ store thật.
 *
 * Chạy:  npm run dev  (cửa sổ khác, nguồn ĐỨNG YÊN trong lúc đo)
 *        node scripts/capture-w4b2b-experiment.mjs [--port 3000] [--out <dir>]
 */

import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const args = process.argv.slice(2);
const argOf = (n, d) => (args.includes(n) ? args[args.indexOf(n) + 1] : d);
const PORT = argOf("--port", "3000");
const APP = `http://localhost:${PORT}`;
const OUT = resolve(argOf("--out", "../docs/evaluation/m17/w4b2b-observe-experiment-explain/browser-flow"));
const CDP_PORT = 9000 + Math.floor(Math.random() * 900);
mkdirSync(OUT, { recursive: true });

const CHROME = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].find(existsSync);
if (!CHROME) { console.error("Không tìm thấy Chrome."); process.exit(1); }

const profile = mkdtempSync(join(tmpdir(), "algosim-w4b2b-"));
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", `--remote-debugging-port=${CDP_PORT}`,
  /* W4B-2D §32: bề rộng đo được là THAM SỐ. Trước đây cố định 1920x1080, nên
     luồng Quan sát/Thí nghiệm/Giải thích chỉ từng được chứng minh ở đúng một
     viewport — trong khi lỗi bố cục của kho này đều lộ ở bề ngang hẹp. */
  `--user-data-dir=${profile}`, `--window-size=${argOf("--window", "1920,1080")}`,
  "--hide-scrollbars", "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shutdown = () => { try { chrome.kill(); } catch { /* đã chết */ } };
process.on("SIGINT", () => { shutdown(); process.exit(130); });

async function connect() {
  for (let i = 0; i < 40; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return page.webSocketDebuggerUrl;
    } catch { /* chưa lên */ }
    await sleep(250);
  }
  throw new Error("Chrome không mở được cổng debug.");
}

const ws = new WebSocket(await connect());
await new Promise((r) => (ws.onopen = r));
let id = 0;
const pending = new Map();
ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
};
const send = (method, params = {}) => new Promise((res) => {
  const i = ++id; pending.set(i, res);
  ws.send(JSON.stringify({ id: i, method, params }));
});
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", {
    expression: expr, awaitPromise: true, returnByValue: true,
  });
  if (r.result?.exceptionDetails) {
    throw new Error(JSON.stringify(r.result.exceptionDetails.exception ?? r.result.exceptionDetails));
  }
  return r.result?.result?.value;
};

const shot = async (name) => {
  const r = await send("Page.captureScreenshot", { format: "png" });
  writeFileSync(join(OUT, `${name}.png`), Buffer.from(r.result.data, "base64"));
};

/* ── ĐỌC TRẠNG THÁI THẬT TỪ STORE ────────────────────────────────────────────
 * Repo KHÔNG có tiện ích hash nào ở frontend (đã kiểm bằng grep), nên "canonical
 * hash" ở đây là chuỗi JSON tất định của chính `active.state` + cursor. Đó là
 * bằng chứng mạnh hơn một hash tự chế: nó so TOÀN BỘ state chứ không so một
 * digest do chính script này định nghĩa. */
const snapshot = () => evaluate(`(async () => {
  const s = await import('/src/state/store.ts');
  const st = s.useAppStore.getState();
  const a = st.active;
  const zone = (l) => !!document.querySelector('[aria-label="' + l + '"]');
  const btn = [...document.querySelectorAll('button')]
    .find((b) => b.textContent.includes('Thí nghiệm'));
  return {
    moduleId: a ? a.moduleId : null,
    cursor: a ? a.state.cursor : null,
    canonical: a ? JSON.stringify(a.state) : null,
    prediction: st.prediction ? { verdict: st.prediction.verdict, answerId: st.prediction.answerId } : null,
    rightOpen: st.rightOpen,
    zones: {
      scan: zone('Thao tác với biến tích luỹ'),
      sort: zone('Thao tác sắp xếp'),
      /* W4B-2D: ho tim kiem la ho thu ba di qua cong nay. Thieu dong nay thi
         moi phep kiem "vung cam ket co hien khong" doc nham ket qua cho
         linear_search/binary_search — va bao PASS. */
      search: zone('Thao tác với bước tìm kiếm'),
    },
    /* Tien de thuoc QUAN SAT (§29): no phai o lai ke ca khi cong da an vung
       cam ket. Do rieng vi day la thu W4B-2D suyt lam mat. */
    precondition: (document.querySelector('.search-precondition') || {}).textContent || null,
    /* W4B-2V: khoi TRANG THAI QUAN SAT phai co mat o CA Quan sat lan Thi nghiem.
       Ghi nguyen van de sidecar chung minh duoc tinh don dieu, khong chi bao co/khong. */
    observeState: (document.querySelector('.search-observe') || {}).textContent || null,
    observeCost: (document.querySelector('.search-cost') || {}).textContent || null,
    /* W4B-2V: quan he co HAI chu so huu hop le — dai nhan qua (quet day/sap xep)
       va khoi quan sat cua ho tim kiem. Do NGU NGHIA, khong do ten class. */
    relation: !!document.querySelector('.decision-strip')
      || !!document.querySelector('.search-observe'),
    experimentButton: btn ? btn.textContent.replace(/\\s+/g, ' ').trim() : null,
    experimentOpen: btn ? btn.getAttribute('aria-expanded') === 'true' : null,
    commitButtons: [...document.querySelectorAll('[aria-label^="Thao tác"] button')]
      .map((b) => b.textContent.replace(/\\s+/g, ' ').trim()),
    /* §10 — rò rỉ đáp án: DOM tuyệt đối không được mang các khoá này. */
    domLeak: ['correctActionId', 'expectedId', 'expectedAction', 'đáp án đúng']
      .filter((k) => document.body.innerHTML.includes(k)),
  };
})()`);

/** Bat ky vung cam ket nao dang hien — khong chep tay danh sach ho. */
const anyZone = (z) => !!(z.scan || z.sort || z.search);

/** Bấm nút theo CHỮ học sinh đọc được — không theo class/id nội bộ. */
const clickText = (text, scope = "button") => evaluate(`(() => {
  const b = [...document.querySelectorAll('${scope}')]
    .find((x) => x.textContent.replace(/\\s+/g,' ').includes(${JSON.stringify(text)}));
  if (!b) return false;
  b.click();
  return true;
})()`);

/** §14 — đi bằng BÀN PHÍM: focus rồi phát keydown Enter thật qua CDP. */
const focusText = (text) => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')]
    .find((x) => x.textContent.replace(/\\s+/g,' ').includes(${JSON.stringify(text)}));
  if (!b) return null;
  b.focus();
  return document.activeElement === b ? b.textContent.replace(/\\s+/g,' ').trim() : null;
})()`);
const pressEnter = async () => {
  /* Chuỗi ĐẦY ĐỦ: Chrome chỉ tổng hợp `click` cho <button> khi có rawKeyDown +
     char + keyUp kèm mã phím gốc. Thiếu `text`/`nativeVirtualKeyCode` thì phím
     tới DOM nhưng KHÔNG thành activation — và lượt đo sẽ đổ lỗi oan cho sản phẩm. */
  const base = { key: "Enter", code: "Enter", windowsVirtualKeyCode: 13,
                 nativeVirtualKeyCode: 13 };
  await send("Input.dispatchKeyEvent", { type: "rawKeyDown", ...base });
  await send("Input.dispatchKeyEvent", { type: "char", text: "\r", ...base });
  await send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
  await sleep(350);
};

/* NẠP BÀI BẰNG ĐÚNG THAO TÁC CỦA HỌC SINH — bấm thẻ trên Trang chủ.
 *
 * Bản đầu gọi thẳng `store.loadEnvelope` qua `import('/src/state/store.ts')`.
 * Đo được: store ĐÓ nhận `view:"workspace"` + `active` đúng, mà React vẫn vẽ
 * Trang chủ ⇒ thể hiện module tôi ghi KHÔNG phải thể hiện mà app đăng ký. Cùng
 * họ với lỗi `registerAllSimulations` đã sửa ở lượt trước: tin vào "cùng URL thì
 * cùng instance" là tin vào một giả định không được kiểm.
 *
 * Đi qua DOM thì không cần giả định nào cả — và nó còn ĐÚNG hơn với §15: học
 * sinh mở bài bằng cách bấm thẻ, không bằng cách gọi hàm. */
const CARD_OF = {
  "algorithm.find_max": "Tìm học sinh có điểm kiểm tra cao nhất",
  "algorithm.insertion_sort": "Sắp xếp các quân bài",
};
/* Loader COPY NGUYÊN khuôn `diagnose-responsive.mjs::loadCatalogEntry` — khuôn
   đó đã chạy được trong chính phiên đo này (ảnh observe-baseline/ là bằng chứng),
   nên dùng lại thay vì tự chế đường nạp thứ hai. */
const loadTarget = (simId) => evaluate(`(async () => {
  const c = await import('/src/data/offline-catalog.ts');
  const s = await import('/src/state/store.ts');
  const r = await import('/src/simulations/index.ts');
  const reg = await import('/src/simulations/registry.ts');
  if (reg.listSimulations().length === 0) r.registerAllSimulations();
  const list = c.offlineCatalog();
  const i = list.findIndex((x) => x.simId === ${JSON.stringify(simId)});
  if (i < 0) return { ok: false, why: 'khong co mau offline' };
  s.useAppStore.getState().loadEnvelope(list[i].envelope);
  const after = s.useAppStore.getState();
  return { ok: !!after.active, view: after.view };
})()`);

/** Nhảy tới bước CÓ THỂ CAM KẾT đầu tiên — dùng chính hàm production. */
const nextStepViaUi = () => evaluate(`(() => {
  const b = [...document.querySelectorAll('button')]
    .find((x) => (x.getAttribute('title') || '') === 'Tiến một bước' && !x.disabled);
  if (!b) return false;
  b.click();
  return true;
})()`);

/** Tiến từng bước BẰNG NÚT tới bước đầu tiên có công cụ cam kết + cổng Thí nghiệm. */
const gotoActionable = async () => {
  for (let i = 0; i < 40; i += 1) {
    /* W4B-2V: quan he cua ho tim kiem doi chu so huu tu .decision-strip sang
       .search-observe (khoi trang thai dung NGOAI cong). Pheo do chi biet mot
       chu so huu se bao 'khong co buoc cam ket nao' o dung nhung bai vua duoc
       sua — mot runner het han lai to cao san pham. */
    const ok = await evaluate(`(() => (!!document.querySelector('.decision-strip')
        || !!document.querySelector('.search-observe'))
      && [...document.querySelectorAll('button')].some((b) => b.textContent.includes('Thí nghiệm')))()`);
    if (ok) return i;
    if (!(await nextStepViaUi())) break;
    await sleep(280);
  }
  return -1;
};

/* CHỜ ĐIỀU KIỆN THẬT, KHÔNG NGỦ TUỲ TIỆN (bài học VIS-003 / anti-pattern #14).
 * `loadEnvelope` trả về trước khi React kịp dựng workspace; đo ngay sau một
 * `sleep` cố định thì lượt đầu của tiến trình bắt được trang Home và mọi khẳng
 * định sau đó đều sai vì lý do chẳng liên quan. Thoát != 0 kèm chẩn đoán nếu
 * sân khấu không bao giờ xuất hiện — im lặng bỏ qua là cách guard chết. */
const waitForStage = async (simId) => {
  for (let i = 0; i < 40; i += 1) {
    const st = await evaluate(`(() => ({
      stage: !!document.querySelector('.sim-stage'),
      title: (document.querySelector('.workspace-title') || {}).textContent || null,
    }))()`);
    if (st?.stage) return st;
    await sleep(250);
  }
  const diag = await evaluate(`(async () => {
    const s = await import('/src/state/store.ts');
    const g = s.useAppStore.getState();
    return { view: g.view, active: g.active ? g.active.moduleId : null,
             analysisError: g.analysisError,
             bodyStart: document.body.innerText.slice(0, 160) };
  })()`);
  throw new Error(`${simId}: sân khấu không dựng được — ${JSON.stringify(diag)}`);
};

const findings = [];
const check = (name, ok, detail) => {
  findings.push({ check: name, verdict: ok ? "PASS" : "FAIL", detail });
  console.log(`  ${ok ? "✓" : "✗"} ${name}${ok ? "" : " — " + JSON.stringify(detail)}`);
};

const report = { app: APP, generated_at: new Date().toISOString(), targets: {} };

try {
  await send("Page.enable");
  await send("Runtime.enable");

  const TARGETS = (argOf("--targets", "algorithm.find_max,algorithm.insertion_sort")).split(",");
  for (const simId of TARGETS) {
    const short = simId.split(".")[1];
    console.log(`\n── ${simId}`);
    await send("Page.navigate", { url: APP });
    await sleep(1600);

    /* `Runtime.evaluate` ngay sau `Page.navigate` thỉnh thoảng trả `undefined`
       cho giá trị trả về (chính `diagnose-responsive.mjs` cũng in cảnh báo đó).
       Giá trị trả về vì thế KHÔNG phải bằng chứng; bằng chứng là DOM. Gọi lại
       vài lượt rồi để `waitForStage` phán — nó đọc trang thật và thoát != 0 kèm
       chẩn đoán nếu sân khấu không bao giờ dựng. */
    for (let tryLoad = 0; tryLoad < 3; tryLoad += 1) {
      const loaded = await loadTarget(simId);
      if (loaded?.ok) break;
      await sleep(500);
    }
    await waitForStage(simId);

    const step = await gotoActionable();
    if (step < 0) throw new Error(`${simId}: không có bước cam kết nào`);
    await waitForStage(simId);
    await sleep(300);

    /* 1 — QUAN SÁT: không vùng cam kết, có cổng, có quan hệ */
    const observe = await snapshot();
    await shot(`${short}-1-observe`);
    check(`${short}: Quan sát KHÔNG có vùng cam kết`,
      !anyZone(observe.zones), observe.zones);
    check(`${short}: cổng Thí nghiệm nhìn thấy được`, !!observe.experimentButton,
      observe.experimentButton);
    check(`${short}: Quan sát không rò đáp án`, observe.domLeak.length === 0, observe.domLeak);
    /* §29 — cong khong duoc lay mat du kien QUAN SAT. */
    check(`${short}: quan hệ đang xét vẫn ở lại Quan sát`, observe.relation, observe.relation);

    /* 2 — MỞ CỔNG BẰNG BÀN PHÍM (§14) */
    const focused = await focusText("Thí nghiệm");
    check(`${short}: Tab tới được cổng`, !!focused, focused);
    await pressEnter();
    let opened = await snapshot();
    let openedBy = "keyboard";
    if (!anyZone(opened.zones)) {
      /* Không mở được bằng phím ⇒ thử chuột để BIẾT lỗi nằm ở đâu: cổng hỏng,
         hay chỉ đường bàn phím hỏng. Hai kết luận rất khác nhau, không được gộp. */
      await clickText("Thí nghiệm");
      await sleep(350);
      opened = await snapshot();
      openedBy = anyZone(opened.zones) ? "mouse-only" : "none";
    }
    await shot(`${short}-2-experiment-open`);
    const zoneOn = anyZone(opened.zones);
    check(`${short}: mở cổng BẰNG BÀN PHÍM (Enter)`, openedBy === "keyboard",
      { openedBy, zones: opened.zones });
    check(`${short}: mở cổng ⇒ vùng cam kết hiện ra`, zoneOn, { openedBy, zones: opened.zones });
    check(`${short}: có nút cam kết`, opened.commitButtons.length >= 2, opened.commitButtons);
    check(`${short}: mở cổng KHÔNG đổi canonical state`,
      opened.canonical === observe.canonical && opened.cursor === observe.cursor,
      { cursor: [observe.cursor, opened.cursor] });
    check(`${short}: Thí nghiệm mở vẫn không rò đáp án`, opened.domLeak.length === 0, opened.domLeak);

    /* 3 — CAM KẾT SAI → phản hồi từ predict.check */
    /* ANH XA NHAN <- ID PHAI LAY TU CHINH MO HINH, KHONG SUY THEO VI TRI.
     *
     * Ban dau doan: `commitButtons[options.indexOf(id)]`. Dung cho hai ho cu vi
     * chung co 2 lua chon cung thu tu. VO cho `binary_search`:
     * `DecisionPoint.options` xep [left, right, found], con `SearchActionZone`
     * CO Y dung theo [right, found, left] va DAO NGHIA nhan ("option left" =
     * nua trai BI LOAI = tim tiep ben PHAI — xem chu thich DAO NGHIA trong
     * decision.ts). Lượt do dau tien vi the bam nhan cua `found` khi tuong minh
     * bam `right`, roi bao "engine cham dung thanh sai" — mot ket luan oan cho
     * san pham. Nay hoi thang mo hinh: id va label di theo cap. */
    const expected = await evaluate(`(async () => {
      const s = await import('/src/state/store.ts');
      const d = await import('/src/simulations/domains/algorithm/decision.ts');
      const st = s.useAppStore.getState().active.state;
      const dp = d.decisionPointOf(st);
      const model = d.scanInteractionOf(st) || d.searchInteractionOf(st) || d.sortInteractionOf(st);
      return {
        expectedId: dp.expectedId,
        options: dp.options.map((o) => o.id),
        actions: model ? model.actions.map((a) => ({ id: a.id, label: a.label })) : [],
      };
    })()`);
    const labelOf = (id) => (expected.actions.find((a) => a.id === id) || {}).label;
    const wrongId = expected.actions.map((a) => a.id).find((o) => o !== expected.expectedId);
    const labels = opened.commitButtons;
    const wrongLabel = labelOf(wrongId);
    if (!wrongLabel) throw new Error(`${simId}: khong anh xa duoc nhan cho id "${wrongId}"`);
    await clickText(wrongLabel, '[aria-label^="Thao tác"] button');
    await sleep(400);
    const afterWrong = await snapshot();
    await shot(`${short}-3-wrong`);
    check(`${short}: cam kết SAI được engine chấm là sai`,
      afterWrong.prediction?.verdict === "incorrect", afterWrong.prediction);
    check(`${short}: chấm sai KHÔNG đổi canonical state`,
      afterWrong.canonical === observe.canonical, { cursor: afterWrong.cursor });

    /* 4 — CAM KẾT ĐÚNG */
    await evaluate(`(async () => {
      const s = await import('/src/state/store.ts');
      s.useAppStore.getState().clearPrediction();
      return true; })()`);
    await sleep(200);
    const rightLabel = labelOf(expected.expectedId);
    if (!rightLabel) throw new Error(`${simId}: khong anh xa duoc nhan cho expectedId`);
    await clickText(rightLabel, '[aria-label^="Thao tác"] button');
    await sleep(400);
    const afterRight = await snapshot();
    await shot(`${short}-4-correct`);
    check(`${short}: cam kết ĐÚNG được engine chấm là đúng`,
      afterRight.prediction?.verdict === "correct", afterRight.prediction);

    /* 5 — GIẢI THÍCH mở/đóng trong lúc Thí nghiệm đang mở (§23) */
    await evaluate(`(async () => {
      const s = await import('/src/state/store.ts');
      s.useAppStore.getState().toggleRight(); return true; })()`);
    await sleep(400);
    const withExplain = await snapshot();
    await shot(`${short}-5-experiment-plus-explain`);
    check(`${short}: mở Giải thích KHÔNG đóng Thí nghiệm`,
      anyZone(withExplain.zones), withExplain.zones);
    check(`${short}: mở Giải thích KHÔNG đổi canonical state`,
      withExplain.canonical === observe.canonical, { cursor: withExplain.cursor });
    await evaluate(`(async () => {
      const s = await import('/src/state/store.ts');
      s.useAppStore.getState().toggleRight(); return true; })()`);
    await sleep(300);

    /* 6 — ĐÓNG CỔNG → Quan sát trở lại, không reset mô phỏng */
    await clickText("Đóng thí nghiệm");
    await sleep(400);
    const closed = await snapshot();
    await shot(`${short}-6-observe-again`);
    check(`${short}: đóng cổng ⇒ vùng cam kết biến mất`,
      !anyZone(closed.zones), closed.zones);
    check(`${short}: đóng cổng KHÔNG reset mô phỏng`,
      closed.cursor === observe.cursor && closed.canonical === observe.canonical,
      { cursor: [observe.cursor, closed.cursor] });

    /* 7 — TIMELINE vẫn chạy sau khi rời Thí nghiệm */
    await evaluate(`(async () => {
      const s = await import('/src/state/store.ts');
      s.useAppStore.getState().nextStep(); return true; })()`);
    await sleep(400);
    const advanced = await snapshot();
    check(`${short}: timeline vẫn tiến được sau khi rời Thí nghiệm`,
      advanced.cursor === observe.cursor + 1, { cursor: advanced.cursor });

    report.targets[simId] = {
      actionable_step: step,
      canonical_at_actionable: observe.canonical?.length ?? null,
      canonical_stable_across_ui_modes:
        opened.canonical === observe.canonical &&
        afterWrong.canonical === observe.canonical &&
        withExplain.canonical === observe.canonical &&
        closed.canonical === observe.canonical,
      commit_buttons: labels,
      experiment_opened_by: openedBy,
      expected_option_hidden_from_dom: observe.domLeak.length === 0 && opened.domLeak.length === 0,
      prediction_wrong: afterWrong.prediction,
      prediction_correct: afterRight.prediction,
      /* §29: tien de phai doc duoc o Quan sat, va chi noi MOT lan. */
      precondition_in_observe: observe.precondition,

    };
  }

  report.findings = findings;
  report.verdict = findings.every((f) => f.verdict === "PASS") ? "PASS" : "FAIL";
  writeFileSync(join(OUT, "experiment-flow.json"), JSON.stringify(report, null, 2) + "\n", "utf-8");
  console.log(`\n${report.verdict === "PASS" ? "✓ PASS" : "✗ FAIL"}  → ${OUT}`);
  shutdown();
  process.exit(report.verdict === "PASS" ? 0 : 1);
} catch (err) {
  writeFileSync(join(OUT, "RUN_ERROR.json"),
    JSON.stringify({ error: String(err), findings }, null, 2) + "\n", "utf-8");
  console.error(`\n✗ ${err}`);
  shutdown();
  process.exit(3);
}
