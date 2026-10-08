# CORRECTNESS.md — Audit tính đúng đắn & nguyên tắc giáo dục (M7.14C)

Tài liệu này là kết quả **Simulation Correctness Audit** (M7.14C) và là nơi ghi
các nguyên tắc ràng buộc mọi milestone sau. Khi code và tài liệu này lệch nhau,
sửa một trong hai — không được để lệch im lặng.

Bối cảnh: một bài hình học phức tạp (chân đường cao, đường vuông góc, giao điểm,
đường tròn ngoại tiếp, giao điểm thứ hai, quỹ tích) từng được hệ render bằng
node/edge với **tọa độ do LLM đoán** — hình "nhìn có vẻ đúng" nhưng sai bản chất:
kéo M thì E/F/P đứng yên. Đây là vi phạm R0 ở tầng ngữ nghĩa.

---

## 1. Nguyên tắc nền (đã chốt)

1. **Canonical simulation phải đúng hoặc capability_gap.** Mô phỏng hệ thống
   sinh ra phải đúng theo deterministic rules/capabilities; engine chưa đủ năng
   lực thì từ chối trung thực — **không dựng xấp xỉ rồi giả vờ đúng**.
2. **Learner action được phép sai.** Thao tác/chỉnh sửa của học sinh có thể sai;
   nếu trạng thái sai vẫn có ý nghĩa học tập thì không nhất thiết reject.
3. **Chỉ deterministic engine/rule mới có quyền xác định đúng/sai.**
4. **Không có rule → `unsupported_to_verify`** — không phán đúng/sai giả tạo.
5. **Feedback là state/result data, không phải hội thoại chatbot.**
6. **LLM không bao giờ là judge correctness.** LLM chỉ trích xuất/phân loại/
   điền config/đề xuất patch — mọi phán quyết đúng-sai thuộc engine.

Một câu: *hệ mô phỏng thì đúng, học sinh thì được sai — và chỉ engine mới có
quyền nói học sinh sai ở đâu.*

### 1a. Correctness của Scene3D visibility và identity

1. Exact comparison dùng canonical machine edge IDs từ endpoint entity IDs;
   `display_label` không phải identity.
2. Mỗi logical edge có một visual owner và thuộc đúng một trong ba lớp
   `VISIBLE`, `HIDDEN`, `MIXED`. Edge mixed có nhiều spans nhưng vẫn một owner.
3. Chỉ canonical solid face được phép occlude mặc định. Base fill, section
   region, cutting plane và auxiliary surface không được tự biến thành vật che.
4. Highlight không được đổi dash policy; formation/causal selection phải giữ
   visibility signature của neutral state.
5. Section edge identity dẫn từ stable semantic endpoints. Coordinate fallback
   chỉ hợp lệ trong synthetic/legacy fixtures, không trong evidence
   authoritative.
6. Product classifier và evidence oracle phải độc lập về implementation.
   Perspective depth phải perspective-correct và được đối chiếu bằng reference
   camera ray/triangle.

Các invariant này đã PASS ở wave 2026-09-28; acceptance tổng do
`docs/CURRENT_STATE.md` sở hữu. Quyết định kiến trúc:
[`OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md).

## 2. Hai trục tách bạch: canonical vs learner

| | Canonical simulation | Learner action / edit |
|---|---|---|
| Ai tạo | Pipeline (compose/reuse) hoặc patch đã validate | Học sinh (drag, toggle, what-if, edit) |
| Được sai không | **Không** — đúng hoặc capability_gap | **Được** — sai là cơ hội học |
| Ai phán | Validator + engine tất định | Engine, và CHỈ khi có rule tất định |
| Sai thì sao | Từ chối/gap, không render | Giữ thành trạng thái/nhánh + feedback nếu có rule |

*Tiền lệ của giai đoạn Tin học (nhánh what-if của miền `algorithm`, đã gỡ): nguyên văn ở [`legacy/CORRECTNESS_INFORMATICS_ERA.md`](legacy/CORRECTNESS_INFORMATICS_ERA.md).*

## 2b. Trục thứ ba: CHẠY ĐƯỢC ≠ CHỨNG MINH ĐƯỢC (route sinh ngữ nghĩa)

Hai trục ở §2 đủ cho đường module: ở đó, config qua được validator là đủ để
phát, vì bản thân module đã mã hoá sẵn cơ chế đúng. Route sinh ngữ nghĩa
(`generic.semantic_program`) không có chỗ dựa ấy — chương trình do LLM viết ra
lần đầu tiên nhìn thấy — nên phải tách thêm một trục:

| | Câu hỏi | Trả lời KHÔNG thì gọi là |
|---|---|---|
| **executable** | Máy có **thực thi** được bài này thành mô phỏng? | `capability_gap` |
| **servable** | Đã đủ **bằng chứng** để phát như canonical? | `verification_gap` |

Gộp hai cái làm một là báo cáo sai năng lực của chính hệ theo hướng **bi quan**:
nói "không làm được" về một bài vừa chạy xong. Đó cũng là chỗ hai chỉ số
đồng-primary của đề tài tách nhau (`STATUS_LEDGER §0-2026-08-20`).

**`servable=false` KHÔNG phải một nhóm đồng nhất.** Bốn nguyên nhân gốc (thêm một
cổng thứ năm từ W15), khác hẳn nhau về bản chất, và chỉ nguyên nhân đầu mới là
"thiếu cách kiểm chứng":

| cổng | ý nghĩa khi trượt |
|---|---|
| C₁a mức yếu | nghĩa vụ **không có checker server-owned** → `verification_gap` |
| C₁b | có đường tạo witness nhưng **lượt chạy không đi qua** (nhánh chết) |
| C₂ | chương trình **tự mâu thuẫn** với nghĩa vụ nó tự khai |
| binding/compile | không dựng nổi bề mặt thị giác từ trace |
| `assumption` (W15) | `DEPENDENT`: đã CHỨNG MINH đáp số đổi theo một kích thước đề **không cho** (thiếu ở đề hoặc chương trình tự đặt — không phải hệ thiếu công cụ); `UNDETERMINED`: hệ **chưa chứng minh** được đáp số chỉ phụ thuộc dữ kiện đề — gần nghĩa `verification_gap`, nhưng mã là `INPUT_NOT_GROUNDED` và lời từ chối nói đúng điều ấy |

C₁b và C₂ chứng minh chương trình **hỏng**, không phải hệ thiếu công cụ. Gọi cả
bốn là `verification_gap` là báo cáo sai.

**Ba điều KHÔNG bị nới ở route này:**

1. **R0 nguyên vẹn.** LLM viết *chương trình*; `SemanticProgramInterpreter` mới
   là authority tính ra kết quả. `execution_authority_gate` thay khái niệm của
   `computation_gate` chứ không nới nó — luật cũ viết "algorithmic ⇒ từ chối",
   luật đúng luôn là "kết quả phải có **authority tất định** sở hữu". Khi hệ
   chưa có interpreter thì hai câu trùng nhau; nay đã có thì phải tách, nếu
   không hệ từ chối đúng lớp bài nó vừa làm được.
2. **Dữ liệu phải truy được về đề** (P2, `grounding_gate`). Ghim **đúng mục
   nào**, không phải "trông giống dữ liệu đề". Giới hạn P1 (Contract → đề gốc)
   còn mở và đã khai ở `semantic-benchmark/P1_LIMITATION.md`.
   **Từ W12 (2026-09-30) P1 có người đọc:** một GIVEN chỉ được nhận khi CÂU ĐỀ
   chứng minh nó — mục `analyze` là lời khai, không phải nguồn. Độ dài cần con
   số của đề (không nhãn đoạn/đơn vị nào mâu thuẫn); giá trị chỉ có trong lời
   khai ⇒ `GIVEN_VALUE_NOT_IN_SOURCE`; span lệch ⇒ `SOURCE_SPAN_MISMATCH`; mâu
   thuẫn ⇒ `SOURCE_EVIDENCE_CONFLICT` — ba mã không gửi đi sửa. Suy ra hợp lệ
   (cạnh bằng nhau của hình lập phương) là DERIVED, toạ độ bố cục là
   LAYOUT_DERIVED — cả hai không phải GIVEN. Giới hạn còn mở: kênh toạ độ giả
   thiết có thể cố định một kích thước đề không cho
   (`ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`); bất biến kiến trúc #36.

   **Từ W15 (2026-10-03), trong vùng đa diện, "served" còn có nghĩa: mọi giá trị số
   học sinh thấy đều có chứng chỉ giả định.** Có hai loại chứng chỉ. C0: mọi literal
   trên lát cắt của giá trị là dữ kiện đề của CÙNG thực thể, đọc tại định nghĩa với tới
   duy nhất. C1: một khuôn T1–T6 khớp ràng buộc server đọc từ CÂU ĐỀ, áp cho thể tích,
   diện tích, khoảng cách. Chú thích quan hệ của mô hình không bao giờ là tiền đề; toạ
   độ bố cục chỉ được làm "biên khuôn", tức vị trí mà ràng buộc khuôn kiểm lại. Không có
   chứng chỉ thì không phục vụ: phụ thuộc đã chứng minh ⇒ `ASSUMPTION_DETERMINES_ANSWER`;
   chưa chứng minh ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN`. Bảo đảm này **chỉ** trong vùng
   thi hành (đề nêu khối đa diện theo từ vựng đóng, quyết định U3); ngoài vùng hệ ghi
   trạng thái mà vẫn phục vụ như trước. Nó là kết quả trên corpus trong phạm vi đã
   đăng ký, không phải chứng minh tổng quát: lối viết ngoài từ vựng bị từ chối dù đề
   xác định đáp số. Thẩm quyền:
   [`ASSUMPTION_CERTIFICATE_AMENDMENT.md`](architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md);
   bất biến kiến trúc #37.

   **W16 (2026-10-03) siết hai chỗ của chứng chỉ ấy (§14):**
   - *"CÙNG thực thể" nay đúng cả với mặt phẳng cho bằng phương trình.* Một hệ số chỉ được
     ghim khi biến gắn được với đúng mặt phẳng của đề: theo tên viết trong mệnh đề
     phương trình, hoặc duy nhất theo đếm. Trùng bộ số không còn là căn cứ.
   - *Quan hệ trong yêu cầu chứng minh hoặc câu hỏi không bao giờ là tiền đề.* Các cụm
     `Chứng minh rằng …`, `CMR`, `Kiểm tra …`, `… hay không?` được che trước khi đọc
     tiền đề.

   Giới hạn W16 khai (C0 không kiểm một phép dựng có dùng đúng thực thể đề nói hay không,
   ví dụ (T) cắt bởi (α) trong khi đề nói (β)) nay đã đóng cho phép cắt — xem W17.

   **W17 (2026-10-04, §15) thêm ba nghĩa cho "served":**
   - *Thiết diện được phục vụ là thiết diện của đúng mặt phẳng và đúng khối đề nêu.* Mọi
     `construct_section` trên lát cắt phải cùng danh tính mặt phẳng và cùng khối với câu
     cắt của đề. Lệch chắc chắn ⇒ `CONSTRUCTION_NOT_TEXT_BOUND`; không ghim được ⇒
     `ASSUMPTION_INVARIANCE_UNPROVEN`.
   - *Giá trị chỉ có trong yêu cầu chứng minh không bao giờ là dữ kiện*, ở mọi vùng: grounding
     đọc trên đề đã che mục tiêu (`GIVEN_ONLY_IN_GOAL_CLAUSE`). "Tính …, biết …" và
     "… bao nhiêu, biết Y?" vẫn là dữ kiện.
   - *Lời từ chối nói đúng nguyên nhân* (SOURCE / CONSTRUCTION / UNKNOWN). Chỉ SOURCE bảo
     người học sửa đề; lỗi dựng của hệ không bao giờ đổ cho đề.

   Giới hạn khai thẳng: chỉ phép cắt được đối chiếu với đề. Trung điểm, chân đường vuông góc
   thì chưa (`ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`). Câu cắt ngoài từ vựng
   đóng ("(Q) qua M và song song với (X)") bị từ chối dù chương trình đúng
   (`ISSUE-ARCH-CUT-PLANE-BY-POINT-AND-PARALLEL`).

   **W18 (2026-10-04, §16) thêm một nghĩa cho "served":**
   - *Điểm đề gọi tên là trung điểm hay hình chiếu được dựng đúng trên thực thể đề nêu*, ở
     mọi vùng, xét theo danh tính, không theo toạ độ hay giá trị. Ví dụ đề nói "M là trung
     điểm của SA" mà chương trình dựng trung điểm SB thì bị từ chối
     `CONSTRUCTION_NOT_TEXT_BOUND`, dù giá trị tình cờ bằng nhau; lời từ chối nêu cả hai quan
     hệ. Danh sách "lần lượt" ghép theo thứ tự. Đổi tên đích hay tráo hai đích cũng bị bắt.
   - *Điểm phụ của hệ* mang xuất xứ `AUXILIARY`, không bao giờ là dữ kiện đề cho.

   Giới hạn khai thẳng (đã đóng phần trung điểm/hình chiếu của
   `ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`):
   - Cách nói ngoài từ vựng đóng là "chưa đối chiếu được" (UNVERIFIED): bị từ chối trong vùng
     đa diện dù chương trình đúng, và lời từ chối không nói đề sai.
   - Tâm, trọng tâm, giao điểm, điểm đối xứng chưa được đối chiếu theo danh tính
     (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`).
3. **Cổng nội bộ KHÔNG phải oracle.** `servable=true` nghĩa là *qua hết cổng nội
   bộ* (STRONG-assurance), **không** nghĩa là *đúng*. Correctness theo oracle
   độc lập phải báo riêng, và case `servable` mà oracle nói sai phải được nêu
   đích danh — che nó bằng một cái nhãn đẹp là tự bịt mắt mình.

### 2b-bis. Trục này ĐÃ ĐƯỢC ĐO — SEALED `7e5df014…` (2026-08-23)

Nguồn: `docs/evaluation/semantic-benchmark/results/OFFICIAL_RESULT.md`. Candidate
`4e13e2b`, N=40, `evaluation_complete = true`, lượt **duy nhất**.

| trục | đo được |
|---|---|
| **executable** (A) | 3/40 |
| **servable** (B) | 1/40 |
| **oracle độc lập** | PASS 2 · FAIL 0 · UNGRADED 9 · NO_RESULT 29 |

Ba điều lượt đo này xác nhận, và một điều nó **không** xác nhận:

- **Tách A/B là đúng và cần thiết.** A ≠ B trên dữ liệu thật (3 vs 1). Gộp lại
  là mất thông tin.
- **`servable=false` thật sự không đồng nhất.** `A − B = 2` và **cả hai là C₂**
  (chương trình tự mâu thuẫn), `verification_gap` = **0**. Nếu đã gọi cả khối là
  `verification_gap` thì báo cáo đã sai 2/2.
- **Cổng nội bộ bảo thủ, không lỏng.** `phát nhưng oracle nói SAI` = **0**;
  ngược lại có **1 false rejection** (`T11CS-C6-041`: oracle ĐÚNG mà C₂ chặn).
  Hướng lệch của biên assurance là **an toàn**.
- **Lượt này KHÔNG đo được năng lực ngữ nghĩa.** 17/40 case chết trước mọi tầng
  ngữ nghĩa vì `spec_version` phát ra là số JSON `1.0` trong khi schema đòi chuỗi
  `"1.0"`. A = 3/40 vì thế là **cận dưới của cận dưới**, không phải ước lượng
  năng lực. Theo luật con dấu, sửa rồi chạy lại là **cấm** — phải niêm phong
  SEALED mới.

## 3. Taxonomy kết quả patch/edit (PatchResult) — TÁCH với interaction feedback

> Đường patch/edit (M7.14) và `InteractionFeedback` của miền generic đã gỡ cùng miền Tin học. Nguyên văn mục này: [`legacy/CORRECTNESS_INFORMATICS_ERA.md`](legacy/CORRECTNESS_INFORMATICS_ERA.md) (`frontend/src/llm/client.ts` còn trích nó).

## 4. Ba luật chống trượt thành tutor/chatbot

1. **Feedback là dẫn xuất của rule, không phải văn của LLM.** Message sinh từ
   rule bị vi phạm (rule → chuỗi tiếng Việt cố định trong engine), không gọi
   mạng, không sinh văn tự do.
2. **Feedback là field của state, không phải lượt hội thoại.** Render trong
   workspace/inspector; không turn-taking, không lịch sử chat, không "AI nhận
   xét bài làm".
3. **Không có bề mặt Q&A LLM nào** — `/api/explain` (giải thích trạng thái engine của miền Tin học, người gọi duy
   nhất là panel không còn gắn) đã gỡ ở run `repo-cleanup`. Không thêm endpoint hội thoại.

## 5–6. (giai đoạn Tin học)

Phân loại A/B/C toàn hệ (§5) và giới hạn tuyên bố của node/edge generic (§6): nguyên văn ở [`legacy/CORRECTNESS_INFORMATICS_ERA.md`](legacy/CORRECTNESS_INFORMATICS_ERA.md).

## 7. Chính sách kiểm thử: offline-first, live là opt-in (M7.14T)

Correctness guard chỉ có giá trị nếu **chạy được thường xuyên mà không đốt
quota**. Vì vậy:

- `pytest` và `vitest` **luôn = 0 API call thật**. Guard nằm ở BIÊN MẠNG
  (`backend/conftest.py` patch transport httpx; `frontend/src/test-setup.ts`
  stub `fetch`), nên **suite xanh ⇔ không có call nào** — quên mock là đỏ ngay,
  không âm thầm gọi thật. Guard cũng gỡ `GEMINI_API_KEY` khỏi env (backend/.env
  được `load_dotenv` nạp lúc import → key thật vốn nằm sẵn trong tiến trình test).
- Lượt gọi provider thật là opt-in (`ALLOW_LIVE_AI=1`), chạy bằng các script `backend/scripts/run_*` /
  `probe_*`, với ngân sách và luật dừng đăng ký trước (`AGENTS.md`, *Đo lường có trần*). Runner `live.py`
  của giai đoạn Tin học đã gỡ: nguyên văn ở [`legacy/CORRECTNESS_INFORMATICS_ERA.md`](legacy/CORRECTNESS_INFORMATICS_ERA.md).

## 8–9. (giai đoạn Tin học)

Lộ trình known-gap của DSL (§8) và chính sách normalize-not-refuse của
`binary_search` (§9, `backend/app/main.py` còn trích): nguyên văn ở [`legacy/CORRECTNESS_INFORMATICS_ERA.md`](legacy/CORRECTNESS_INFORMATICS_ERA.md).
