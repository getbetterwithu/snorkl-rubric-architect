#!/usr/bin/env python3
"""
Golden Example 1: Geometry + Linear Equation Hybrid with Subparts (1) & (2)
Unit: 2022 개정 중1 수학 | 변화와 관계 · 일차방정식의 활용
"""

from __future__ import annotations

import os
import sys

EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(EXAMPLE_DIR, "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import snorkl_geometry_engine as geo
from snorkl_builder import AltSolution, CriterionRow, ProblemSpec, build_all_outputs


def build_trapezoid_svg() -> str:
    # Canvas: 480 x 456. Rectangle ABCD: width 15 -> 300px (20px/cm), height 8 -> 160px (20px/cm)
    A = (85.0, 125.0)
    D = (385.0, 125.0)
    B = (85.0, 285.0)
    C = (385.0, 285.0)
    # Representative snapshot at x = 4s -> BP = 8cm -> 160px
    P = geo.midpoint(B, C, ratio=8.0 / 15.0)
    rect_pts = [A, B, C, D]

    parts = [
        '<svg width="480" height="456" viewBox="0 0 480 456" xmlns="http://www.w3.org/2000/svg">',
        # Shaded trapezoid ABPD
        geo.render_shaded_region([A, B, P, D], label="y cm²", is_math=False, font_size=21),
        # Outer rectangle ABCD
        f'<polygon points="{" ".join(geo.format_pt(pt) for pt in rect_pts)}" fill="none" stroke="#0F172A" stroke-width="2.3" stroke-linejoin="round"/>',
        # Segment DP
        f'<line x1="{D[0]:.2f}" y1="{D[1]:.2f}" x2="{P[0]:.2f}" y2="{P[1]:.2f}" stroke="#0284C7" stroke-width="2.2"/>',
        # Right angles at A and B
        geo.render_right_angle(A, B, D, size=12),
        geo.render_right_angle(B, C, A, size=12),
        # Dimension arcs: AD = 15 cm (top outward), AB = 8 cm (left outward)
        geo.render_dimension_arc(A, D, "15 cm", side="outward", sagitta=22, font_size=18, polygon_points=rect_pts),
        geo.render_dimension_arc(B, A, "8 cm", side="outward", sagitta=22, font_size=18, polygon_points=rect_pts),
        # Moving point P & direction arrow along BC
        f'<circle cx="{P[0]:.2f}" cy="{P[1]:.2f}" r="4.5" fill="#0284C7" stroke="#FFFFFF" stroke-width="1.5"/>',
        '<line x1="115" y1="322" x2="215" y2="322" stroke="#0284C7" stroke-width="2.2"/>',
        '<polygon points="223,322 212,316.5 212,327.5" fill="#0284C7"/>',
        geo.render_cloud_label(168, 348, "매초 2 cm", is_var=False, font_size=16, anchor="middle"),
        # Vertex labels
        geo.render_vertex_label(A, "A", direction="top-left", offset=12, font_size=23),
        geo.render_vertex_label(D, "D", direction="top-right", offset=12, font_size=23),
        geo.render_vertex_label(B, "B", direction="bottom-left", offset=12, font_size=23),
        geo.render_vertex_label(C, "C", direction="bottom-right", offset=12, font_size=23),
        geo.render_vertex_label(P, "P", direction="bottom", offset=10, font_size=23, color="#0369A1"),
        "</svg>",
    ]
    return "\n".join(parts)


def make_spec() -> ProblemSpec:
    return ProblemSpec(
        title="직사각형 위를 움직이는 점과 사다리꼴의 넓이",
        slug="직사각형_움직이는점_사다리꼴",
        category_tag="2022 개정 중1 수학 | 변화와 관계 · 일차방정식의 활용",
        header_latex=(
            r"오른쪽 그림과 같이 $\overline{\mathrm{AD}}=15\text{ cm}$, $\overline{\mathrm{AB}}=8\text{ cm}$인 "
            r"직사각형 $\mathrm{ABCD}$에서 점 $\mathrm{P}$가 꼭짓점 $\mathrm{B}$를 출발하여 변 $\mathrm{BC}$를 따라 "
            r"꼭짓점 $\mathrm{C}$까지 매초 $2\text{ cm}$의 속력으로 움직인다. 출발한 지 $x$초 후 사각형 $\mathrm{ABPD}$의 넓이를 $y\text{ cm}^2$라 하자."
        ),
        header_plain=(
            "그림과 같이 선분 AD = 15 cm, 선분 AB = 8 cm인 직사각형 ABCD에서 점 P가 꼭짓점 B를 출발하여 "
            "변 BC를 따라 꼭짓점 C까지 매초 2 cm의 속력으로 움직인다. 출발한 지 x초 후 사각형 ABPD의 넓이를 y cm²라 하자."
        ),
        question_latex=(
            r"(1) $y$를 $x$에 대한 식으로 나타내고, 식을 세운 이유를 도형의 성질과 변의 길이를 이용하여 설명하시오.<br>"
            r"(2) 사각형 $\mathrm{ABPD}$의 넓이가 $92\text{ cm}^2$가 되는 것은 출발한 지 몇 초 후인지 풀이 과정과 함께 구하시오."
        ),
        question_plain=(
            "(1) y를 x에 대한 식으로 나타내고, 식을 세운 이유를 도형의 성질과 변의 길이를 이용하여 설명하시오.\n"
            "(2) 사각형 ABPD의 넓이가 92 cm²가 되는 것은 출발한 지 몇 초 후인지 풀이 과정과 함께 구하시오."
        ),
        condition_latex=r"단, $0 < x \le 7.5$이다.",
        condition_plain="단, 0 < x <= 7.5이다.",
        svg_diagram=build_trapezoid_svg(),
        final_answer_latex=r"(1) $y = 8x + 60$ &nbsp; (2) $4$초 후",
        final_answer_plain="(1) y = 8x + 60, (2) 4초 후",
        model_solution_latex=(
            r"(1) 직사각형 $\mathrm{ABCD}$에서 $\overline{\mathrm{AD}} \parallel \overline{\mathrm{BC}}$이므로 $\overline{\mathrm{AD}} \parallel \overline{\mathrm{BP}}$이고 "
            r"$\angle\mathrm{B}=90^\circ$이므로 사각형 $\mathrm{ABPD}$는 윗변 $\overline{\mathrm{AD}}=15\text{ cm}$, 아랫변 $\overline{\mathrm{BP}}=2x\text{ cm}$, "
            r"높이 $\overline{\mathrm{AB}}=8\text{ cm}$인 사다리꼴이다. 따라서 $y = \frac{1}{2} \times (15 + 2x) \times 8 = 8x + 60$이다. "
            r"(2) $y = 92$를 대입하면 $8x + 60 = 92$, $8x = 32$이므로 $x = 4$이다. 이는 $0 < x \le 7.5$를 만족하므로 출발한 지 $4$초 후이다."
        ),
        model_solution_plain=(
            "(1) 직사각형 ABCD에서 선분 AD // 선분 BC이므로 선분 AD // 선분 BP이고 각 B = 90°이므로, 사각형 ABPD는 윗변 AD = 15 cm, "
            "아랫변 BP = 2x cm, 높이 AB = 8 cm인 사다리꼴이다. 따라서 y = (1/2) × (15 + 2x) × 8 = 8x + 60이다.\n"
            "(2) y = 92를 대입하면 8x + 60 = 92, 8x = 32이므로 x = 4이다. 이는 0 < x <= 7.5 범위에 맞으므로 출발한 지 4초 후이다."
        ),
        rubric_archetype="hybrid",
        criteria=[
            CriterionRow(
                stage="① 도형·길이 관계 (1점)",
                full_latex=r"점 $\mathrm{P}$의 이동 거리 $\overline{\mathrm{BP}} = 2x$와 사다리꼴(또는 넓이 분할)의 밑변·높이 관계를 필기·도형·음성으로 제시함",
                full_plain="선분 BP = 2x와 사다리꼴(또는 분할 도형)의 변·높이 관계를 필기·도형 표시·음성 중 하나로 명확히 제시함",
                edge_note_latex=r"'사다리꼴' 명칭을 생략했어도 $\overline{\mathrm{AD}}=15$, $\overline{\mathrm{BP}}=2x$, 높이 $8$ 관계가 드러나면 인정",
                edge_note_plain="'사다리꼴' 용어를 직접 쓰지 않아도 윗변 15, 아랫변 2x, 높이 8(또는 넓이 합·차 구조)의 근거가 확인되면 인정",
            ),
            CriterionRow(
                stage="② (1) 관계식 도출 (1점)",
                full_latex=r"$y = \frac{1}{2}(15 + 2x)\times 8$ 또는 동치 식을 세워 $y = 8x + 60$을 올바르게 도출함",
                full_plain="사다리꼴 넓이 식(또는 분할 식)을 세워 y = 8x + 60 (또는 동치인 미정리 식 y = 4(15 + 2x))을 올바르게 도출함",
                edge_note_latex=r"전개 전 동치 식 $y = 4(15+2x)$도 발문에 전개 강제가 없으므로 인정; $\frac{1}{2}$ 누락 등 개념 오류는 미충족",
                edge_note_plain="전개 전 동치 식 y = 4(15 + 2x)도 인정하되, 1/2 누락 등 사다리꼴 넓이 공식 자체의 개념 오류는 미충족",
            ),
            CriterionRow(
                stage="③ (2) 방정식 수립·풀이 (1점)",
                full_latex=r"(1)의 관계식에 $y = 92$를 대입하여 일차방정식 $8x + 60 = 92$를 세우고 일관되게 풀어 $x$를 구함",
                full_plain="(1)에서 구한 식에 y = 92를 대입해 일차방정식을 세우고 등식의 성질·이항으로 일관되게 풀어 x를 구함",
                edge_note_latex=r"(1)의 단순 계산 실수 식을 대입해 일관되게 푼 경우 오류 이월 인정(단, 상수식 등 구조 붕괴 식은 불인정)",
                edge_note_plain="(1)에서 단순 연산 실수로 얻은 일차식을 그대로 대입해 논리적으로 일관되게 풀었다면 중복 감점 없이 이월 인정",
            ),
            CriterionRow(
                stage="④ 최종 결론 완결 (1점)",
                full_latex=r"타당한 풀이·음성 근거를 바탕으로 출발한 지 $4$초 후($x = 4$, 앞선 연산 실수 이월 시 해당 방정식의 양수 해)임을 명확히 답함",
                full_plain="타당한 필기·도형·음성 근거를 바탕으로 최종 시각 4초 후(또는 4초, x = 4; 앞선 연산 실수 이월 시 해당 일차방정식에서 일관되게 도출된 양수 시각)를 명확히 제시함",
                edge_note_latex=r"$0 < x \le 7.5$ 범위 언급 생략은 무감점; 오류 이월 시 설명 점수에서는 ④를 인정하되 정오 판단은 원 정답 기준 적용",
                edge_note_plain="0 < x <= 7.5 범위 언급을 생략해도 감점하지 않으며, 앞 단계 연산 실수로 다른 양수 시각이 일관되게 도출된 경우 설명 점수에서는 ④를 이월 인정한다(근거 없는 단답은 0점)",
            ),
        ],
        score_levels_plain=[
            "4점: ①~④ 네 성취 요소를 모두 충족하여 식 세우기의 도형적 근거와 4초 도출 과정을 명확히 설명함",
            "3점: 오류 이월을 포함해 3개 성취 요소를 충족함(예: ② 식 정리 또는 ③ 방정식 계산 중 한 요소에서 연산 실수가 있었으나 나머지 요소를 논리적으로 일관되게 완결한 경우)",
            "2점: 2개 성취 요소를 충족함(예: (1)의 ①·②만 완결했거나, ① 파악 후 식 수립·방정식 풀이 중 한 단계만 추가 도달한 경우)",
            "1점: 1개 성취 요소만 충족함(예: BP = 2x 또는 사다리꼴 밑변·높이 조건 파악만 확인되고 관계식 수립과 방정식 풀이에 이르지 못한 경우)",
            "0점: 충족한 성취 요소가 없음(풀이·도형·음성 근거 없이 정답만 단독 기재했거나 수학적으로 무관한 응답)",
        ],
        score_levels_latex=[
            "<strong>4점</strong>: ①~④ 전 요소 충족",
            "<strong>3점</strong>: 오류 이월 포함 3개 요소 충족(한 요소 연산 실수 외 후속 일관 완결)",
            "<strong>2점</strong>: 2개 요소 충족((1)만 완결 등)",
            "<strong>1점</strong>: 1개 요소 충족($\\overline{\\mathrm{BP}}=2x$ 등 초기 조건 파악만 성공)",
            "<strong>0점</strong>: 충족 요소 없음(근거 없는 단답 또는 무관한 응답)",
        ],
        alt_solutions=[
            AltSolution(
                title="직사각형에서 직각삼각형 넓이 빼기 / 직사각형+직각삼각형 분할",
                process_latex=(
                    r"직사각형 $\mathrm{ABCD}$의 넓이 $15\times 8=120$에서 $\overline{\mathrm{PC}}=15-2x$인 직각삼각형 $\mathrm{DPC}$의 넓이 "
                    r"$\frac{1}{2}\times(15-2x)\times 8 = 60-8x$를 빼어 $y = 120-(60-8x)=8x+60$을 구함(또는 $x=0$일 때 $\triangle\mathrm{ABD}=60$에 $\triangle\mathrm{DBP}=8x$를 더함)."
                ),
                process_plain=(
                    "직사각형 ABCD 넓이 120에서 선분 PC = 15 - 2x인 직각삼각형 DPC 넓이 (1/2)×(15 - 2x)×8 = 60 - 8x를 빼어 "
                    "y = 120 - (60 - 8x) = 8x + 60을 구하거나, 삼각형 ABD(넓이 60)와 삼각형 DBP(넓이 8x)의 합으로 구함."
                ),
                mapping_latex=r"$\overline{\mathrm{PC}}=15-2x$(또는 분할 삼각형 밑변·높이) 제시 시 ① 인정, 넓이 차·합으로 $y=8x+60$ 도출 시 ② 동등 인정",
                mapping_plain="PC = 15 - 2x 또는 분할 삼각형의 밑변·높이를 밝히면 ① 인정, 넓이의 차 또는 합으로 y = 8x + 60을 얻으면 ② 동등 인정",
            ),
        ],
        specific_guardrails_latex=[
            r"단위 생략 허용: 최종 답을 '$4$', '$4$초', '$4$초 후', '$x=4$' 중 어느 형태로 적어도 정답 및 결론 요소 인정.",
            r"속력·거리 역산 풀이 인정: (2)에서 사다리꼴 넓이 $92 = \frac{1}{2}\times(15+\overline{\mathrm{BP}})\times 8$로 $\overline{\mathrm{BP}}=8\text{ cm}$를 먼저 구한 뒤 $8\div 2=4$(초)로 구한 풀이도 ③·④ 완전 인정.",
        ],
        specific_guardrails_plain=[
            "단위 표기 유연성: (2)의 답을 '4', '4초', '4초 후', 'x = 4' 중 어느 형태로 표현해도 동일하게 인정한다.",
            "선분 길이 우선 역산 인정: (2)에서 (1)의 식에 대입하는 대신 92 = (1/2)×(15 + BP)×8로 선분 BP = 8 cm를 먼저 구하고 8 ÷ 2 = 4(초)로 구한 풀이도 ③, ④ 요소를 모두 충족한 것으로 인정한다.",
        ],
    )


if __name__ == "__main__":
    paths = build_all_outputs(make_spec(), EXAMPLE_DIR, max_pdf_pages=1, validate=True)
    for k, v in paths.items():
        print(f"{k}: {v}")
