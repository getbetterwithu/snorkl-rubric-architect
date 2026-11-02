#!/usr/bin/env python3
"""
snorkl_geometry_engine.py (v7.0 Master Edition)
한국 중·고등학교 수학 교과서 및 수능/전국연합학평 기하 그래픽 표준 엔진.

[확립된 황금 세팅 규격]
1. 치수선: 변을 현(Chord)으로 하는 '순수 원호(Circular Arc, SVG A 명령어)' 작도
2. 치수 라벨 상자(Dimension Box): 변을 가리지 않게 외측으로 딱 '살짝(6~8px)'만 이격하여 불투명 마스킹
3. 평행 화살표: 가시성 2배 확대 (길이 14px, 너비 10px)로 선분 중간 안착
4. 꼭짓점 레이블: 로만체 볼드(Times New Roman) 및 선분/꼭짓점에서 바깥으로 10~15px 여유 이격
5. 수학적 비례: 선분 길이 비례(예: 3:1) 내분점 공식을 엄밀하게 좌표화
"""

import math

def format_pt(p):
    return f"{p[0]:.2f},{p[1]:.2f}"

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def midpoint(p1, p2, ratio=0.5):
    """p1에서 p2 방향으로 ratio 비율의 내분점 계산"""
    return (p1[0] + (p2[0] - p1[0]) * ratio, p1[1] + (p2[1] - p1[1]) * ratio)

def unit_vector(p1, p2):
    d = distance(p1, p2)
    if d == 0:
        return (0.0, 0.0)
    return ((p2[0] - p1[0]) / d, (p2[1] - p1[1]) / d)

def normal_vector(p1, p2):
    """선분 p1->p2 기준 왼쪽(외측) 직교 단위벡터"""
    ux, uy = unit_vector(p1, p2)
    return (-uy, ux)

def right_normal_vector(p1, p2):
    """선분 p1->p2 기준 오른쪽(외측) 직교 단위벡터"""
    ux, uy = unit_vector(p1, p2)
    return (uy, -ux)

def render_right_angle(vertex, p1, p2, size=13, stroke="#1E293B", stroke_width=1.8):
    """한국 교과서 표준 직각 표시 기호 사각형"""
    u1 = unit_vector(vertex, p1)
    u2 = unit_vector(vertex, p2)
    c1 = (vertex[0] + u1[0] * size, vertex[1] + u1[1] * size)
    c2 = (c1[0] + u2[0] * size, c1[1] + u2[1] * size)
    c3 = (vertex[0] + u2[0] * size, vertex[1] + u2[1] * size)
    return f'<path d="M {format_pt(c1)} L {format_pt(c2)} L {format_pt(c3)}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>'

def render_parallel_arrow(p1, p2, count=1, length=14, width=10, stroke="#1E293B", fill="#1E293B", ratio=0.5):
    """
    한국 교과서 및 시험지 표준 평행 화살표 (2배 확대 황금 규격: length=14, width=10)
    count=1: ▶, count=2: ▶▶
    """
    mid = midpoint(p1, p2, ratio)
    ux, uy = unit_vector(p1, p2)
    nx, ny = normal_vector(p1, p2)
    
    arrows = []
    if count == 1:
        offsets = [0]
    elif count == 2:
        offsets = [-length * 0.8, length * 0.8]
    elif count == 3:
        offsets = [-length * 1.6, 0, length * 1.6]
    else:
        offsets = [0]
        
    for off in offsets:
        tip = (mid[0] + ux * off + ux * (length / 2), mid[1] + uy * off + uy * (length / 2))
        back_left = (tip[0] - ux * length + nx * (width / 2), tip[1] - uy * length + ny * (width / 2))
        back_right = (tip[0] - ux * length - nx * (width / 2), tip[1] - uy * length - ny * (width / 2))
        arrows.append(f'<polygon points="{format_pt(tip)} {format_pt(back_left)} {format_pt(back_right)}" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
    return "\n".join(arrows)

def render_tick_mark(p1, p2, count=1, tick_len=9, spacing=3.5, stroke="#1E293B", stroke_width=1.8, ratio=0.5):
    """길이 같음 표시 틱 마크 (count=1: |, count=2: ||)"""
    mid = midpoint(p1, p2, ratio)
    ux, uy = unit_vector(p1, p2)
    nx, ny = normal_vector(p1, p2)
    
    ticks = []
    if count == 1:
        offsets = [0]
    elif count == 2:
        offsets = [-spacing / 2, spacing / 2]
    elif count == 3:
        offsets = [-spacing, 0, spacing]
    else:
        offsets = [0]
        
    for off in offsets:
        center = (mid[0] + ux * off, mid[1] + uy * off)
        t1 = (center[0] + nx * (tick_len / 2), center[1] + ny * (tick_len / 2))
        t2 = (center[0] - nx * (tick_len / 2), center[1] - ny * (tick_len / 2))
        ticks.append(f'<line x1="{t1[0]:.2f}" y1="{t1[1]:.2f}" x2="{t2[0]:.2f}" y2="{t2[1]:.2f}" stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round"/>')
    return "\n".join(ticks)

def render_cloud_label(x, y, text_str, is_var=False, font_size=19, anchor="middle"):
    """
    [황금 세팅 v12.0 최종본] 구름처럼 올록볼록한 불투명 텍스트 라벨 (Puffy Cloud-masked Label)
    1. 내부 완전 밀폐: 글자 사이 빈틈, 띄어쓰기 공백, 숫자 내부 구멍 등 100% 꽉 찬 불투명 흰색으로 점선 완벽 차단.
    2. 외부 올록볼록 구름 외곽선: 글자 외곽 곡선을 따라 부드럽게 튀어나오는 10px 라운드 스트로크.
    3. 소문자 윗줄 100% 일치: 표준 베이스라인으로 x, y, c, m 상단선 수평 정렬.
    """
    w_approx = len(text_str) * 11.0
    h_approx = font_size
    
    if anchor == "middle":
        rx = x - w_approx / 2.0
    elif anchor == "end":
        rx = x - w_approx
    else: # start
        rx = x
        
    ry = y - h_approx + 4
    rw = w_approx
    rh = h_approx - 2
    
    if is_var:
        parts = text_str.split(" ", 1)
        var_part = parts[0]
        unit_part = (" " + parts[1]) if len(parts) > 1 else ""
        content_bg = f'<tspan font-style="italic">{var_part}</tspan>{unit_part}'
        content_fg = f'<tspan font-style="italic">{var_part}</tspan>{unit_part}'
    else:
        content_bg = text_str
        content_fg = text_str
        
    return f"""<g>
  <!-- 내부 빈틈 및 띄어쓰기 완전 차단 흰색 코어 -->
  <rect x="{rx:.1f}" y="{ry:.1f}" width="{rw:.1f}" height="{rh:.1f}" fill="#FFFFFF"/>
  <!-- 올록볼록 구름 외곽선 (두꺼운 라운드 스트로크) -->
  <text x="{x:.1f}" y="{y:.1f}" font-family="'Times New Roman', Times, serif" font-size="{font_size}" font-weight="bold" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="10px" stroke-linejoin="round" stroke-linecap="round" text-anchor="{anchor}">{content_bg}</text>
  <!-- 전면 선명한 본문 텍스트 -->
  <text x="{x:.1f}" y="{y:.1f}" font-family="'Times New Roman', Times, serif" font-size="{font_size}" font-weight="bold" fill="#0F172A" text-anchor="{anchor}">{content_fg}</text>
</g>"""

def render_angle_arc(vertex, p1, p2, label=None, r=20,
                     stroke="#1E293B", stroke_width=1.6, label_color="#0F172A",
                     halo_color="#FFFFFF", halo_width=6, font_size=16):
    """
    [황금 세팅 v11.0 최종본]
    1. 꼭짓점 중심 동심원: vertex를 원점으로 삼아 양 변에 100% 밀착.
    2. 내각 회전: sweep을 정확히 내각 방향으로 설정.
    3. 비간섭 이등분선 레이블: 양 변과 각도 호에 일절 닿지 않도록 각도 크기에 따른 안전거리 자동 계산.
    4. 텍스트 헤일로 마스크 적용: 6px 흰색 헤일로로 미세 겹침까지 완벽 보호.
    """
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
    
    min_d_sides = 12.0 / math.sin(max(0.1, alpha / 2.0))
    min_d_arc = r + 13.0
    d_label = min(46.0, max(min_d_sides, min_d_arc))
    
    label_x = vertex[0] + d_label * math.cos(bisector)
    label_y = vertex[1] + d_label * math.sin(bisector)
    
    path_tag = f'<path d="M {s_x:.2f},{s_y:.2f} A {r} {r} 0 0 {sweep} {e_x:.2f},{e_y:.2f}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    if label:
        text_tag = f'<text x="{label_x:.2f}" y="{label_y:.2f}" font-family="-apple-system, BlinkMacSystemFont, \'Times New Roman\', sans-serif" font-size="{font_size}" font-weight="bold" fill="{label_color}" text-anchor="middle" dominant-baseline="central" style="paint-order: stroke fill; stroke: {halo_color}; stroke-width: {halo_width}px; stroke-linejoin: round; stroke-linecap: round;">{label}</text>'
        return f"{path_tag}\n{text_tag}"
    return path_tag

def render_vertex_label(point, label, direction="top", offset=14, font_size=25, color="#1E293B"):
    """
    꼭짓점 레이블: 로만체 볼드(Times New Roman) 및 선분에서 10~15px 자연스럽게 이격
    """
    dx, dy = 0, 0
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
        
    return f'<text x="{point[0] + dx:.2f}" y="{point[1] + dy:.2f}" font-family="Times New Roman, serif" font-weight="bold" font-size="{font_size}" fill="{color}" text-anchor="{anchor}">{label}</text>'
