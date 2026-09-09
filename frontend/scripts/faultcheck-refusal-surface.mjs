/**
 * faultcheck-refusal-surface.mjs — CỔNG VỪA SỬA CÓ CÒN RĂNG KHÔNG.
 *
 * Một cổng vừa đi từ `17–19/21` chập chờn lên `21/21` mười lượt liền là tin
 * tốt — hoặc là dấu hiệu nó đã ngừng kiểm. Phân biệt được bằng đúng một cách:
 * **phá sản phẩm và đòi nó đỏ** (`ARCHITECTURE_MAP §8` #14).
 *
 * Bốn phép tiêm, mỗi phép nhắm một khẳng định khác nhau:
 *
 *   1  bỏ nhãn thẻ từ chối            → `· nhãn` phải đỏ
 *   2  in thẳng `error_code` lên thẻ  → `· KHÔNG lộ mã kỹ thuật` phải đỏ
 *   3  dựng khung 3D dưới lời từ chối → `· KHÔNG dựng cảnh` phải đỏ
 *   4  trỏ vào cổng chết             → phải là `PAGE_NOT_LOADED` (exit 2),
 *                                       **không** phải một artifact `17/21`
 *
 * Phép thứ tư là phép quan trọng nhất của wave này: nó khoá đúng cái tật cũ —
 * báo lỗi NỘI DUNG cho một sự cố HẠ TẦNG.
 *
 * Tiêm vào `src/`, **dựng lại**, chạy cổng, rồi phục hồi NGUYÊN BYTE và dựng
 * lại lần nữa. Băm được đối chiếu sau mỗi lượt.
 */
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FE = fileURLToPath(new URL("..", import.meta.url));
const GOC = resolve(FE, "..");
const OUT = join(GOC, "docs", "evaluation", "geometry", "final-system-release");
mkdirSync(OUT, { recursive: true });

const WORKSPACE = join(FE, "src", "components", "SimulationWorkspace.tsx");
const bam = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");

const dung = () => spawnSync("npm", ["run", "build"],
  { cwd: FE, shell: true, encoding: "utf8" }).status === 0;

function chayCong(base) {
  const r = spawnSync("node",
    ["scripts/certify-refusal-surface.mjs", ...(base ? ["--base", base] : [])],
    { cwd: FE, shell: true, encoding: "utf8" });
  const out = `${r.stdout ?? ""}${r.stderr ?? ""}`;
  const m = out.match(/ĐẠT (\d+)\/(\d+)/);
  return {
    exit: r.status,
    dat: m ? Number(m[1]) : null,
    tong: m ? Number(m[2]) : null,
    page_not_loaded: /PAGE_NOT_LOADED/.test(out),
    do: [...out.matchAll(/^✗ (.+?) \|/gm)].map((x) => x[1]),
  };
}

/** Thay `cu` → `moi` trong tệp, dựng lại, chạy cổng, phục hồi nguyên byte. */
function tiem(ten, tep, cu, moi, nhamToi) {
  const goc = readFileSync(tep);
  const truoc = createHash("sha256").update(goc).digest("hex");
  let src = goc.toString("utf8");
  // Kho có cả tệp LF lẫn CRLF; "khớp 0 lần" trông y hệt "mẫu viết sai".
  if (src.split(cu).length - 1 !== 1 && cu.includes("\n")) {
    const crlf = cu.replace(/\n/g, "\r\n");
    if (src.split(crlf).length - 1 === 1) { cu = crlf; moi = moi.replace(/\n/g, "\r\n"); }
  }
  if (src.split(cu).length - 1 !== 1) {
    throw new Error(`${ten}: mẫu tiêm khớp ${src.split(cu).length - 1} lần`);
  }
  let kq; let dungDuoc = true;
  try {
    writeFileSync(tep, src.replace(cu, moi), "utf8");
    dungDuoc = dung();
    kq = dungDuoc ? chayCong() : { exit: -1 };
  } finally {
    writeFileSync(tep, goc);
    dung();
  }
  if (bam(tep) !== truoc) throw new Error(`${ten}: KHÔNG phục hồi nguyên byte`);

  /* ⚠️ PHÉP TIÊM KHÔNG DỰNG ĐƯỢC ≠ CỔNG KHÔNG CÓ RĂNG — và gộp hai cái là
     đúng lớp lỗi wave này đang đi sửa. Lần đầu chạy, phép tiêm số 1 thay
     `{eyebrow}` bằng `{""}`, khiến `eyebrow` thành biến không dùng và `tsc -b`
     ĐỎ; cổng chưa từng chạy, mà báo cáo ghi `NOT_DETECTED` — đọc như "cổng
     mù". Nhãn riêng để không ai kết luận nhầm về cổng. */
  if (!dungDuoc) {
    return { ten, nham_toi: nhamToi, exit: -1, dat: null, do: [],
             phat_hien: false, ket_qua: "BUILD_FAILED",
             ghi_chu: "Phép tiêm không biên dịch được — cổng CHƯA ĐƯỢC CHẠY. "
               + "Đây là lỗi của phép tiêm, không phải kết luận về cổng." };
  }
  const batDung = kq.do?.some((d) => d.includes(nhamToi)) ?? false;
  return { ten, nham_toi: nhamToi, exit: kq.exit, dat: kq.dat,
           do: kq.do ?? [], phat_hien: batDung,
           ket_qua: batDung ? "DETECTED" : "NOT_DETECTED" };
}

const ket = [];

ket.push(tiem("1_bo_nhan_the_tu_choi", WORKSPACE,
  `      <span className="eyebrow">{eyebrow}</span>`,
  `      <span className="eyebrow">{eyebrow.slice(0, 0)}</span>`,
  "· nhãn"));

ket.push(tiem("2_in_thang_ma_loi_len_the", WORKSPACE,
  `          <dd>{nhanLoai}</dd>`,
  `          <dd>{unsupported.error_code ?? nhanLoai}</dd>`,
  "KHÔNG lộ mã kỹ thuật"));

ket.push(tiem("3_dung_khung_3D_duoi_loi_tu_choi", WORKSPACE,
  `      <p className="notes">{hint}</p>`,
  `      <p className="notes">{hint}</p>\n      <canvas width={10} height={10} />`,
  "KHÔNG dựng cảnh"));

// Phép thứ tư — KHÔNG cần tiêm mã: trỏ cổng vào một cổng TCP chết.
{
  const k = chayCong("http://localhost:9");
  ket.push({ ten: "4_cong_chet_phai_la_PAGE_NOT_LOADED", nham_toi: "PAGE_NOT_LOADED",
             exit: k.exit, dat: k.dat, do: k.do,
             phat_hien: k.page_not_loaded && k.exit === 2 && k.dat === null,
             ket_qua: k.page_not_loaded && k.exit === 2 && k.dat === null
               ? "DETECTED" : "NOT_DETECTED",
             ghi_chu: "Lỗi hạ tầng phải ném PAGE_NOT_LOADED và KHÔNG ghi artifact "
               + "nghiệm thu; đây chính là tật cũ của bản trước." });
}

const tom = {
  wave: "FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE",
  cong: "certify-refusal-surface.mjs",
  FAULT_INJECTIONS: ket.length,
  DETECTED: ket.filter((k) => k.phat_hien).length,
  NOT_DETECTED: ket.filter((k) => k.ket_qua === "NOT_DETECTED").map((k) => k.ten),
  BUILD_FAILED: ket.filter((k) => k.ket_qua === "BUILD_FAILED").map((k) => k.ten),
  injections: ket,
};
writeFileSync(join(OUT, "FAULT_INJECTIONS_refusal_surface.json"),
  JSON.stringify(tom, null, 1), "utf8");
for (const k of ket) console.log(`  ${k.phat_hien ? "✓" : "✗"} ${k.ten} — ${k.ket_qua}`);
console.log(`\n${tom.DETECTED}/${tom.FAULT_INJECTIONS} phép tiêm bị bắt`);
process.exit(tom.NOT_DETECTED.length || tom.BUILD_FAILED.length ? 1 : 0);
