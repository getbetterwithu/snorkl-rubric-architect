#!/usr/bin/env python3
"""
snorkl_geometry_engine.py (v15.0 Safety & Precision Edition)
한국 중학교 수학 교과서(2022 개정 교육과정) 표준 기하 벡터 작도 엔진.

[표준 캔버스 및 좌표 규격]
- 전체 카드 캔버스: 1000 × 500 CSS px (2x 레티나 캡처 시 2000 × 1000 px)
- 오른쪽 기하 도형 영역(.geometry): 480 × 456 CSS px (`viewBox="0 0 480 456"` 권장)
- 꼭짓점 라벨 잘림 방지를 위해 모든 도형 꼭짓점은 상하좌우 최소 36px 안쪽([36..444] × [36..420])에 배치 권장.

[v15.0 핵심 무결성 보장]
1. line_intersection(): 평행·일치·퇴화 직선 입력 시 가짜 중점 반환을 금지하고 즉시 ValueError 발생.
2. interior_label_point(): 볼록다각형은 수학적 무게중심(polygon_centroid)을 사용하고,
   ㄱ자형 등 오목다각형에서 무게중심이 외부/경계 근접 시 Ray-casting 내부 최대 여유점(Visual Center)으로 자동 보정.
3. render_cloud_label(): 동아시아 전각 문자 폭(unicodedata) 정밀 계산 및 화이트 헤일로 마스킹 일원화.
4. 중학교 필수 도형 헬퍼 완비: 원(render_circle), 원호(render_arc), 점선(render_dashed_line),
   교과서 치수 원호(render_dimension_arc), 좌표평면(render_coord_axes), 꼭짓점 자동 외측 배치(direction="auto").
"""

from __future__ import annotations

import html
import math
import unicodedata
from typing import Sequence, Tuple

Point = Tuple[float, float]


def format_pt(p: Point) -> str:
    return f"{p[0]:.2f},{p[1]:.2f}"


def distance(p1: Point, p2: Point) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def midpoint(p1: Point, p2: Point, ratio: float = 0.5) -> Point:
    """p1에서 p2 방향으로 ratio 비율의 내분점(또는 외분점) 계산."""
    return (p1[0] + (p2[0] - p1[0]) * ratio, p1[1] + (p2[1] - p1[1]) * ratio)


def unit_vector(p1: Point, p2: Point) -> Point:
    d = distance(p1, p2)
    if d < 1e-12:
        return (0.0, 0.0)
    return ((p2[0] - p1[0]) / d, (p2[1] - p1[1]) / d)


def normal_vector(p1: Point, p2: Point) -> Point:
    """선분 p1->p2 진행 방향 기준 시계방향 90° 직교 단위벡터 `(-uy, ux)` (SVG y-down 좌표계)."""
    ux, uy = unit_vector(p1, p2)
    return (-uy, ux)


def right_normal_vector(p1: Point, p2: Point) -> Point:
    """선분 p1->p2 진행 방향 기준 반시계방향 90° 직교 단위벡터 `(uy, -ux)` (SVG y-down 좌표계)."""
    ux, uy = unit_vector(p1, p2)
    return (uy, -ux)


def outward_normal_vector(p1: Point, p2: Point, polygon_points: Sequence[Point]) -> Tuple[Point, int]:
    """
    다각형 변 (p1->p2)에서 다각형 바깥쪽을 향하는 직교 단위벡터와 SVG arc sweep 플래그를 자동 판별.
    반환값: `(normal_vec, sweep_flag)` — 원호가 p1->p2 바깥쪽으로 볼록하게 휘어지도록 보장.
    """
    mid = midpoint(p1, p2)
    n_cw = normal_vector(p1, p2)         # (-uy, ux) -> SVG arc sweep=0 bulges toward (-uy, ux)? Let's check exact SVG arc geometry!
    n_ccw = right_normal_vector(p1, p2)  # (uy, -ux)

    # Probe 3px along each normal to see which side is OUTSIDE the polygon
    probe_cw = (mid[0] + n_cw[0] * 3.0, mid[1] + n_cw[1] * 3.0)
    probe_ccw = (mid[0] + n_ccw[0] * 3.0, mid[1] + n_ccw[1] * 3.0)

    cw_inside = point_in_polygon(probe_cw, polygon_points)
    ccw_inside = point_in_polygon(probe_ccw, polygon_points)

    if not cw_inside and ccw_inside:
        # Outward direction is n_cw = (-uy, ux); minor arc from p1 to p2 bulges toward n_cw when sweep=0
        return n_cw, 0
    if not ccw_inside and cw_inside:
        # Outward direction is n_ccw = (uy, -ux); minor arc from p1 to p2 bulges toward n_ccw when sweep=1
        return n_ccw, 1

    # Fallback: compare distance from polygon centroid
    cx, cy = polygon_centroid(polygon_points)
    if distance(probe_cw, (cx, cy)) >= distance(probe_ccw, (cx, cy)):
        return n_cw, 0
    return n_ccw, 1


def estimate_text_width(text_str: str, font_size: float) -> float:
    """한글/전각 문자와 영문/숫자 폭 차이를 반영한 텍스트 픽셀 폭 추정."""
    total = 0.0
    for ch in text_str:
        if ch.isspace():
            total += font_size * 0.30
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            total += font_size * 0.94
        else:
            total += font_size * 0.58
    return max(total, font_size * 0.6)


def render_right_angle(
    vertex: Point,
    p1: Point,
    p2: Point,
    size: float = 13,
    stroke: str = "#1E293B",
    stroke_width: float = 1.8,
) -> str:
    """한국 교과서 표준 직각 표시 기호 사각형."""
    u1 = unit_vector(vertex, p1)
    u2 = unit_vector(vertex, p2)
    c1 = (vertex[0] + u1[0] * size, vertex[1] + u1[1] * size)
    c2 = (c1[0] + u2[0] * size, c1[1] + u2[1] * size)
    c3 = (vertex[0] + u2[0] * size, vertex[1] + u2[1] * size)
    return (
        f'<path d="M {format_pt(c1)} L {format_pt(c2)} L {format_pt(c3)}" '
        f'fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def render_parallel_arrow(
    p1: Point,
    p2: Point,
    count: int = 1,
    length: float = 14,
    width: float = 10,
    stroke: str = "#1E293B",
    fill: str = "#1E293B",
    ratio: float = 0.5,
) -> str:
    """한국 교과서 표준 평행 화살표 (count=1: ▶, count=2: ▶▶)."""
    mid = midpoint(p1, p2, ratio)
    ux, uy = unit_vector(p1, p2)
    nx, ny = normal_vector(p1, p2)

    if count == 2:
        offsets = [-length * 0.8, length * 0.8]
    elif count == 3:
        offsets = [-length * 1.6, 0.0, length * 1.6]
    else:
        offsets = [0.0]

    arrows = []
    for off in offsets:
        tip = (mid[0] + ux * off + ux * (length / 2), mid[1] + uy * off + uy * (length / 2))
        back_left = (tip[0] - ux * length + nx * (width / 2), tip[1] - uy * length + ny * (width / 2))
        back_right = (tip[0] - ux * length - nx * (width / 2), tip[1] - uy * length - ny * (width / 2))
        arrows.append(
            f'<polygon points="{format_pt(tip)} {format_pt(back_left)} {format_pt(back_right)}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
        )
    return "\n".join(arrows)


def render_tick_mark(
    p1: Point,
    p2: Point,
    count: int = 1,
    tick_len: float = 9,
    spacing: float = 3.5,
    stroke: str = "#1E293B",
    stroke_width: float = 1.8,
    ratio: float = 0.5,
) -> str:
    """선분 길이 같음 표시 틱 마크 (count=1: |, count=2: ||, count=3: |||)."""
    mid = midpoint(p1, p2, ratio)
    ux, uy = unit_vector(p1, p2)
    nx, ny = normal_vector(p1, p2)

    if count == 2:
        offsets = [-spacing / 2, spacing / 2]
    elif count == 3:
        offsets = [-spacing, 0.0, spacing]
    else:
        offsets = [0.0]

    ticks = []
    for off in offsets:
        center = (mid[0] + ux * off, mid[1] + uy * off)
        t1 = (center[0] + nx * (tick_len / 2), center[1] + ny * (tick_len / 2))
        t2 = (center[0] - nx * (tick_len / 2), center[1] - ny * (tick_len / 2))
        ticks.append(
            f'<line x1="{t1[0]:.2f}" y1="{t1[1]:.2f}" x2="{t2[0]:.2f}" y2="{t2[1]:.2f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round"/>'
        )
    return "\n".join(ticks)


def render_cloud_label(
    x: float,
    y: float,
    text_str: str,
    is_var: bool = False,
    font_size: float = 19,
    anchor: str = "middle",
) -> str:
    """
    점선·치수선을 깔끔하게 마스킹하는 불투명 화이트 헤일로 텍스트 라벨.
    한글/전각 문자 폭을 정확히 계산하여 배경 코어 박스와 paint-order 헤일로를 함께 렌더링.
    """
    w_approx = estimate_text_width(text_str, font_size) + 6.0
    h_approx = font_size * 0.92

    if anchor == "middle":
        rx = x - w_approx / 2.0
    elif anchor == "end":
        rx = x - w_approx
    else:
        rx = x
    ry = y - h_approx * 0.78

    has_cjk = any(unicodedata.east_asian_width(c) in ("W", "F") for c in text_str)
    font_family = (
        "-apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', 'Times New Roman', serif"
        if has_cjk
        else "'Times New Roman', Times, serif"
    )

    if is_var:
        parts = text_str.split(" ", 1)
        var_part = html.escape(parts[0])
        unit_part = (" " + html.escape(parts[1])) if len(parts) > 1 else ""
        content = f'<tspan font-style="italic">{var_part}</tspan>{unit_part}'
    else:
        content = html.escape(text_str)

    return (
        f'<g>\n'
        f'  <rect x="{rx:.1f}" y="{ry:.1f}" width="{w_approx:.1f}" height="{h_approx:.1f}" rx="4" fill="#FFFFFF"/>\n'
        f'  <text x="{x:.1f}" y="{y:.1f}" font-family="{font_family}" font-size="{font_size}" '
        f'font-weight="bold" fill="#0F172A" text-anchor="{anchor}" '
        f'style="paint-order: stroke fill; stroke: #FFFFFF; stroke-width: 9px; stroke-linejoin: round; stroke-linecap: round;">'
        f'{content}</text>\n'
        f'</g>'
    )


def render_angle_arc(
    vertex: Point,
    p1: Point,
    p2: Point,
    label: str | None = None,
    r: float = 20,
    stroke: str = "#1E293B",
    stroke_width: float = 1.6,
    label_color: str = "#0F172A",
    halo_color: str = "#FFFFFF",
    halo_width: float = 6,
    font_size: float = 16,
) -> str:
    """꼭짓점 중심 내각 원호 및 이등분선 방향 비간섭 각도 라벨."""
    theta1 = math.atan2(p1[1] - vertex[1], p1[0] - vertex[0])
    theta2 = math.atan2(p2[1] - vertex[1], p2[0] - vertex[0])
    diff = (theta2 - theta1 + math.pi) % (2 * math.pi) - math.pi
    alpha = abs(diff)

    s_x = vertex[0] + r * math.cos(theta1)
    s_y = vertex[1] + r * math.sin(theta1)
    e_x = vertex[0] + r * math.cos(theta2)
    e_y = vertex[1] + r * math.sin(theta2)

    sweep = 1 if diff > 0 else 0
    bisector = theta1 + diff / 2.0

    min_d_sides = 12.0 / math.sin(max(0.12, alpha / 2.0))
    min_d_arc = r + 13.0
    d_label = min(48.0, max(min_d_sides, min_d_arc))

    label_x = vertex[0] + d_label * math.cos(bisector)
    label_y = vertex[1] + d_label * math.sin(bisector)

    path_tag = (
        f'<path d="M {s_x:.2f},{s_y:.2f} A {r} {r} 0 0 {sweep} {e_x:.2f},{e_y:.2f}" '
        f'fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )
    if label:
        safe_label = html.escape(label)
        text_tag = (
            f'<text x="{label_x:.2f}" y="{label_y:.2f}" '
            f'font-family="-apple-system, BlinkMacSystemFont, \'Apple SD Gothic Neo\', \'Malgun Gothic\', \'Times New Roman\', sans-serif" '
            f'font-size="{font_size}" font-weight="bold" fill="{label_color}" '
            f'text-anchor="middle" dominant-baseline="central" '
            f'style="paint-order: stroke fill; stroke: {halo_color}; stroke-width: {halo_width}px; '
            f'stroke-linejoin: round; stroke-linecap: round;">{safe_label}</text>'
        )
        return f"{path_tag}\n{text_tag}"
    return path_tag


def render_vertex_label(
    point: Point,
    label: str,
    direction: str = "top",
    offset: float = 14,
    font_size: float = 25,
    color: str = "#1E293B",
    polygon_points: Sequence[Point] | None = None,
) -> str:
    """
    꼭짓점 로만체 볼드 라벨.
    direction="auto"와 polygon_points가 주어지면 다각형 중심 반대(외측) 방향으로 자동 이격 배치.
    """
    safe_label = html.escape(label)
    if direction == "auto" and polygon_points and len(polygon_points) >= 3:
        cx, cy = polygon_centroid(polygon_points)
        ux, uy = unit_vector((cx, cy), point)
        if abs(ux) < 1e-9 and abs(uy) < 1e-9:
            ux, uy = (0.0, -1.0)
        dist = offset + font_size * 0.35
        lx = point[0] + ux * dist
        ly = point[1] + uy * dist
        return (
            f'<text x="{lx:.2f}" y="{ly:.2f}" font-family="\'Times New Roman\', Times, serif" '
            f'font-weight="bold" font-size="{font_size}" fill="{color}" '
            f'text-anchor="middle" dominant-baseline="central">{safe_label}</text>'
        )

    dx, dy = 0.0, 0.0
    anchor = "middle"

    if direction == "top":
        dy = -offset
    elif direction == "bottom":
        dy = offset + font_size * 0.7
    elif direction == "left":
        dx = -offset
        dy = font_size * 0.35
        anchor = "end"
    elif direction == "right":
        dx = offset
        dy = font_size * 0.35
        anchor = "start"
    elif direction == "top-left":
        dx = -offset * 0.7
        dy = -offset * 0.7
        anchor = "end"
    elif direction == "top-right":
        dx = offset * 0.7
        dy = -offset * 0.7
        anchor = "start"
    elif direction == "bottom-left":
        dx = -offset * 0.7
        dy = offset * 0.7 + font_size * 0.4
        anchor = "end"
    elif direction == "bottom-right":
        dx = offset * 0.7
        dy = offset * 0.7 + font_size * 0.4
        anchor = "start"

    return (
        f'<text x="{point[0] + dx:.2f}" y="{point[1] + dy:.2f}" '
        f'font-family="\'Times New Roman\', Times, serif" font-weight="bold" '
        f'font-size="{font_size}" fill="{color}" text-anchor="{anchor}">{safe_label}</text>'
    )


def triangle_centroid(p1: Point, p2: Point, p3: Point) -> Point:
    """삼각형 세 꼭짓점의 수학적 무게중심 계산."""
    return ((p1[0] + p2[0] + p3[0]) / 3.0, (p1[1] + p2[1] + p3[1]) / 3.0)


def polygon_centroid(points: Sequence[Point]) -> Point:
    """임의의 단순 다각형의 면적 가중 무게중심(Green's Theorem / Shoelace) 계산."""
    n = len(points)
    if n == 0:
        return (0.0, 0.0)
    if n == 1:
        return points[0]
    if n == 2:
        return midpoint(points[0], points[1])
    if n == 3:
        return triangle_centroid(points[0], points[1], points[2])

    signed_area = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        signed_area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    signed_area *= 0.5
    if abs(signed_area) < 1e-6:
        return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n)

    cx /= 6.0 * signed_area
    cy /= 6.0 * signed_area
    return (cx, cy)


def point_to_segment_distance(pt: Point, a: Point, b: Point) -> float:
    """점 pt에서 선분 ab까지의 최단 거리."""
    px, py = pt
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    len_sq = dx * dx + dy * dy
    if len_sq < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / len_sq))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def point_in_polygon(pt: Point, points: Sequence[Point]) -> bool:
    """Ray-casting 알고리즘을 이용한 다각형 순수 내부 포함 여부 판별 (경계선 위는 False)."""
    n = len(points)
    if n < 3:
        return False
    x, y = pt
    for i in range(n):
        if point_to_segment_distance(pt, points[i], points[(i + 1) % n]) < 1e-7:
            return False

    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = points[i]
        xj, yj = points[j]
        intersects = ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) if abs(yj - yi) > 1e-12 else 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def polygon_min_clearance(pt: Point, points: Sequence[Point]) -> float:
    """점 pt에서 다각형의 모든 변까지의 최소 여유 거리."""
    n = len(points)
    if n < 2:
        return 0.0
    return min(point_to_segment_distance(pt, points[i], points[(i + 1) % n]) for i in range(n))


def interior_label_point(points: Sequence[Point], min_edge_clearance: float = 8.0) -> Point:
    """
    볼록다각형은 수학적 무게중심을 그대로 반환하고,
    오목다각형(ㄱ자형 등)에서 무게중심이 외부로 이탈하거나 변에 과도하게 붙을 경우
    다각형 내부에서 모든 변으로부터 가장 여유가 큰 시각적 중심점(Pole of Inaccessibility 근사)을 반환.
    """
    n = len(points)
    if n < 3:
        return polygon_centroid(points)

    centroid = polygon_centroid(points)
    if point_in_polygon(centroid, points) and polygon_min_clearance(centroid, points) >= min_edge_clearance:
        return centroid

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    best_pt: Point | None = centroid if point_in_polygon(centroid, points) else None
    best_dist = polygon_min_clearance(best_pt, points) if best_pt else -1.0

    steps = 24
    dx = (max_x - min_x) / steps if max_x > min_x else 1.0
    dy = (max_y - min_y) / steps if max_y > min_y else 1.0

    for ix in range(1, steps):
        for iy in range(1, steps):
            cand = (min_x + ix * dx, min_y + iy * dy)
            if point_in_polygon(cand, points):
                clr = polygon_min_clearance(cand, points)
                if clr > best_dist:
                    best_dist = clr
                    best_pt = cand

    # Local refinement around best grid candidate
    if best_pt is not None and max_x > min_x and max_y > min_y:
        sub_dx = dx / 4.0
        sub_dy = dy / 4.0
        cx0, cy0 = best_pt
        for sx in range(-3, 4):
            for sy in range(-3, 4):
                cand = (cx0 + sx * sub_dx, cy0 + sy * sub_dy)
                if point_in_polygon(cand, points):
                    clr = polygon_min_clearance(cand, points)
                    if clr > best_dist:
                        best_dist = clr
                        best_pt = cand
        return best_pt

    return centroid


def line_intersection(p1: Point, p2: Point, p3: Point, p4: Point) -> Point:
    """
    두 직선 (p1-p2)와 (p3-p4)의 유일한 수학적 교점 좌표를 계산.
    두 직선이 평행·일치하거나 퇴화(길이 0)된 경우 가짜 좌표를 반환하지 않고 즉시 ValueError를 발생시킨다.
    """
    if distance(p1, p2) < 1e-9 or distance(p3, p4) < 1e-9:
        raise ValueError("Degenerate line specification: endpoints of each line must be distinct.")

    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        raise ValueError(
            f"Lines ({p1}->{p2}) and ({p3}->{p4}) are parallel or collinear; unique intersection does not exist."
        )

    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


def render_shaded_region(
    points: Sequence[Point],
    fill: str = "#E0F2FE",
    stroke: str = "#38BDF8",
    stroke_width: float = 1.5,
    label: str | None = None,
    label_color: str = "#0369A1",
    font_size: float = 22,
    is_math: bool = True,
    halo_color: str = "#FFFFFF",
    halo_width: float = 5,
) -> str:
    """
    다각형 영역 음영 및 안전 내부 중심 라벨 안착 엔진.
    볼록다각형은 수학적 무게중심에, 오목다각형은 내부 안전 중심점(interior_label_point)에 라벨을 안착시킨다.
    """
    pts_str = " ".join(format_pt(p) for p in points)
    stroke_attr = (
        f'stroke="{stroke}" stroke-width="{stroke_width}"'
        if stroke and stroke.lower() != "none"
        else 'stroke="none"'
    )
    poly_tag = f'<polygon points="{pts_str}" fill="{fill}" {stroke_attr} stroke-linejoin="round"/>'

    if not label:
        return poly_tag

    cx, cy = interior_label_point(points)
    font_style = 'font-style="italic"' if is_math else ""
    safe_label = html.escape(label)
    text_tag = (
        f'<text x="{cx:.2f}" y="{cy:.2f}" '
        f'font-family="\'Times New Roman\', Times, serif" font-size="{font_size}" font-weight="bold" {font_style} '
        f'fill="{label_color}" text-anchor="middle" dominant-baseline="central" '
        f'style="paint-order: stroke fill; stroke: {halo_color}; stroke-width: {halo_width}px; '
        f'stroke-linejoin: round; stroke-linecap: round;">'
        f"{safe_label}</text>"
    )
    return f"{poly_tag}\n{text_tag}"


def render_dashed_line(
    p1: Point,
    p2: Point,
    stroke: str = "#475569",
    stroke_width: float = 1.6,
    dasharray: str = "6,4",
) -> str:
    """보조선, 수선, 이동 경로 등을 나타내는 교과서 표준 점선."""
    return (
        f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
        f'stroke="{stroke}" stroke-width="{stroke_width}" stroke-dasharray="{dasharray}" stroke-linecap="round"/>'
    )


def render_circle(
    center: Point,
    radius: float,
    stroke: str = "#1E293B",
    stroke_width: float = 2.0,
    fill: str = "none",
    show_center: bool = True,
    center_label: str | None = None,
    label_direction: str = "bottom-right",
) -> str:
    """중1 원과 부채꼴, 중3 원의 성질 단원용 표준 원 및 중심점 표시."""
    tags = [
        f'<circle cx="{center[0]:.2f}" cy="{center[1]:.2f}" r="{radius:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    ]
    if show_center:
        tags.append(f'<circle cx="{center[0]:.2f}" cy="{center[1]:.2f}" r="3.2" fill="{stroke}"/>')
    if center_label:
        tags.append(render_vertex_label(center, center_label, direction=label_direction, offset=10, font_size=22))
    return "\n".join(tags)


def render_arc(
    center: Point,
    radius: float,
    start_deg: float,
    end_deg: float,
    stroke: str = "#1E293B",
    stroke_width: float = 2.0,
    fill: str = "none",
    dashed: bool = False,
) -> str:
    """중심각(도 단위, 수학 표준 반시계 기준이 아닌 SVG 시계방향 각도 지원: 수학 표준 각도 반시계 기준 자동 변환) 원호 작도."""
    # Convert standard math degrees (0° = +x, 90° = -y upward on screen) to SVG coordinates
    s_rad = -math.radians(start_deg)
    e_rad = -math.radians(end_deg)
    sx = center[0] + radius * math.cos(s_rad)
    sy = center[1] + radius * math.sin(s_rad)
    ex = center[0] + radius * math.cos(e_rad)
    ey = center[1] + radius * math.sin(e_rad)

    span = (end_deg - start_deg) % 360.0
    if span == 0 and start_deg != end_deg:
        return render_circle(center, radius, stroke=stroke, stroke_width=stroke_width, fill=fill, show_center=False)
    large_arc = 1 if span > 180.0 else 0
    # Increasing math angle moves counter-clockwise on screen -> sweep=0 in SVG y-down
    dash_attr = ' stroke-dasharray="6,4"' if dashed else ""
    return (
        f'<path d="M {sx:.2f},{sy:.2f} A {radius:.2f} {radius:.2f} 0 {large_arc} 0 {ex:.2f},{ey:.2f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr}/>'
    )


def render_dimension_arc(
    p1: Point,
    p2: Point,
    label: str,
    side: str = "outward",
    sagitta: float = 20.0,
    is_var: bool = False,
    font_size: float = 18,
    stroke: str = "#64748B",
    polygon_points: Sequence[Point] | None = None,
) -> str:
    """
    선분 p1->p2에 한국 교과서식 점선 원호 치수선과 중앙 마스킹 라벨을 함께 작도.
    `polygon_points`가 주어지고 `side="outward"`(기본값)이면 다각형 바깥쪽으로 자동 볼록하게 작도한다.
    """
    chord = distance(p1, p2)
    if chord < 1e-6:
        raise ValueError("Cannot draw dimension arc on zero-length segment.")
    if side == "outward" and polygon_points and len(polygon_points) >= 3:
        (nx, ny), sweep = outward_normal_vector(p1, p2, polygon_points)
    elif side in ("ccw", "right"):
        nx, ny = right_normal_vector(p1, p2)
        sweep = 1
    else:
        nx, ny = normal_vector(p1, p2)
        sweep = 0

    # Ensure horizontal/slanted label box never touches the segment
    min_h_for_label = (estimate_text_width(label, font_size) * 0.5 + 8.0) * abs(nx)
    h = max(6.0, abs(sagitta), min_h_for_label)
    radius = (chord * chord) / (8.0 * h) + h / 2.0

    mid = midpoint(p1, p2)
    apex_x = mid[0] + nx * h
    apex_y = mid[1] + ny * h + font_size * 0.30
    arc_tag = (
        f'<path d="M {format_pt(p1)} A {radius:.2f} {radius:.2f} 0 0 {sweep} {format_pt(p2)}" '
        f'fill="none" stroke="{stroke}" stroke-width="1.4" stroke-dasharray="5,4"/>'
    )
    label_tag = render_cloud_label(apex_x, apex_y, label, is_var=is_var, font_size=font_size, anchor="middle")
    return f"{arc_tag}\n{label_tag}"


def render_coord_axes(
    origin: Point = (240.0, 228.0),
    x_range: Tuple[int, int] = (-5, 5),
    y_range: Tuple[int, int] = (-5, 5),
    scale: float = 34.0,
    show_grid: bool = False,
    stroke: str = "#1E293B",
) -> str:
    """중1~중3 함수·좌표평면 단원용 표준 x축, y축, 원점 O 및 화살표 작도."""
    ox, oy = origin
    x_min_px = ox + x_range[0] * scale - 16
    x_max_px = ox + x_range[1] * scale + 20
    y_min_px = oy - y_range[1] * scale - 20
    y_max_px = oy - y_range[0] * scale + 16

    elems = []
    if show_grid:
        for gx in range(x_range[0], x_range[1] + 1):
            if gx == 0:
                continue
            px = ox + gx * scale
            elems.append(
                f'<line x1="{px:.1f}" y1="{y_min_px + 12:.1f}" x2="{px:.1f}" y2="{y_max_px - 10:.1f}" '
                f'stroke="#E2E8F0" stroke-width="1"/>'
            )
        for gy in range(y_range[0], y_range[1] + 1):
            if gy == 0:
                continue
            py = oy - gy * scale
            elems.append(
                f'<line x1="{x_min_px + 10:.1f}" y1="{py:.1f}" x2="{x_max_px - 12:.1f}" y2="{py:.1f}" '
                f'stroke="#E2E8F0" stroke-width="1"/>'
            )

    # Axes
    elems.append(
        f'<line x1="{x_min_px:.1f}" y1="{oy:.1f}" x2="{x_max_px:.1f}" y2="{oy:.1f}" '
        f'stroke="{stroke}" stroke-width="1.8"/>'
    )
    elems.append(
        f'<line x1="{ox:.1f}" y1="{y_max_px:.1f}" x2="{ox:.1f}" y2="{y_min_px:.1f}" '
        f'stroke="{stroke}" stroke-width="1.8"/>'
    )
    # Arrowheads
    elems.append(
        f'<polygon points="{x_max_px + 4:.1f},{oy:.1f} {x_max_px - 6:.1f},{oy - 4.5:.1f} {x_max_px - 6:.1f},{oy + 4.5:.1f}" fill="{stroke}"/>'
    )
    elems.append(
        f'<polygon points="{ox:.1f},{y_min_px - 4:.1f} {ox - 4.5:.1f},{y_min_px + 6:.1f} {ox + 4.5:.1f},{y_min_px + 6:.1f}" fill="{stroke}"/>'
    )
    # Labels x, y, O
    elems.append(
        f'<text x="{x_max_px + 8:.1f}" y="{oy + 6:.1f}" font-family="\'Times New Roman\', Times, serif" '
        f'font-style="italic" font-weight="bold" font-size="20" fill="{stroke}">x</text>'
    )
    elems.append(
        f'<text x="{ox + 8:.1f}" y="{y_min_px + 4:.1f}" font-family="\'Times New Roman\', Times, serif" '
        f'font-style="italic" font-weight="bold" font-size="20" fill="{stroke}">y</text>'
    )
    elems.append(
        f'<text x="{ox - 16:.1f}" y="{oy + 18:.1f}" font-family="\'Times New Roman\', Times, serif" '
        f'font-weight="bold" font-size="18" fill="{stroke}">O</text>'
    )
    return "\n".join(elems)
