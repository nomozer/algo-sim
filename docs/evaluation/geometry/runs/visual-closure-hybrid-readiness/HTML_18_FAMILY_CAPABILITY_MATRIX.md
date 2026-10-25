# HTML 18-family capability matrix

Reference SHA-256 `279216192b09d6e12c8b8d444dcb0bf943419e6c52078fe04107684f0d9e8af1`, 207567 bytes; all 18 catalog entries inspected. A byte-identical reference is preserved under `reference/`; its scripts/CDNs were not executed as an oracle.

**Scope:** complete HTML configurations including their section, inscription and composite goals. A served volume subset does not certify the complete catalog entry. No provider extraction or independent holdout was run.

Legend: F=`FULL_E2E_VERIFIED`, O=`OFFLINE_GEOMETRY_VERIFIED`, R=`RENDER_ONLY`, P=`PARTIAL`, U=`UNSUPPORTED`, ?=`UNKNOWN`. Browser P means related views exist, not full-family acceptance. New O means new authored offline cases, never a blind holdout.

| # / actual HTML family | V2 facts | Source gate | Registry | Planner | Exact engine | Adapter /4 | Frontend | Browser | New problem | Overall |
|---|---|---|---|---|---|---|---|---|---|---|
| 1. Đường Thẳng – Mặt Phẳng & ĐL 3 Đường ⊥ (`quan_he_dt_mp`) | P | P | O | P | O | P | R | P | ? | PARTIAL |
| 2. Hai Đường Thẳng Chéo Nhau & Đoạn ⊥ Chung (`hai_dt_cheo_nhau`) | P | P | O | P | O | P | R | P | ? | PARTIAL |
| 3. Chóp S.ABCD có SA ⊥ (ABCD) (`chop_sa_vuong_day_vuong`) | P | O | O | O | O | O | R | P | ? | PARTIAL |
| 4. Chóp tứ giác đều S.ABCD (Nội/Ngoại tiếp) (`chop_tu_giac_deu`) | P | O | O | O | O | O | R | P | ? | PARTIAL |
| 5. Chóp tam giác đều S.ABC (Nội/Ngoại tiếp) (`chop_tam_giac_deu`) | P | O | O | O | O | O | R | P | ? | PARTIAL |
| 6. Chóp S.ABC có SA ⊥ (ABC) (`chop_sa_vuong_abc`) | P | O | O | O | O | O | R | P | ? | PARTIAL |
| 7. Tổ Hợp Chóp Đều – Nón Nội & Ngoại Tiếp (`to_hop_chop_non`) | P | U | U | U | P | U | R | ? | ? | RENDER_ONLY |
| 8. Tổ Hợp Lăng Trụ – Hình Trụ – Mặt Cầu (`to_hop_lang_tru_tru_cau`) | P | U | U | U | P | U | R | ? | ? | RENDER_ONLY |
| 9. Tổ Hợp Hình Nón – Mặt Cầu Nội & Ngoại Tiếp (`to_hop_non_cau`) | P | U | U | U | P | U | R | ? | ? | RENDER_ONLY |
| 10. Hình Chóp Cụt Tứ Giác Đều (`chop_cut_deu`) | U | U | U | U | P | U | ? | ? | ? | UNSUPPORTED |
| 11. Hình Hộp Chữ Nhật / Lập Phương (`hinh_hop_chu_nhat`) | P | O | O | O | O | O | R | P | ? | PARTIAL |
| 12. Lăng Trụ Đứng ABC.A′B′C′ (`lang_tru_tam_giac_deu`) | P | O | O | O | O | O | R | P | O | PARTIAL |
| 13. Lăng Trụ Xiên ABC.A′B′C′ (`lang_tru_xien`) | P | O | O | O | O | O | R | P | O | PARTIAL |
| 14. Mặt Cầu Giao Mặt Phẳng & Tiếp Tuyến (`mat_cau`) | P | U | U | U | O | U | R | P | ? | RENDER_ONLY |
| 15. Hình Nón, Thiết Diện & Đường Sinh (`hinh_non`) | P | U | U | U | P | U | R | P | ? | RENDER_ONLY |
| 16. Hình Trụ Tròn Xoay & Thiết Diện Song Song Trục (`hinh_tru`) | P | U | U | U | P | U | R | P | ? | RENDER_ONLY |
| 17. Hệ Tọa Độ Oxyz & Mặt Phẳng Đoạn Chắn (`he_truc_oxyz`) | P | U | U | U | P | U | R | ? | ? | UNSUPPORTED |
| 18. Tổ Hợp Oxyz: Đường Thẳng Δ, MP (P) & Mặt Cầu (`oxyz_dt_mp_cau`) | P | U | U | U | P | U | R | ? | ? | RENDER_ONLY |

Full E2E supported configurations: **0/18**. Overall classifications: **9 PARTIAL, 7 RENDER_ONLY, 2 UNSUPPORTED**. This does not mean there is no Hybrid solver: bounded pyramid/prism/polyhedral goals work offline, and seven new canonical V2 prism cases pass exact volume and /4 checks.

## Per-entry limits / evidence scope

- `quan_he_dt_mp` (HTML line 404): Named/polyhedral instances only; three-perpendicular theorem discovery and full standalone source family not certified.
- `hai_dt_cheo_nhau` (HTML line 429): Exact line relations exist on Route B/kernel; canonical V2 measurement bridge does not expose general distance/angle goals.
- `chop_sa_vuong_day_vuong` (HTML line 453): Pyramid construction/volume/sections have offline paths; requested circumsphere combination is not canonical Hybrid.
- `chop_tu_giac_deu` (HTML line 478): Regular-square-pyramid subset; inscribed/circumscribed spheres are absent from the canonical bridge.
- `chop_tam_giac_deu` (HTML line 503): Regular-triangular-pyramid subset; full incircle/circumsphere program not certified.
- `chop_sa_vuong_abc` (HTML line 527): Determined triangular bases only; no blanket arbitrary-triangle/in- or circumsphere claim.
- `to_hop_chop_non` (HTML line 551): Curved solid declaration parses; bridge rejects cone before Source Gate/Planner.
- `to_hop_lang_tru_tru_cau` (HTML line 576): Renderer can compose supplied meshes; canonical cylinder/sphere bridge is refused.
- `to_hop_non_cau` (HTML line 601): Curved primitives in legacy kernel do not establish canonical inscribed/circumscribed composite solving.
- `chop_cut_deu` (HTML line 626): Square-pyramid frustum is not the cone_frustum schema enum; no canonical frustum topology/goal contract.
- `hinh_hop_chu_nhat` (HTML line 650): Cuboid/cube metric subset served; optional sphere combination is not canonical Hybrid.
- `lang_tru_tam_giac_deu` (HTML line 674): New right-triangular-prism volume probes pass; full arbitrary-base/circumsphere catalog behavior not certified.
- `lang_tru_xien` (HTML line 698): New oblique-prism volume probes pass with one lateral vector; general perpendicular sections and arbitrary bases remain bounded.
- `mat_cau` (HTML line 722): Kernel distinguishes proper circle/tangent/no cut exactly; canonical bridge rejects sphere. Legacy screenshots are render evidence.
- `hinh_non` (HTML line 746): Legacy cone/generator/axial cuts exist; canonical bridge has no cone function or goal contracts.
- `hinh_tru` (HTML line 770): Legacy cylinder sections are bounded; arbitrary axis-parallel sections and canonical routing are not certified here.
- `he_truc_oxyz` (HTML line 794): A root frame marker is not source-grounded arbitrary point coordinates; bridge lacks general coordinate inputs/goals.
- `oxyz_dt_mp_cau` (HTML line 818): Legacy coordinates/plane/sphere rendering is not source-gated canonical Hybrid solving.

## Evidence and restrictions

`catalog-audit.json` binds all inspected source files; `capability-probe.json` records seven new prism positives, five negatives and three curved refusals. Existing B1/B2 offline corpus/browser receipts retain their historical scope. Current Visual/Adapter/browser results are in the adjacent reports.

V2 schema acceptance of sphere/cone/cylinder is independently verified, but `typed_fact_next_bridge.py` rejects them with `BRIDGE_UNSUPPORTED_CURVED` before canonical Registry/planning. Kernel and legacy renderer capabilities therefore cannot be promoted to Hybrid support. General canonical V2 distance/angle targets are also not bridged despite Route B planner/kernel functions.

No complete HTML configuration or NL-extraction quality is upgraded from its name, a plausible picture, an authored fixture, or an old model run. Locked independent holdout was not used for development.
