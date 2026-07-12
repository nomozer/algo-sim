import type { AnalysisOk, AlgorithmId } from "../core/types";

/**
 * Ngân hàng bài mẫu (R2.3e) — kết quả phân tích soạn sẵn, chạy offline
 * không cần API. Mỗi thuật toán một bài, đề bám ngữ cảnh SGK.
 */

export interface SampleProblem {
  id: string;
  algorithmId: AlgorithmId;
  problemText: string;
  analysis: AnalysisOk;
}

export const SAMPLES: SampleProblem[] = [
  {
    id: "diem-cao-nhat",
    algorithmId: "find_max",
    problemText:
      "Tổ 1 lớp 10A có 8 bạn với điểm kiểm tra Tin học lần lượt: An 7,5; Bình 9; Chi 6,5; Dũng 8; Em 5,5; Giang 8,5; Hà 7; Khang 6. Hãy tìm bạn có điểm cao nhất.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Tìm học sinh có điểm kiểm tra cao nhất trong tổ 8 bạn",
        input: "Danh sách điểm kiểm tra của 8 học sinh tổ 1 lớp 10A",
        output: "Học sinh có điểm cao nhất và giá trị điểm đó",
      },
      algorithm_id: "find_max",
      data: {
        array: [7.5, 9, 6.5, 8, 5.5, 8.5, 7, 6],
        labels: ["An", "Bình", "Chi", "Dũng", "Em", "Giang", "Hà", "Khang"],
        target: null,
        condition: null,
        order: null,
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "nhiet-do-thap-nhat",
    algorithmId: "find_min",
    problemText:
      "Nhiệt độ trung bình 7 ngày trong tuần ở Hà Nội lần lượt là 28; 26; 31; 24; 27; 30; 25 (độ C). Tìm ngày có nhiệt độ thấp nhất.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Tìm ngày có nhiệt độ trung bình thấp nhất trong tuần",
        input: "Nhiệt độ trung bình của 7 ngày trong tuần (độ C)",
        output: "Ngày có nhiệt độ thấp nhất và giá trị nhiệt độ đó",
      },
      algorithm_id: "find_min",
      data: {
        array: [28, 26, 31, 24, 27, 30, 25],
        labels: ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"],
        target: null,
        condition: null,
        order: null,
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "tong-tien-tren-50",
    algorithmId: "sum_if",
    problemText:
      "Cửa hàng ghi lại số tiền (nghìn đồng) của 9 đơn hàng trong buổi sáng: 45; 120; 80; 30; 95; 150; 60; 25; 110. Tính tổng tiền của các đơn hàng từ 80 nghìn trở lên.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Tính tổng tiền các đơn hàng có giá trị từ 80 nghìn đồng trở lên",
        input: "Số tiền của 9 đơn hàng trong buổi sáng (nghìn đồng)",
        output: "Tổng tiền của các đơn hàng ≥ 80 nghìn đồng",
      },
      algorithm_id: "sum_if",
      data: {
        array: [45, 120, 80, 30, 95, 150, 60, 25, 110],
        labels: null,
        target: null,
        condition: { op: ">=", value: 80 },
        order: null,
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "dem-hoc-sinh-gioi",
    algorithmId: "count_if",
    problemText:
      "Điểm trung bình môn Tin của 10 bạn trong nhóm là: 8,2; 6,5; 9,1; 7,8; 8,0; 5,9; 8,7; 7,2; 9,4; 6,8. Đếm xem có bao nhiêu bạn đạt loại giỏi (từ 8,0 trở lên).",
    analysis: {
      status: "ok",
      problem: {
        summary: "Đếm số học sinh đạt điểm trung bình môn từ 8,0 trở lên",
        input: "Điểm trung bình môn Tin học của 10 học sinh",
        output: "Số lượng học sinh đạt loại giỏi (điểm ≥ 8,0)",
      },
      algorithm_id: "count_if",
      data: {
        array: [8.2, 6.5, 9.1, 7.8, 8.0, 5.9, 8.7, 7.2, 9.4, 6.8],
        labels: null,
        target: null,
        condition: { op: ">=", value: 8 },
        order: null,
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "tim-ma-so",
    algorithmId: "linear_search",
    problemText:
      "Danh sách số báo danh của 8 thí sinh trong phòng thi (xếp theo chỗ ngồi): 105; 213; 178; 154; 231; 189; 122; 167. Kiểm tra xem thí sinh số báo danh 189 có ngồi trong phòng này không.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Tìm thí sinh có số báo danh 189 trong danh sách phòng thi",
        input: "Danh sách 8 số báo danh xếp theo chỗ ngồi (chưa theo thứ tự)",
        output: "Vị trí của thí sinh 189, hoặc kết luận không có trong phòng",
      },
      algorithm_id: "linear_search",
      data: {
        array: [105, 213, 178, 154, 231, 189, 122, 167],
        labels: null,
        target: 189,
        condition: null,
        order: null,
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "tra-tu-dien",
    algorithmId: "binary_search",
    problemText:
      "Sổ điểm đã xếp theo thứ tự tăng dần: 4; 5,5; 6; 6,5; 7; 8; 8,5; 9; 9,5; 10. Kiểm tra xem có bạn nào được 8,5 điểm không, tìm nhanh nhất có thể.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Tìm điểm 8,5 trong sổ điểm đã sắp thứ tự tăng dần",
        input: "Dãy 10 mức điểm đã xếp tăng dần",
        output: "Vị trí của mức điểm 8,5, hoặc kết luận không có",
      },
      algorithm_id: "binary_search",
      data: {
        array: [4, 5.5, 6, 6.5, 7, 8, 8.5, 9, 9.5, 10],
        labels: null,
        target: 8.5,
        condition: null,
        order: null,
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "xep-hang-chieu-cao",
    algorithmId: "bubble_sort",
    problemText:
      "Chiều cao (cm) của 7 bạn trong đội bóng rổ: 172; 158; 180; 165; 175; 160; 168. Sắp xếp danh sách theo chiều cao tăng dần để xếp hàng chụp ảnh.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Sắp xếp 7 bạn theo chiều cao tăng dần bằng phương pháp nổi bọt",
        input: "Chiều cao của 7 thành viên đội bóng rổ (cm)",
        output: "Danh sách chiều cao đã xếp tăng dần",
      },
      algorithm_id: "bubble_sort",
      data: {
        array: [172, 158, 180, 165, 175, 160, 168],
        labels: null,
        target: null,
        condition: null,
        order: "asc",
      },
      data_generated: false,
      notes: null,
    },
  },
  {
    id: "xep-bai-tren-tay",
    algorithmId: "insertion_sort",
    problemText:
      "Bạn Nam đang cầm trên tay các quân bài có số: 7; 3; 9; 4; 8; 2. Hãy sắp xếp các quân bài tăng dần theo đúng cách người chơi bài hay làm: rút từng quân và chèn vào đúng chỗ.",
    analysis: {
      status: "ok",
      problem: {
        summary: "Sắp xếp các quân bài tăng dần bằng phương pháp chèn",
        input: "Dãy 6 quân bài trên tay theo thứ tự đang cầm",
        output: "Dãy quân bài đã xếp tăng dần",
      },
      algorithm_id: "insertion_sort",
      data: {
        array: [7, 3, 9, 4, 8, 2],
        labels: null,
        target: null,
        condition: null,
        order: "asc",
      },
      data_generated: false,
      notes: null,
    },
  },
];
