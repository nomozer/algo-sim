"""Phát hiện vùng bài toán tự động và tiền xử lý ảnh nhẹ — tất định, 0 lượt gọi AI.

Chiến lược (§10.A, §11–§14):
1. Đánh giá chất lượng ảnh (độ sáng, độ tương phản, độ nét) và cân bằng sáng nhẹ cho ảnh
   thiếu sáng mà không làm đứt nét mảnh của ký hiệu toán (`A′`, `⟂`, `∥`, chỉ số dưới).
2. Tách ranh giới trang giấy khỏi nền bàn học / mép ngoài khi có độ tương phản nền–giấy rõ.
3. Ước lượng góc nghiêng dòng chữ bằng phương sai chiếu ngang trên ảnh nhị phân thu nhỏ
   (tăng tốc bằng C-kernel của Pillow) và xoay thẳng khi độ tin cậy cao.
4. Phân vùng bố cục (khối chữ, công thức, hình vẽ minh họa, chú thích), loại nhiễu rìa trang
   và tự động ghép khối chữ với hình vẽ liên quan (nằm cạnh hoặc nằm dưới).
5. Phát hiện trường hợp nhiều bài toán độc lập tách biệt; kiểm chứng độ đầy đủ biên cắt và
   luôn giữ cơ chế fallback về ảnh chuẩn hóa đầy đủ khi độ tin cậy vùng cắt chưa đủ cao.
"""

from __future__ import annotations

import base64
import hashlib
import io
import math
from dataclasses import dataclass
from typing import Literal

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

from app.ingestion.image import JPEG_QUALITY, MAX_SEND_SIDE, NormalizedImage


@dataclass(frozen=True)
class BoundingBox:
    """Khung bao theo pixel trên ảnh đã chuẩn hóa hướng (`0 <= x0 < x1 <= w`)."""

    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def width(self) -> int:
        return max(0, self.x1 - self.x0)

    @property
    def height(self) -> int:
        return max(0, self.y1 - self.y0)

    @property
    def area(self) -> int:
        return self.width * self.height

    def normalized(self, img_w: int, img_h: int) -> tuple[float, float, float, float]:
        if img_w <= 0 or img_h <= 0:
            return (0.0, 0.0, 1.0, 1.0)
        return (
            round(self.x0 / img_w, 4),
            round(self.y0 / img_h, 4),
            round(self.width / img_w, 4),
            round(self.height / img_h, 4),
        )

    def union(self, other: "BoundingBox") -> "BoundingBox":
        return BoundingBox(
            min(self.x0, other.x0),
            min(self.y0, other.y0),
            max(self.x1, other.x1),
            max(self.y1, other.y1),
        )

    def pad(self, pad_x: int, pad_y: int, max_w: int, max_h: int) -> "BoundingBox":
        return BoundingBox(
            max(0, self.x0 - pad_x),
            max(0, self.y0 - pad_y),
            min(max_w, self.x1 + pad_x),
            min(max_h, self.y1 + pad_y),
        )


@dataclass(frozen=True)
class LayoutBlock:
    bbox: BoundingBox
    kind: Literal["text", "figure", "noise"]
    ink_pixels: int
    fill_ratio: float


@dataclass(frozen=True)
class CandidateProblemRegion:
    region_id: str
    index: int
    label: str
    bbox: BoundingBox
    normalized_bbox: tuple[float, float, float, float]
    has_figure: bool
    text_block_count: int
    figure_block_count: int
    completeness_confidence: float
    preview_data_url: str


@dataclass(frozen=True)
class ImageQualityReport:
    mean_luma: float
    p5_luma: int
    p95_luma: int
    dynamic_range: int
    edge_energy: float
    is_low_light: bool
    is_blank_or_unreadable: bool
    enhanced_low_light: bool


@dataclass(frozen=True)
class RegionDetectionResult:
    """Kết quả phân tích vùng đề trên ảnh đã chuẩn hóa hướng."""

    full_image: NormalizedImage
    prepared_image: NormalizedImage
    quality: ImageQualityReport
    page_bbox: BoundingBox
    desk_trimmed: bool
    skew_angle_deg: float
    deskew_applied: bool
    blocks: tuple[LayoutBlock, ...]
    candidates: tuple[CandidateProblemRegion, ...]
    selected_bbox: BoundingBox
    used_crop: bool
    used_fallback_full_image: bool
    has_associated_figure: bool
    completeness_confidence: float
    ambiguous_multi_problem: bool


def _encode_rgb_to_normalized(
    rgb: Image.Image,
    base_meta: NormalizedImage,
    *,
    quality: int = JPEG_QUALITY,
) -> NormalizedImage:
    work = rgb.convert("RGB")
    downscaled = base_meta.downscaled
    if max(work.size) > MAX_SEND_SIDE:
        work = work.copy()
        work.thumbnail((MAX_SEND_SIDE, MAX_SEND_SIDE), Image.Resampling.LANCZOS)
        downscaled = True
    raw_pixels = work.tobytes()
    clean = Image.frombytes("RGB", work.size, raw_pixels)
    sha = hashlib.sha256(b"RGB:%dx%d:" % clean.size + raw_pixels).hexdigest()
    buf = io.BytesIO()
    clean.save(buf, format="JPEG", quality=quality)
    return NormalizedImage(
        data=buf.getvalue(),
        mime_type="image/jpeg",
        sha256=sha,
        width=clean.size[0],
        height=clean.size[1],
        source_mime=base_meta.source_mime,
        exif_orientation=base_meta.exif_orientation,
        rotation_applied=base_meta.rotation_applied,
        downscaled=downscaled,
        source_had_exif=base_meta.source_had_exif,
        source_had_gps=base_meta.source_had_gps,
    )


def _make_preview_data_url(rgb: Image.Image, bbox: BoundingBox, max_side: int = 360) -> str:
    crop = rgb.crop((bbox.x0, bbox.y0, bbox.x1, bbox.y1))
    if max(crop.size) > max_side:
        crop.thumbnail((max_side, max_side), Image.Resampling.BILINEAR)
    buf = io.BytesIO()
    crop.save(buf, format="JPEG", quality=76)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _histogram_percentile(hist: list[int], total: int, pct: float) -> int:
    if total <= 0:
        return 0
    target = total * pct
    acc = 0
    for idx, count in enumerate(hist):
        acc += count
        if acc >= target:
            return idx
    return 255


def assess_and_enhance_image(rgb: Image.Image) -> tuple[Image.Image, ImageQualityReport]:
    """Đánh giá chất lượng sáng/nét và nâng sáng nhẹ khi ảnh chụp thiếu sáng."""
    w, h = rgb.size
    sample = rgb
    if max(w, h) > 640:
        sample = rgb.copy()
        sample.thumbnail((640, 640), Image.Resampling.BILINEAR)
    gray = ImageOps.grayscale(sample)
    hist = gray.histogram()
    total = sample.size[0] * sample.size[1]
    mean_luma = ImageStat.Stat(gray).mean[0] if total > 0 else 0.0
    p5 = _histogram_percentile(hist, total, 0.05)
    p95 = _histogram_percentile(hist, total, 0.95)
    dyn = max(0, p95 - p5)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_energy = ImageStat.Stat(edges).mean[0] if total > 0 else 0.0

    is_blank = dyn < 12 and edge_energy < 1.8
    is_low_light = (mean_luma < 108.0 or p95 < 175) and not is_blank

    enhanced = False
    out_rgb = rgb
    if is_low_light and dyn >= 14:
        stretched = ImageOps.autocontrast(rgb, cutoff=(0.4, 0.4))
        # Nâng gamma nhẹ (0.82) để kéo nền giấy tối lên sáng rõ mà giữ nguyên nét mực đậm.
        lut = [min(255, int(round(((i / 255.0) ** 0.82) * 255.0))) for i in range(256)]
        out_rgb = stretched.point(lut * 3)
        enhanced = True

    return out_rgb, ImageQualityReport(
        mean_luma=round(mean_luma, 2),
        p5_luma=p5,
        p95_luma=p95,
        dynamic_range=dyn,
        edge_energy=round(edge_energy, 2),
        is_low_light=is_low_light,
        is_blank_or_unreadable=is_blank,
        enhanced_low_light=enhanced,
    )


def detect_page_boundary(rgb: Image.Image) -> tuple[BoundingBox, bool]:
    """Tách vùng trang sách/giấy sáng khỏi nền bàn học tối hoặc có màu đậm ở rìa ảnh."""
    w, h = rgb.size
    full = BoundingBox(0, 0, w, h)
    if w < 120 or h < 120:
        return full, False

    gw = min(200, w)
    gh = max(32, int(round(h * (gw / w))))
    small_hsv = rgb.resize((gw, gh), Image.Resampling.BILINEAR).convert("HSV")
    _, s_ch, v_ch = small_hsv.split()
    s_bytes = s_ch.tobytes()
    v_bytes = v_ch.tobytes()

    border_x = max(2, gw // 18)
    border_y = max(2, gh // 18)
    border_v: list[int] = []
    border_s: list[int] = []
    inner_v: list[int] = []
    inner_s: list[int] = []

    cx0, cx1 = gw // 4, (gw * 3) // 4
    cy0, cy1 = gh // 4, (gh * 3) // 4

    for y in range(gh):
        row = y * gw
        on_y_border = y < border_y or y >= gh - border_y
        in_y_center = cy0 <= y < cy1
        for x in range(gw):
            idx = row + x
            sv = s_bytes[idx]
            vv = v_bytes[idx]
            if on_y_border or x < border_x or x >= gw - border_x:
                border_v.append(vv)
                border_s.append(sv)
            elif in_y_center and cx0 <= x < cx1:
                inner_v.append(vv)
                inner_s.append(sv)

    if not border_v or not inner_v:
        return full, False

    border_v.sort()
    border_s.sort()
    inner_v.sort()
    inner_s.sort()

    b_v_med = border_v[len(border_v) // 2]
    b_s_med = border_s[len(border_s) // 2]
    i_v_p75 = inner_v[(len(inner_v) * 3) // 4]
    i_s_med = inner_s[len(inner_s) // 2]

    darker_desk = b_v_med + 28 < i_v_p75
    colored_desk = b_s_med > i_s_med + 32 and b_s_med > 42
    if not (darker_desk or colored_desk):
        return full, False

    v_thresh = max(95, int((b_v_med + i_v_p75) * 0.52)) if darker_desk else max(110, i_v_p75 - 55)
    s_thresh = min(140, max(65, int((b_s_med + i_s_med) * 0.55))) if colored_desk else 175

    # Tìm thành phần liên thông lớn nhất của mặt giấy để không lấy nhầm vật sáng lẻ ở góc bàn.
    paper_mask = bytearray(gw * gh)
    for idx in range(gw * gh):
        if v_bytes[idx] >= v_thresh and s_bytes[idx] <= s_thresh:
            paper_mask[idx] = 1

    visited = bytearray(gw * gh)
    best_count = 0
    best_box: tuple[int, int, int, int] | None = None

    for start in range(gw * gh):
        if not paper_mask[start] or visited[start]:
            continue
        visited[start] = 1
        stack = [start]
        count = 0
        min_x, min_y = gw, gh
        max_x, max_y = 0, 0
        while stack:
            cur = stack.pop()
            count += 1
            cy, cx = divmod(cur, gw)
            if cx < min_x:
                min_x = cx
            if cx > max_x:
                max_x = cx
            if cy < min_y:
                min_y = cy
            if cy > max_y:
                max_y = cy
            if cx > 0 and paper_mask[cur - 1] and not visited[cur - 1]:
                visited[cur - 1] = 1
                stack.append(cur - 1)
            if cx + 1 < gw and paper_mask[cur + 1] and not visited[cur + 1]:
                visited[cur + 1] = 1
                stack.append(cur + 1)
            if cy > 0 and paper_mask[cur - gw] and not visited[cur - gw]:
                visited[cur - gw] = 1
                stack.append(cur - gw)
            if cy + 1 < gh and paper_mask[cur + gw] and not visited[cur + gw]:
                visited[cur + gw] = 1
                stack.append(cur + gw)
        if count > best_count:
            best_count = count
            best_box = (min_x, min_y, max_x + 1, max_y + 1)

    if best_box is None:
        return full, False

    bx0, by0, bx1, by1 = best_box
    box_area_ratio = ((bx1 - bx0) * (by1 - by0)) / float(gw * gh)
    # Trang giấy hợp lệ phải chiếm diện tích đáng kể (16%..90%) mới cắt bỏ nền bàn.
    if box_area_ratio < 0.16 or box_area_ratio > 0.90:
        return full, False

    sx = w / float(gw)
    sy = h / float(gh)
    raw_page = BoundingBox(
        int(math.floor(bx0 * sx)),
        int(math.floor(by0 * sy)),
        int(math.ceil(bx1 * sx)),
        int(math.ceil(by1 * sy)),
    )
    # Co nhẹ vào trong 1% để bỏ mép bóng đổ gập trang, hoặc đệm nhẹ nếu sát lề chữ.
    inset_x = max(2, int(round(raw_page.width * 0.008)))
    inset_y = max(2, int(round(raw_page.height * 0.008)))
    trimmed = BoundingBox(
        min(raw_page.x1 - 1, raw_page.x0 + inset_x),
        min(raw_page.y1 - 1, raw_page.y0 + inset_y),
        max(raw_page.x0 + 1, raw_page.x1 - inset_x),
        max(raw_page.y0 + 1, raw_page.y1 - inset_y),
    )
    if trimmed.width < 80 or trimmed.height < 80:
        return full, False
    return trimmed, True


def _adaptive_ink_image(rgb: Image.Image, max_side: int = 720) -> tuple[Image.Image, float, float]:
    """Ảnh nhị phân mực đen trên nền sáng (255 = có mực, 0 = nền) thích nghi theo vùng cục bộ."""
    w, h = rgb.size
    work = ImageOps.grayscale(rgb)
    if max(w, h) > max_side:
        scale = max_side / float(max(w, h))
        nw = max(16, int(round(w * scale)))
        nh = max(16, int(round(h * scale)))
        work = work.resize((nw, nh), Image.Resampling.BILINEAR)
    blur_radius = max(8, min(22, max(work.size) // 32))
    local_bg = work.filter(ImageFilter.BoxBlur(blur_radius))
    diff = ImageChops.subtract(local_bg, work)
    ink = diff.point(lambda p: 255 if p >= 20 else 0)
    return ink, w / float(work.size[0]), h / float(work.size[1])


def _projection_variance(ink_small: Image.Image, angle_deg: float) -> float:
    rot = (
        ink_small
        if abs(angle_deg) < 1e-4
        else ink_small.rotate(
            -angle_deg,
            resample=Image.Resampling.BILINEAR,
            expand=False,
            fillcolor=0,
        )
    )
    h = rot.size[1]
    if h <= 2:
        return 0.0
    row_means = rot.resize((1, h), Image.Resampling.BOX).tobytes()
    diffs = [abs(row_means[i] - row_means[i - 1]) for i in range(1, h)]
    mean_d = sum(diffs) / float(len(diffs))
    return sum((d - mean_d) ** 2 for d in diffs) / float(len(diffs))


def _count_text_bands(ink_small: Image.Image, angle_deg: float) -> int:
    rot = (
        ink_small
        if abs(angle_deg) < 1e-4
        else ink_small.rotate(
            -angle_deg,
            resample=Image.Resampling.BILINEAR,
            expand=False,
            fillcolor=0,
        )
    )
    h = rot.size[1]
    if h <= 4:
        return 0
    row_means = rot.resize((1, h), Image.Resampling.BOX).tobytes()
    active_thresh = 8
    bands = 0
    in_band = False
    gap_len = 0
    for val in row_means:
        if val >= active_thresh:
            if not in_band:
                bands += 1
                in_band = True
            gap_len = 0
        else:
            gap_len += 1
            if gap_len >= 2:
                in_band = False
    return bands


def estimate_and_correct_skew(rgb: Image.Image) -> tuple[Image.Image, float, bool]:
    """Phát hiện ảnh nghiêng và xoay thẳng khi phương sai chiếu dòng tăng rõ rệt."""
    w, h = rgb.size
    if w < 140 or h < 140:
        return rgb, 0.0, False

    ink, _, _ = _adaptive_ink_image(rgb, max_side=360)
    ink_ratio = ImageStat.Stat(ink).mean[0] / 255.0
    if ink_ratio < 0.002 or ink_ratio > 0.45:
        return rgb, 0.0, False

    var_zero = _projection_variance(ink, 0.0)
    if var_zero <= 1e-6:
        return rgb, 0.0, False

    best_angle = 0.0
    best_var = var_zero
    for step in range(-8, 9):
        ang = step * 2.0
        if ang == 0.0:
            continue
        v = _projection_variance(ink, ang)
        if v > best_var:
            best_var = v
            best_angle = ang

    fine_center = best_angle
    for step in range(-4, 5):
        ang = round(fine_center + step * 0.4, 2)
        if abs(ang) > 17.0:
            continue
        v = _projection_variance(ink, ang)
        if v > best_var:
            best_var = v
            best_angle = ang

    # Chỉ xoay khi góc nghiêng >= 1.2°, độ sắc nét dòng tăng >= 18% VÀ có >= 3 dải dòng chữ nằm ngang
    # để tuyệt đối không xoay nhầm cạnh xiên của hình chóp/tam giác đơn lẻ (vd: ảnh chỉ có hình vẽ).
    if abs(best_angle) < 1.2 or best_var < var_zero * 1.18:
        return rgb, 0.0, False
    if _count_text_bands(ink, best_angle) < 3:
        return rgb, 0.0, False

    corrected = rgb.rotate(
        -best_angle,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor=(255, 255, 255),
    )
    return corrected, round(best_angle, 2), True


def _segment_layout_blocks(rgb: Image.Image) -> tuple[list[LayoutBlock], Image.Image, float, float]:
    """Tách các khối nội dung (chữ, hình vẽ, nhiễu rìa) từ mặt nạ mực nhị phân."""
    w, h = rgb.size
    ink, sx, sy = _adaptive_ink_image(rgb, max_side=640)
    iw, ih = ink.size
    ink_bytes = ink.tobytes()

    # Lưới ô thô (~4x4 pixel trên ảnh ink) nối các ký tự gần nhau trên cùng từ/công thức/nét hình.
    cell_x = max(3, iw // 130)
    cell_y = max(3, ih // 160)
    gw = max(1, (iw + cell_x - 1) // cell_x)
    gh = max(1, (ih + cell_y - 1) // cell_y)

    grid = bytearray(gw * gh)
    cell_ink = [0] * (gw * gh)

    for y in range(ih):
        gy = y // cell_y
        row_off = y * iw
        g_row = gy * gw
        for x in range(iw):
            if ink_bytes[row_off + x]:
                gi = g_row + (x // cell_x)
                grid[gi] = 1
                cell_ink[gi] += 1

    # Nối ngang nhẹ 1 ô cho các từ cùng dòng mà không nối dọc qua khoảng trắng giữa hai bài toán.
    bridged = bytearray(grid)
    for gy in range(gh):
        g_row = gy * gw
        for gx in range(1, gw - 1):
            idx = g_row + gx
            if not grid[idx] and grid[idx - 1] and grid[idx + 1]:
                bridged[idx] = 1

    visited = bytearray(gw * gh)
    raw_blocks: list[LayoutBlock] = []
    page_area = float(w * h)

    for start in range(gw * gh):
        if not bridged[start] or visited[start]:
            continue
        visited[start] = 1
        stack = [start]
        min_gx, min_gy = gw, gh
        max_gx, max_gy = 0, 0
        ink_sum = 0
        active_cells = 0

        while stack:
            cur = stack.pop()
            ink_sum += cell_ink[cur]
            if grid[cur]:
                active_cells += 1
            cy, cx = divmod(cur, gw)
            if cx < min_gx:
                min_gx = cx
            if cx > max_gx:
                max_gx = cx
            if cy < min_gy:
                min_gy = cy
            if cy > max_gy:
                max_gy = cy
            for ny in range(max(0, cy - 1), min(gh, cy + 2)):
                for nx in range(max(0, cx - 1), min(gw, cx + 2)):
                    ni = ny * gw + nx
                    if bridged[ni] and not visited[ni]:
                        visited[ni] = 1
                        stack.append(ni)

        if ink_sum < 3:
            continue

        px0 = max(0, int(math.floor(min_gx * cell_x * sx)))
        py0 = max(0, int(math.floor(min_gy * cell_y * sy)))
        px1 = min(w, int(math.ceil(min(iw, (max_gx + 1) * cell_x) * sx)))
        py1 = min(h, int(math.ceil(min(ih, (max_gy + 1) * cell_y) * sy)))
        bbox = BoundingBox(px0, py0, px1, py1)
        if bbox.width <= 1 or bbox.height <= 1:
            continue

        span_cells = max(1, (max_gx - min_gx + 1) * (max_gy - min_gy + 1))
        cell_fill = active_cells / float(span_cells)
        rel_w = bbox.width / float(w)
        rel_h = bbox.height / float(h)
        rel_y0 = bbox.y0 / float(h)
        rel_y1 = bbox.y1 / float(h)
        rel_x0 = bbox.x0 / float(w)
        rel_x1 = bbox.x1 / float(w)
        area_frac = bbox.area / page_area

        # Nhận diện nhiễu rìa: vết bẩn cực nhỏ, đường gáy sách sát mép trái/phải, viền khung trang bao trọn ảnh,
        # hoặc số trang đơn lẻ sát mép trên/dưới.
        aspect = bbox.width / float(max(1, bbox.height))
        is_speck = area_frac < 0.00025 and ink_sum < 10
        is_book_spine = (rel_x1 <= 0.035 or rel_x0 >= 0.965) and rel_w <= 0.035
        is_page_frame = rel_w >= 0.94 and rel_h >= 0.94 and cell_fill < 0.18
        is_edge_artifact = (
            ((rel_y1 >= 0.985 and rel_y0 >= 0.86) or (rel_y0 <= 0.015 and rel_y1 <= 0.14))
            and (rel_x0 <= 0.02 or rel_x1 >= 0.98)
            and rel_w >= 0.80
        )
        is_lone_page_num = (rel_y1 <= 0.045 or rel_y0 >= 0.955) and rel_h <= 0.032 and rel_w <= 0.18
        if is_speck or is_book_spine or is_page_frame or is_edge_artifact or is_lone_page_num:
            kind: Literal["text", "figure", "noise"] = "noise"
        elif (
            rel_h >= 0.095
            and bbox.height >= 48
            and aspect <= 4.0
            and (cell_fill < 0.38 or (rel_w < 0.55 and rel_h > rel_w * 0.52 and cell_fill < 0.48))
        ):
            kind = "figure"
        else:
            kind = "text"

        raw_blocks.append(
            LayoutBlock(
                bbox=bbox,
                kind=kind,
                ink_pixels=ink_sum,
                fill_ratio=round(cell_fill, 4),
            )
        )

    # Bảo toàn ký hiệu toán học nhỏ & nhãn đỉnh (`A`, `A′`, `S`, `α`, `⊥`):
    # Mọi mảnh chữ nhỏ nằm gần một hình vẽ (<= 4.5% kích thước trang) được gom trực tiếp vào khung hình vẽ đó!
    figures = [b for b in raw_blocks if b.kind == "figure"]
    others = [b for b in raw_blocks if b.kind != "figure"]
    if figures:
        prox_x = max(10, int(round(w * 0.045)))
        prox_y = max(10, int(round(h * 0.045)))
        merged_figs = list(figures)
        kept_others: list[LayoutBlock] = []
        for b in others:
            is_small_label = b.bbox.width <= w * 0.09 and b.bbox.height <= h * 0.06
            attached = False
            if is_small_label:
                for idx, fig in enumerate(merged_figs):
                    expanded = fig.bbox.pad(prox_x, prox_y, w, h)
                    if not (
                        b.bbox.x1 < expanded.x0
                        or b.bbox.x0 > expanded.x1
                        or b.bbox.y1 < expanded.y0
                        or b.bbox.y0 > expanded.y1
                    ):
                        merged_figs[idx] = LayoutBlock(
                            bbox=fig.bbox.union(b.bbox),
                            kind="figure",
                            ink_pixels=fig.ink_pixels + b.ink_pixels,
                            fill_ratio=fig.fill_ratio,
                        )
                        attached = True
                        break
            if not attached:
                kept_others.append(b)
        raw_blocks = kept_others + merged_figs

    return raw_blocks, ink, sx, sy


def _expand_to_clear_ink_border(
    bbox: BoundingBox,
    ink: Image.Image,
    sx: float,
    sy: float,
    max_w: int,
    max_h: int,
) -> BoundingBox:
    """Đảm bảo đường biên crop không cắt ngang qua bất kỳ nét chữ/hình nào."""
    iw, ih = ink.size
    ink_bytes = ink.tobytes()
    cur = bbox

    for _ in range(4):
        ix0 = max(0, min(iw - 1, int(round(cur.x0 / sx))))
        iy0 = max(0, min(ih - 1, int(round(cur.y0 / sy))))
        ix1 = max(0, min(iw - 1, int(round((cur.x1 - 1) / sx))))
        iy1 = max(0, min(ih - 1, int(round((cur.y1 - 1) / sy))))

        touch_top = cur.y0 > 0 and any(ink_bytes[iy0 * iw + x] for x in range(ix0, ix1 + 1))
        touch_bot = cur.y1 < max_h and any(ink_bytes[iy1 * iw + x] for x in range(ix0, ix1 + 1))
        touch_left = cur.x0 > 0 and any(ink_bytes[y * iw + ix0] for y in range(iy0, iy1 + 1))
        touch_right = cur.x1 < max_w and any(ink_bytes[y * iw + ix1] for y in range(iy0, iy1 + 1))

        if not (touch_top or touch_bot or touch_left or touch_right):
            break

        step_x = max(8, int(round(max_w * 0.02)))
        step_y = max(8, int(round(max_h * 0.02)))
        cur = BoundingBox(
            max(0, cur.x0 - (step_x if touch_left else 0)),
            max(0, cur.y0 - (step_y if touch_top else 0)),
            min(max_w, cur.x1 + (step_x if touch_right else 0)),
            min(max_h, cur.y1 + (step_y if touch_bot else 0)),
        )
    return cur


def _group_problem_clusters(
    blocks: list[LayoutBlock],
    img_w: int,
    img_h: int,
) -> list[tuple[BoundingBox, list[LayoutBlock], list[LayoutBlock]]]:
    """Gom các dòng chữ và hình vẽ liên quan thành từng vùng bài toán ứng viên."""
    text_blocks = sorted(
        [b for b in blocks if b.kind == "text"],
        key=lambda b: (b.bbox.y0, b.bbox.x0),
    )
    fig_blocks = sorted(
        [b for b in blocks if b.kind == "figure"],
        key=lambda b: (b.bbox.y0, b.bbox.x0),
    )

    if not text_blocks and not fig_blocks:
        return []

    if not text_blocks:
        union_fig = fig_blocks[0].bbox
        for fb in fig_blocks[1:]:
            union_fig = union_fig.union(fb.bbox)
        return [(union_fig, [], fig_blocks)]

    # Nhóm các khối chữ theo khoảng cách dọc; khoảng trống dọc >= 6.5% chiều cao ảnh giữa hai
    # cụm chữ đủ rộng (>= 22% bề ngang trang) báo hiệu ranh giới giữa các bài độc lập.
    line_gap_thresh = max(14, int(round(img_h * 0.058)))
    raw_clusters: list[tuple[BoundingBox, list[LayoutBlock]]] = []

    for tb in text_blocks:
        if not raw_clusters:
            raw_clusters.append((tb.bbox, [tb]))
            continue
        prev_box, prev_list = raw_clusters[-1]
        v_gap = tb.bbox.y0 - prev_box.y1
        if v_gap <= line_gap_thresh:
            raw_clusters[-1] = (prev_box.union(tb.bbox), prev_list + [tb])
        else:
            raw_clusters.append((tb.bbox, [tb]))

    # Gộp cụm tiêu đề/dòng lẻ quá hẹp vào cụm bài liền kề để tránh tách tiêu đề khỏi thân đề;
    # đồng thời lọc tiêu đề đầu trang sách (nằm sát mép trên y0 < 8%, cách xa thân bài > 8% chiều cao).
    filtered_clusters: list[tuple[BoundingBox, list[LayoutBlock]]] = []
    for idx, (cbox, clist) in enumerate(raw_clusters):
        is_running_header = (
            idx == 0
            and len(raw_clusters) > 1
            and cbox.y1 <= img_h * 0.11
            and cbox.height <= img_h * 0.045
            and (raw_clusters[1][0].y0 - cbox.y1) >= img_h * 0.065
        )
        is_running_footer = (
            idx == len(raw_clusters) - 1
            and len(raw_clusters) > 1
            and cbox.y0 >= img_h * 0.89
            and cbox.height <= img_h * 0.045
            and (cbox.y0 - raw_clusters[-2][0].y1) >= img_h * 0.065
        )
        if is_running_header or is_running_footer:
            continue
        filtered_clusters.append((cbox, clist))

    if not filtered_clusters:
        filtered_clusters = raw_clusters

    merged_clusters: list[tuple[BoundingBox, list[LayoutBlock], list[LayoutBlock]]] = []
    min_problem_width = img_w * 0.24
    min_problem_height = img_h * 0.032

    for cbox, clist in filtered_clusters:
        if not merged_clusters:
            merged_clusters.append((cbox, list(clist), []))
            continue
        prev_box, prev_texts, prev_figs = merged_clusters[-1]
        prev_substantial = prev_box.width >= min_problem_width and prev_box.height >= min_problem_height
        cur_substantial = cbox.width >= min_problem_width and cbox.height >= min_problem_height
        v_gap = cbox.y0 - prev_box.y1
        # Chỉ tách thành 2 bài độc lập khi cả 2 cụm đều là thân đề thực sự và ngăn cách rõ (>= 6.5% trang).
        if prev_substantial and cur_substantial and v_gap >= max(18, int(round(img_h * 0.065))):
            merged_clusters.append((cbox, list(clist), []))
        else:
            merged_clusters[-1] = (prev_box.union(cbox), prev_texts + list(clist), prev_figs)

    # Ghép từng khối hình vẽ (figure) vào cụm chữ liên quan (nằm ngang bên cạnh hoặc ngay bên dưới/trên).
    for fb in fig_blocks:
        best_idx = 0
        best_score = float("inf")
        f_cy = (fb.bbox.y0 + fb.bbox.y1) * 0.5
        for idx, (cbox, _, _) in enumerate(merged_clusters):
            overlap_y = min(fb.bbox.y1, cbox.y1) - max(fb.bbox.y0, cbox.y0)
            if overlap_y > 0:
                # Hình nằm ngang hàng với đoạn chữ (kể cả cách xa sang cột phải — Case 4!)
                c_cy = (cbox.y0 + cbox.y1) * 0.5
                score = abs(f_cy - c_cy) * 0.25
            elif fb.bbox.y0 >= cbox.y1:
                # Hình nằm bên dưới đoạn đề vừa nêu (ưu tiên gắn với đề phía trên nó)
                score = (fb.bbox.y0 - cbox.y1) * 1.0
            else:
                # Hình nằm phía trên đoạn chữ
                score = (cbox.y0 - fb.bbox.y1) * 1.35
            if score < best_score:
                best_score = score
                best_idx = idx

        cbox, ctexts, cfigs = merged_clusters[best_idx]
        merged_clusters[best_idx] = (cbox.union(fb.bbox), ctexts, cfigs + [fb])

    return merged_clusters


def detect_problem_regions(
    normalized: NormalizedImage,
    *,
    target_problem_index: int | None = None,
    selected_region_id: str | None = None,
) -> RegionDetectionResult:
    """Chạy toàn bộ pipeline CV nhẹ trên `NormalizedImage` đã chuẩn hóa EXIF."""
    orig_rgb = Image.open(io.BytesIO(normalized.data)).convert("RGB")
    orig_w, orig_h = orig_rgb.size

    enhanced_rgb, quality = assess_and_enhance_image(orig_rgb)

    if quality.is_blank_or_unreadable:
        full_box = BoundingBox(0, 0, orig_w, orig_h)
        return RegionDetectionResult(
            full_image=normalized,
            prepared_image=normalized,
            quality=quality,
            page_bbox=full_box,
            desk_trimmed=False,
            skew_angle_deg=0.0,
            deskew_applied=False,
            blocks=(),
            candidates=(),
            selected_bbox=full_box,
            used_crop=False,
            used_fallback_full_image=True,
            has_associated_figure=False,
            completeness_confidence=0.0,
            ambiguous_multi_problem=False,
        )

    page_bbox, desk_trimmed = detect_page_boundary(enhanced_rgb)
    working_rgb = (
        enhanced_rgb.crop((page_bbox.x0, page_bbox.y0, page_bbox.x1, page_bbox.y1))
        if desk_trimmed
        else enhanced_rgb
    )

    pre_blocks, _, _, _ = _segment_layout_blocks(working_rgb)
    has_text_for_skew = sum(b.ink_pixels for b in pre_blocks if b.kind == "text") >= 350
    if has_text_for_skew:
        working_rgb, skew_angle, deskew_applied = estimate_and_correct_skew(working_rgb)
    else:
        skew_angle, deskew_applied = 0.0, False
    work_w, work_h = working_rgb.size
    full_work_box = BoundingBox(0, 0, work_w, work_h)

    # Ảnh đầy đủ chưa cắt bất kỳ phần nào (chỉ nâng sáng nếu tối) — làm baseline đo lường
    # và là lưới an toàn cuối cùng khi fallback 1 lần (§13).
    full_orig_norm = (
        _encode_rgb_to_normalized(enhanced_rgb, normalized)
        if quality.enhanced_low_light
        else normalized
    )
    # Trang làm việc (đã tách nền bàn học / xoay thẳng khi tin cậy).
    page_work_norm = (
        _encode_rgb_to_normalized(working_rgb, normalized)
        if (quality.enhanced_low_light or desk_trimmed or deskew_applied)
        else normalized
    )

    def _to_orig_bbox(wbox: BoundingBox) -> BoundingBox:
        base_box = page_bbox if desk_trimmed else BoundingBox(0, 0, orig_w, orig_h)
        if deskew_applied and work_w > 0 and work_h > 0:
            rx0 = wbox.x0 / float(work_w)
            ry0 = wbox.y0 / float(work_h)
            rx1 = wbox.x1 / float(work_w)
            ry1 = wbox.y1 / float(work_h)
            return BoundingBox(
                max(0, int(round(base_box.x0 + rx0 * base_box.width))),
                max(0, int(round(base_box.y0 + ry0 * base_box.height))),
                min(orig_w, int(round(base_box.x0 + rx1 * base_box.width))),
                min(orig_h, int(round(base_box.y0 + ry1 * base_box.height))),
            )
        if desk_trimmed:
            return BoundingBox(
                page_bbox.x0 + wbox.x0,
                page_bbox.y0 + wbox.y0,
                page_bbox.x0 + wbox.x1,
                page_bbox.y0 + wbox.y1,
            )
        return wbox

    blocks, ink_mask, sx, sy = _segment_layout_blocks(working_rgb)
    meaningful = [b for b in blocks if b.kind != "noise"]
    total_meaningful_ink = sum(b.ink_pixels for b in meaningful)

    if not meaningful or total_meaningful_ink <= 0:
        return RegionDetectionResult(
            full_image=full_orig_norm,
            prepared_image=page_work_norm,
            quality=quality,
            page_bbox=page_bbox,
            desk_trimmed=desk_trimmed,
            skew_angle_deg=skew_angle,
            deskew_applied=deskew_applied,
            blocks=tuple(blocks),
            candidates=(),
            selected_bbox=_to_orig_bbox(full_work_box),
            used_crop=desk_trimmed,
            used_fallback_full_image=not desk_trimmed,
            has_associated_figure=False,
            completeness_confidence=0.5,
            ambiguous_multi_problem=False,
        )

    clusters = _group_problem_clusters(blocks, work_w, work_h)
    # Tổng lượng mực của các cụm bài thực sự (đã loại bỏ running header/footer ở rìa trang sách).
    cluster_blocks = [b for _, ctexts, cfigs in clusters for b in (*ctexts, *cfigs)]
    total_cluster_ink = sum(b.ink_pixels for b in cluster_blocks) or total_meaningful_ink
    pad_x = max(20, int(round(work_w * 0.04)))
    pad_y = max(20, int(round(work_h * 0.04)))

    candidates: list[CandidateProblemRegion] = []
    for idx, (cbox, ctexts, cfigs) in enumerate(clusters, start=1):
        padded = cbox.pad(pad_x, pad_y, work_w, work_h)
        safe_box = _expand_to_clear_ink_border(padded, ink_mask, sx, sy, work_w, work_h)
        cluster_ink = sum(b.ink_pixels for b in ctexts) + sum(b.ink_pixels for b in cfigs)
        conf = (
            min(0.98, 0.78 + 0.20 * (cluster_ink / float(max(1, total_cluster_ink))))
            if len(clusters) == 1
            else 0.88
        )
        pos_hint = (
            "phía trên"
            if idx == 1 and len(clusters) >= 2
            else ("phía dưới" if idx == len(clusters) and len(clusters) >= 2 else f"vị trí {idx}")
        )
        label = (
            "Vùng đề bài chính"
            if len(clusters) == 1
            else f"Vùng bài {idx} ({pos_hint}{' · kèm hình vẽ' if cfigs else ''})"
        )
        candidates.append(
            CandidateProblemRegion(
                region_id=f"region-{idx}",
                index=idx,
                label=label,
                bbox=safe_box,
                normalized_bbox=safe_box.normalized(work_w, work_h),
                has_figure=bool(cfigs),
                text_block_count=len(ctexts),
                figure_block_count=len(cfigs),
                completeness_confidence=round(conf, 3),
                preview_data_url=_make_preview_data_url(working_rgb, safe_box),
            )
        )

    # Chọn vùng đề theo chỉ dẫn người dùng hoặc phát hiện mơ hồ nhiều bài (§14).
    chosen: CandidateProblemRegion | None = None
    ambiguous = False

    if len(candidates) == 1:
        chosen = candidates[0]
    elif len(candidates) > 1:
        if selected_region_id:
            for c in candidates:
                if c.region_id == selected_region_id:
                    chosen = c
                    break
        elif target_problem_index is not None:
            if target_problem_index == -1:
                chosen = candidates[-1]
            elif 1 <= target_problem_index <= len(candidates):
                chosen = candidates[target_problem_index - 1]
            else:
                ambiguous = True
        else:
            ambiguous = True

    if ambiguous or chosen is None:
        any_fig = any(c.has_figure for c in candidates)
        return RegionDetectionResult(
            full_image=full_orig_norm,
            prepared_image=page_work_norm,
            quality=quality,
            page_bbox=page_bbox,
            desk_trimmed=desk_trimmed,
            skew_angle_deg=skew_angle,
            deskew_applied=deskew_applied,
            blocks=tuple(blocks),
            candidates=tuple(candidates),
            selected_bbox=_to_orig_bbox(full_work_box),
            used_crop=desk_trimmed,
            used_fallback_full_image=True,
            has_associated_figure=any_fig,
            completeness_confidence=0.85,
            ambiguous_multi_problem=ambiguous,
        )

    # Bảo toàn dữ kiện toán học (§13): nếu chỉ có 1 bài mà diện tích crop tiết kiệm < 15%
    # hoặc độ phủ mực có ích < 96% hoặc độ tin cậy < 0.78 => giữ toàn trang làm việc!
    selected_ink = sum(
        b.ink_pixels
        for b in (cluster_blocks or meaningful)
        if not (
            b.bbox.x1 < chosen.bbox.x0
            or b.bbox.x0 > chosen.bbox.x1
            or b.bbox.y1 < chosen.bbox.y0
            or b.bbox.y0 > chosen.bbox.y1
        )
    )
    ink_coverage = selected_ink / float(max(1, total_cluster_ink))
    area_ratio = chosen.bbox.area / float(max(1, work_w * work_h))

    if len(candidates) == 1 and (
        ink_coverage < 0.96
        or chosen.completeness_confidence < 0.78
        or area_ratio > 0.85
    ):
        return RegionDetectionResult(
            full_image=full_orig_norm,
            prepared_image=page_work_norm,
            quality=quality,
            page_bbox=page_bbox,
            desk_trimmed=desk_trimmed,
            skew_angle_deg=skew_angle,
            deskew_applied=deskew_applied,
            blocks=tuple(blocks),
            candidates=tuple(candidates),
            selected_bbox=_to_orig_bbox(full_work_box),
            used_crop=desk_trimmed,
            used_fallback_full_image=not desk_trimmed,
            has_associated_figure=chosen.has_figure,
            completeness_confidence=round(ink_coverage, 3),
            ambiguous_multi_problem=False,
        )

    cropped_rgb = working_rgb.crop((chosen.bbox.x0, chosen.bbox.y0, chosen.bbox.x1, chosen.bbox.y1))
    prepared_norm = _encode_rgb_to_normalized(cropped_rgb, normalized)

    return RegionDetectionResult(
        full_image=full_orig_norm,
        prepared_image=prepared_norm,
        quality=quality,
        page_bbox=page_bbox,
        desk_trimmed=desk_trimmed,
        skew_angle_deg=skew_angle,
        deskew_applied=deskew_applied,
        blocks=tuple(blocks),
        candidates=tuple(candidates),
        selected_bbox=_to_orig_bbox(chosen.bbox),
        used_crop=True,
        used_fallback_full_image=False,
        has_associated_figure=chosen.has_figure,
        completeness_confidence=chosen.completeness_confidence,
        ambiguous_multi_problem=False,
    )
