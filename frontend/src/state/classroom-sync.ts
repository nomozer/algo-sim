/**
 * ĐỒNG BỘ LỚP HỌC — quyết định "áp lệnh nào" là HÀM THUẦN.
 *
 * ─── VÌ SAO TÁCH KHỎI STORE ─────────────────────────────────────────────
 *
 * Luật ở đây là thứ dễ sai nhất và khó nhìn nhất của cả tính năng: *khi nào
 * trạng thái giáo viên được phép ghi đè lên thao tác học sinh*. Sai một nhánh
 * thì hoặc học sinh bị giật về mỗi vài giây, hoặc lệnh "gọi cả lớp về đây"
 * không tới ai cả.
 *
 * Store zustand không kiểm được bằng SSR (`useSyncExternalStore` luôn trả
 * trạng thái đầu — `ARCHITECTURE_MAP §8` #8), nên luật phải sống ở hàm thuần.
 *
 * ─── BA NHÁNH, KHÔNG PHẢI HAI ───────────────────────────────────────────
 *
 *   BÁM THEO   → lệnh mới nào cũng áp.
 *   TỰ DO      → KHÔNG áp… trừ đúng một ngoại lệ:
 *   GỌI VỀ     → `syncCmdId` tăng thì áp ĐÚNG MỘT LẦN, rồi trả lại tự do.
 *
 * Gộp "gọi về" vào "bám theo" thì giáo viên phải đổi chế độ để gọi cả lớp, và
 * quên bật lại là cả lớp bị khoá mà không ai hiểu vì sao.
 */
import type { InteractionState } from "../simulations/domains/geometry/interaction-state";

/** Trạng thái phiên do MÁY CHỦ phát. Hình dạng khớp `session_router`. */
export interface ClassroomSession {
  sessionId: number;
  roundId: string;
  cmdId: number;
  syncCmdId: number;
  mode: "follow" | "free";
  assignmentId: number | null;
  simulationId: string | null;
  currentStep: number;
  selectedId: string | null;
  isolatedIds: string[];
  explodedGroups: string[];
  updatedAt: string | null;
}

/**
 * Cái client NHỚ để không áp lại một lệnh đã áp.
 *
 * Máy chủ KHÔNG nhớ hộ từng học sinh đã thấy tới đâu — nhớ hộ là dựng một hàng
 * đợi cho mỗi em. Nó phát một con số tăng đơn điệu; phần còn lại là việc của
 * client, và vì thế nó phải nằm ở đây chứ không rải trong component.
 */
export interface SeenMarks {
  roundId: string | null;
  cmdId: number;
  syncCmdId: number;
}

export const CHUA_THAY: SeenMarks = { roundId: null, cmdId: -1, syncCmdId: -1 };

export interface ApplyResult {
  /** Trạng thái xem MỚI, hoặc chính `local` nếu không có gì để áp. */
  next: InteractionState;
  seen: SeenMarks;
  /** Đã áp trạng thái giáo viên trong lượt này chưa — để hiện lời báo ngắn. */
  applied: boolean;
  /** Vì sao — chỉ để hiện cho người dùng, không dùng để rẽ nhánh. */
  reason: "follow" | "sync" | "none";
}

/**
 * ID nào của giáo viên còn có nghĩa trong cảnh này (`§21`).
 *
 * Giáo viên có thể đang chiếu một bài khác, hoặc chọn một vật vừa bị đổi tên.
 * Bỏ ID lạc và đi tiếp — **fail-safe, không sập phiên**. Dựng một vật mới cho
 * khớp ID là suy hình học ở tầng nhìn, đúng thứ ranh giới cấm.
 */
function locId(ids: string[], coTrongCanh: (id: string) => boolean): string[] {
  return ids.filter(coTrongCanh);
}

/**
 * Áp trạng thái phiên lên trạng thái xem cục bộ.
 *
 * `coTrongCanh` do bên gọi cấp — module này không biết Scene3D, và không được
 * biết: nó điều phối, không phán vật nào tồn tại.
 */
export function apDungPhien(
  local: InteractionState,
  phien: ClassroomSession | null,
  seen: SeenMarks,
  coTrongCanh: (id: string) => boolean = () => true,
): ApplyResult {
  if (phien === null) {
    // Tiết đã kết thúc (hoặc chưa bắt đầu). KHÔNG hoàn nguyên gì: học sinh
    // đang xem cái gì thì cứ để em ấy xem tiếp. Kéo về một trạng thái "sạch"
    // ở đây là xoá công của em ấy vì một lý do em ấy không gây ra.
    return { next: local, seen: CHUA_THAY, applied: false, reason: "none" };
  }

  // Round mới ⇒ mọi mốc cũ vô nghĩa. Không đặt lại thì một `cmdId` của tiết
  // trước (vốn có thể LỚN HƠN) sẽ nuốt mọi lệnh của tiết mới.
  const cungRound = seen.roundId === phien.roundId;
  const daThay: SeenMarks = cungRound ? seen : { ...CHUA_THAY, roundId: phien.roundId };

  const lenhMoi = phien.cmdId > daThay.cmdId;
  const goiVe = phien.syncCmdId > daThay.syncCmdId && phien.syncCmdId > 0;
  const nen = lenhMoi && (phien.mode === "follow" || goiVe);

  const mocMoi: SeenMarks = {
    roundId: phien.roundId,
    cmdId: Math.max(daThay.cmdId, phien.cmdId),
    syncCmdId: Math.max(daThay.syncCmdId, phien.syncCmdId),
  };

  if (!nen) return { next: local, seen: mocMoi, applied: false, reason: "none" };

  return {
    next: {
      ...local,
      current_step: phien.currentStep,
      selected_id:
        phien.selectedId && coTrongCanh(phien.selectedId) ? phien.selectedId : null,
      isolated_ids: locId(phien.isolatedIds, coTrongCanh),
      // `exploded_groups` là TÊN NHÓM (`face`), không phải id vật — không lọc
      // qua `coTrongCanh`, và lọc nhầm thì bung hình của giáo viên biến mất.
      exploded_groups: [...phien.explodedGroups],
    },
    seen: mocMoi,
    applied: true,
    reason: phien.mode === "follow" ? "follow" : "sync",
  };
}

/**
 * Nhịp hỏi lại, tính bằng mili-giây.
 *
 * Hai nhịp KHÁC NHAU vì hai câu hỏi khác nhau về độ trễ chấp nhận được: lệnh
 * của giáo viên mà tới chậm 5 giây thì cả lớp nhìn nhầm chỗ trong lúc thầy
 * đang nói; bảng theo dõi chậm 5 giây thì không ai thiệt gì.
 *
 * KHÔNG dựng WebSocket cho việc này: repo chưa có hạ tầng ấy, và một kênh
 * thời gian thực chỉ để đẩy một object vài trăm byte mỗi giây rưỡi là thêm
 * một chế độ hỏng (mất kết nối, tái kết nối, thứ tự tin nhắn) đổi lấy một độ
 * trễ không ai cảm được.
 */
export const NHIP_PHIEN_MS = 1500;
export const NHIP_THEO_DOI_MS = 4000;

/**
 * Có nên gửi tiến độ lên không — CHỐNG SPAM ở nguồn.
 *
 * Học sinh xoay hình sinh ra hàng chục thay đổi mỗi giây. Gửi hết là dựng một
 * máy theo dõi thay vì một lớp học, và bảng của giáo viên cũng không đọc nổi.
 * Chỉ gửi khi TIÊU ĐIỂM NGỮ NGHĨA đổi, và không nhanh hơn `toiThieuMs`.
 */
export function nenGuiTienDo(
  truoc: { step: number; selectedId: string | null; luc: number } | null,
  nay: { step: number; selectedId: string | null; luc: number },
  toiThieuMs = 1000,
): boolean {
  if (truoc === null) return true;
  if (nay.luc - truoc.luc < toiThieuMs) return false;
  return truoc.step !== nay.step || truoc.selectedId !== nay.selectedId;
}
