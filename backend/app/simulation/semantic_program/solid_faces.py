# -*- coding: utf-8 -*-
"""Phân loại TỔ HỢP bảng mặt của một khối đa diện — module LÁ.

Chỉ đọc số đỉnh và bảng mặt (chỉ số đỉnh). Không toạ độ, không tên, không nhãn:
hai khối cùng bảng mặt cho cùng kết quả. `display_names` (đặt tên khối) và
`formation` (dựng hình theo lớp) dùng chung MỘT bản — một thẩm quyền tô-pô, không
hai. Tách từ `display_names._phan_loai_khoi` (W14); phần hình học CHÍNH XÁC (đứng,
hình hộp, lập phương) ở lại `display_names`. Không import gì trong gói (khoá:
`test_solid_faces_la_la`).
"""
from __future__ import annotations


def phan_loai_bang_mat(so_dinh: int, mat: list[list[int]]) -> list[tuple[str, list[int], list[int]]]:
    """MỌI cách đọc bảng mặt thành chóp hoặc lăng trụ, theo đúng thứ tự duyệt gốc.

    `("pyramid", [đỉnh], đáy)` — một đỉnh nằm ngoài đúng một mặt, mọi mặt khác là
    tam giác; mỗi mặt thoả là một cách (tứ diện có bốn).
    `("prism", đáy, trên)` — hai mặt rời nhau cùng số đỉnh, mọi mặt khác là tứ giác,
    `trên[k]` tương ứng `đáy[k]` qua mặt bên, và tương ứng ấy là SONG ÁNH (không song
    ánh ⇒ cặp nắp không cho cách đọc nào). Mỗi cặp nắp cho HAI hướng; hướng đứng
    trước là hướng có đáy chứa đỉnh khai đầu tiên (`ABC.DEF`, không `DEF.ABC`).

    Chóp đứng trước lăng trụ, nên phần tử đầu là đúng kết quả cũ của
    `_phan_loai_khoi`. Bảng mặt phải hợp lệ (chỉ số trong miền, mặt ≥ 3 đỉnh khác
    nhau) — người gọi kiểm trước.
    """
    ra: list[tuple[str, list[int], list[int]]] = []
    n, so_mat = so_dinh, len(mat)
    for i, day in enumerate(mat):
        con_lai = set(range(n)) - set(day)
        if (len(con_lai) == 1 and len(day) == n - 1 and so_mat == n
                and all(len(f) == 3 for j, f in enumerate(mat) if j != i)):
            ra.append(("pyramid", [con_lai.pop()], list(day)))
    for i, f in enumerate(mat):
        for j, g in enumerate(mat):
            if (j <= i or len(f) != len(g) or set(f) & set(g)
                    or 2 * len(f) != n or so_mat != len(f) + 2):
                continue
            ben = [h for k, h in enumerate(mat) if k not in (i, j)]
            if not all(len(h) == 4 for h in ben):
                continue
            doi: dict[int, int] = {}
            for h in ben:
                for u, w in zip(h, h[1:] + h[:1]):
                    if u in f and w in g:
                        doi[u] = w
                    elif w in f and u in g:
                        doi[w] = u
            if len(doi) != len(f):
                continue
            nguoc = {w: u for u, w in doi.items()}
            if len(nguoc) != len(g):
                # Tương ứng KHÔNG song ánh ⇒ nắp đọc ra lặp đỉnh (`[3, 3, 5]`): không phải
                # lăng trụ theo hướng nào (W15). Trước đây giữ một hướng — một cách đọc vô
                # nghĩa mà `display_names` đem gọi tên.
                continue
            xuoi = ("prism", list(f), [doi[v] for v in f])
            lui = ("prism", list(g), [nguoc[v] for v in g])
            ra += [xuoi, lui] if min(f) < min(g) else [lui, xuoi]
    return ra
