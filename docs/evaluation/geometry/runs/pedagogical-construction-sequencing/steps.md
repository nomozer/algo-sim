# Trình tự dựng trước / sau — ba họ hình

Trước: `../scene3d-construction-audit/after/intel-d3d11/` (product `eea6f3df`). Sau: `after/intel-d3d11/` (product `c217aade`).
Mỗi dòng là một BƯỚC HỌC (khung `anchor` của `geometryTimeline`); lời là lời kể các bước trace gộp vào bước ấy.

## two-line-pyramid — trước 13 bước học / 16 trace · sau 13 / 16

| # | trước | sau |
|---|---|---|
| 1 | Đặt các điểm đề cho vào không gian. | Đặt các điểm đề cho vào không gian. |
| 2 | Dựng M. · Lấy vectơ BC. | Dựng đáy ABCD. |
| 3 | Dựng H. · Lấy vectơ AS. | Dựng các cạnh bên SA, SB, SC, SD. |
| 4 | Dựng H1. | Dựng hình chóp S.ABCD (5 đỉnh, 5 mặt). |
| 5 | Dựng đáy ABCD. | Dựng M là trung điểm của đoạn AB. · Lấy vectơ BC. |
| 6 | Dựng các cạnh bên SA, SB, SC, SD. | Qua M dựng điểm H sao cho vectơ MH bằng vectơ BC. · Lấy vectơ AS. |
| 7 | Dựng hình chóp S.ABCD (5 đỉnh, 5 mặt). | Qua M dựng điểm H1 sao cho vectơ MH1 bằng vectơ AS. |
| 8 | Dựng (P). | Dựng (P). |
| 9 | Trên mặt ABCD, nối giao điểm thuộc cạnh AB với giao điểm thuộc cạnh CD. | Trên mặt ABCD, nối giao điểm thuộc cạnh AB với giao điểm thuộc cạnh CD. |
| 10 | Trên mặt SCD, nối giao điểm thuộc cạnh CD với giao điểm thuộc cạnh SC. | Trên mặt SCD, nối giao điểm thuộc cạnh CD với giao điểm thuộc cạnh SC. |
| 11 | Trên mặt SBC, nối giao điểm thuộc cạnh SC với giao điểm thuộc cạnh SB. | Trên mặt SBC, nối giao điểm thuộc cạnh SC với giao điểm thuộc cạnh SB. |
| 12 | Trên mặt SAB, nối giao điểm thuộc cạnh SB với giao điểm thuộc cạnh AB. | Trên mặt SAB, nối giao điểm thuộc cạnh SB với giao điểm thuộc cạnh AB. |
| 13 | Thiết diện khép lại thành tứ giác: (P) cắt hình chóp S.ABCD. · Diện tích thiết diện bằng 9/4. | Thiết diện khép lại thành tứ giác: (P) cắt hình chóp S.ABCD. · Diện tích thiết diện bằng 9/4. |

## two-line-prism — trước 11 bước học / 14 trace · sau 14 / 17

| # | trước | sau |
|---|---|---|
| 1 | Đặt các điểm đề cho vào không gian. | Đặt các điểm đề cho vào không gian. |
| 2 | Dựng M. · Lấy vectơ BC. | Dựng đáy dưới ABC. |
| 3 | Dựng H. · Lấy vectơ BB′. | Dựng đáy trên A′B′C′. |
| 4 | Dựng H1. | Dựng các cạnh bên AA′, BB′, CC′. |
| 5 | Dựng lăng trụ đứng ABC.A′B′C′ (6 đỉnh, 5 mặt). | Dựng lăng trụ đứng ABC.A′B′C′ (6 đỉnh, 5 mặt). |
| 6 | Dựng (P). | Dựng M là trung điểm của đoạn AB. · Lấy vectơ BC. |
| 7 | Trên mặt ABC, nối giao điểm thuộc cạnh AB với giao điểm thuộc cạnh AC. | Qua M dựng điểm H sao cho vectơ MH bằng vectơ BC. · Lấy vectơ BB′. |
| 8 | Trên mặt CAA′C′, nối giao điểm thuộc cạnh AC với giao điểm thuộc cạnh A′C′. | Qua M dựng điểm H1 sao cho vectơ MH1 bằng vectơ BB′. |
| 9 | Trên mặt A′B′C′, nối giao điểm thuộc cạnh A′C′ với giao điểm thuộc cạnh A′B′. | Dựng (P). |
| 10 | Trên mặt ABB′A′, nối giao điểm thuộc cạnh A′B′ với giao điểm thuộc cạnh AB. | Trên mặt ABC, nối giao điểm thuộc cạnh AB với giao điểm thuộc cạnh AC. |
| 11 | Thiết diện khép lại thành tứ giác: (P) cắt lăng trụ đứng ABC.A′B′C′. · Diện tích thiết diện bằng 3. | Trên mặt CAA′C′, nối giao điểm thuộc cạnh AC với giao điểm thuộc cạnh A′C′. |
| 12 |  | Trên mặt A′B′C′, nối giao điểm thuộc cạnh A′C′ với giao điểm thuộc cạnh A′B′. |
| 13 |  | Trên mặt ABB′A′, nối giao điểm thuộc cạnh A′B′ với giao điểm thuộc cạnh AB. |
| 14 |  | Thiết diện khép lại thành tứ giác: (P) cắt lăng trụ đứng ABC.A′B′C′. · Diện tích thiết diện bằng 3. |

## two-line-cuboid — trước 11 bước học / 14 trace · sau 14 / 17

| # | trước | sau |
|---|---|---|
| 1 | Đặt các điểm đề cho vào không gian. | Đặt các điểm đề cho vào không gian. |
| 2 | Dựng M. · Lấy vectơ BC. | Dựng đáy dưới ABCD. |
| 3 | Dựng H. · Lấy vectơ BB′. | Dựng đáy trên A′B′C′D′. |
| 4 | Dựng H1. | Dựng các cạnh bên AA′, BB′, CC′, DD′. |
| 5 | Dựng hình hộp chữ nhật ABCD.A′B′C′D′ (8 đỉnh, 6 mặt). | Dựng hình hộp chữ nhật ABCD.A′B′C′D′ (8 đỉnh, 6 mặt). |
| 6 | Dựng (P). | Dựng M là trung điểm của đoạn AB. · Lấy vectơ BC. |
| 7 | Trên mặt ABCD, nối giao điểm thuộc cạnh AB với giao điểm thuộc cạnh CD. | Qua M dựng điểm H sao cho vectơ MH bằng vectơ BC. · Lấy vectơ BB′. |
| 8 | Trên mặt CDD′C′, nối giao điểm thuộc cạnh CD với giao điểm thuộc cạnh C′D′. | Qua M dựng điểm H1 sao cho vectơ MH1 bằng vectơ BB′. |
| 9 | Trên mặt A′B′C′D′, nối giao điểm thuộc cạnh C′D′ với giao điểm thuộc cạnh A′B′. | Dựng (P). |
| 10 | Trên mặt ABB′A′, nối giao điểm thuộc cạnh A′B′ với giao điểm thuộc cạnh AB. | Trên mặt ABCD, nối giao điểm thuộc cạnh AB với giao điểm thuộc cạnh CD. |
| 11 | Thiết diện khép lại thành tứ giác: (P) cắt hình hộp chữ nhật ABCD.A′B′C′D′. · Diện tích thiết diện bằng 12. | Trên mặt CDD′C′, nối giao điểm thuộc cạnh CD với giao điểm thuộc cạnh C′D′. |
| 12 |  | Trên mặt A′B′C′D′, nối giao điểm thuộc cạnh C′D′ với giao điểm thuộc cạnh A′B′. |
| 13 |  | Trên mặt ABB′A′, nối giao điểm thuộc cạnh A′B′ với giao điểm thuộc cạnh AB. |
| 14 |  | Thiết diện khép lại thành tứ giác: (P) cắt hình hộp chữ nhật ABCD.A′B′C′D′. · Diện tích thiết diện bằng 12. |
