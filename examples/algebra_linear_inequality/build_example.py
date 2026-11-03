#!/usr/bin/env python3
"""
Golden Example 2: Algebra Linear Inequality (Whiteboard Workspace Mode, 0 Forced Alternatives)
Unit: 2022 개정 중2 수학 | 변화와 관계 · 일차부등식
"""

from __future__ import annotations

import os
import sys

EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.path.join(EXAMPLE_DIR, "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from snorkl_builder import CriterionRow, ProblemSpec, build_all_outputs


def make_spec() -> ProblemSpec:
    return ProblemSpec(
        title="계수가 분수인 일차부등식의 최대 자연수 해",
        slug="일차부등식_최대자연수해",
        category_tag="일차부등식",
        header_latex=r"다음 일차부등식을 만족시키는 가장 큰 자연수 $x$의 값을 구하려고 한다.",
        header_plain="다음 일차부등식을 만족시키는 가장 큰 자연수 x의 값을 구하려고 한다.",
        formulas_latex=[r"\frac{2}{5}x - \frac{1}{2} > \frac{2x - 4}{3}"],
        formulas_plain=["(2/5)x - 1/2 > (2x - 4)/3"],
        question_latex=(
            r"부등식의 성질을 이용하여 주어진 일차부등식의 해를 구하고, "
            r"이를 만족시키는 가장 큰 자연수 $x$의 값을 풀이 과정과 함께 서술하시오."
        ),
        question_plain=(
            "부등식의 성질을 이용하여 주어진 일차부등식의 해를 구하고, "
            "이를 만족시키는 가장 큰 자연수 x의 값을 풀이 과정과 함께 서술하시오."
        ),
        svg_diagram="",  # Algebra whiteboard workspace mode
        final_answer_latex=r"$3$",
        final_answer_plain="3",
        model_solution_latex=(
            r"분모 $5, 2, 3$의 최소공배수인 양수 $30$을 양변에 곱하면 $12x - 15 > 10(2x - 4)$이다. "
            r"우변의 괄호를 풀면 $12x - 15 > 20x - 40$이고, 일차항을 좌변으로, 상수항을 우변으로 이항하여 정리하면 "
            r"$-8x > -25$이다. 양변을 음수 $-8$로 나누면 부등호의 방향이 바뀌므로 $x < \frac{25}{8}$ ($= 3.125$)이다. "
            r"따라서 이를 만족시키는 자연수 $x$는 $1, 2, 3$이므로 가장 큰 자연수 $x$의 값은 $3$이다."
        ),
        model_solution_plain=(
            "분모 5, 2, 3의 최소공배수인 양수 30을 양변에 곱하면 12x - 15 > 10(2x - 4)이다. "
            "괄호를 풀면 12x - 15 > 20x - 40이고, 이항하여 동류항을 정리하면 -8x > -25이다. "
            "양변을 음수 -8로 나누면 부등호의 방향이 바뀌므로 x < 25/8 (= 3.125)이다. "
            "따라서 이를 만족시키는 자연수 x는 1, 2, 3이므로 가장 큰 자연수 x의 값은 3이다."
        ),
        rubric_archetype="calculation",
        criteria=[
            CriterionRow(
                stage="① 정계수 변환·전개 (1점)",
                full_latex=r"양변에 $30$(또는 공배수)을 곱하거나 통분하여 $12x - 15 > 20x - 40$과 동치인 식으로 올바르게 정리함",
                full_plain="양변에 분모의 공배수(30 등)를 곱하거나 통분하여 12x - 15 > 20x - 40과 동치인 식으로 정리함",
                edge_note_latex=r"상수항 $-\frac{1}{2}$에 $30$을 곱하지 않는 분배 누락 또는 괄호 부호 실수 시 본 요소 감점(후속 일관 풀이는 이월)",
                edge_note_plain="-1/2에 30을 곱하지 않거나 10(2x - 4) 분배 시 부호·계산 실수가 있으면 본 요소만 감점하고 후속 과정은 이월 채점",
            ),
            CriterionRow(
                stage="② 이항 및 동류항 정리 (1점)",
                full_latex=r"미지수 항과 상수항을 이항하여 $-8x > -25$ 또는 $25 > 8x$ ($8x < 25$)를 도출함",
                full_plain="이항으로 동류항을 정리하여 -8x > -25 또는 25 > 8x (8x < 25)를 올바르게 도출함",
                edge_note_latex=r"미지수 항을 우변으로 넘겨 양수 계수($25 > 8x$)로 정리한 풀이도 100% 동등 인정",
                edge_note_plain="미지수 항을 우변으로 이항해 양수 계수(25 > 8x)로 정리한 풀이도 부등식 성질의 올바른 적용이므로 완전 인정",
            ),
            CriterionRow(
                stage="③ 부등식 해 도출 (1점)",
                full_latex=r"부등호 방향을 올바르게 처리하여 해 $x < \frac{25}{8}$ (또는 $x < 3\frac{1}{8}$, $x < 3.125$)를 구함",
                full_plain="부등호 방향을 올바르게 처리하여 x < 25/8 (또는 x < 3과 1/8, x < 3.125)를 정확히 구함",
                edge_note_latex=r"$-8$로 나눌 때 부등호 방향 미전환($x > \frac{25}{8}$) 시 본 요소 미충족 및 '최대 자연수' 구조 붕괴로 ④ 이월 불가",
                edge_note_plain="-8로 나눌 때 부등호 방향을 바꾸지 않아 x > 25/8이 되면 최대 자연수가 존재하지 않게 되어 문항 구조가 무너지므로 ④ 이월 불인정",
            ),
            CriterionRow(
                stage="④ 최대 자연수 결정 (1점)",
                full_latex=r"구한 해의 범위($x < \frac{25}{8}$)를 근거로 가장 큰 자연수 $3$을 명확히 도출함",
                full_plain="구한 해의 범위를 근거로(수직선·대소 비교·음성 설명 포함) 가장 큰 자연수 3을 정확히 결정함",
                edge_note_latex=r"앞선 산술 실수로 예: $x < \frac{35}{8}$을 얻은 뒤 그 범위의 최대 자연수 $4$를 일관되게 답한 경우 ④ 이월 인정",
                edge_note_plain="앞 단계 단순 산술 실수로 예컨대 x < 35/8을 얻었더라도 그 범위에서 최대 자연수 4를 일관되게 선택했다면 ④는 이월 인정",
            ),
        ],
        score_levels_plain=[
            "4점: ①~④ 네 성취 요소를 모두 충족하여 해 x < 25/8과 최대 자연수 3을 근거와 함께 명확히 제시함",
            "3점: 오류 이월을 포함해 3개 성취 요소를 충족함(예: ①에서 분배 산술 실수가 있었으나 그 결과식으로부터 ②~④를 논리적으로 일관되게 완결한 경우)",
            "2점: 2개 성취 요소를 충족함(예: ①·②로 -8x > -25까지 도출한 뒤 음수 나눗셈 부등호 방향 전환에 실패해 ③·④가 무너진 경우)",
            "1점: 1개 성취 요소만 충족함(예: ① 공배수 30을 곱해 정계수 부등식으로 올바르게 변형한 뒤, 부등식의 해를 구하지 않고 자연수 대입으로만 확인한 경우)",
            "0점: 충족한 성취 요소가 없음(근거 없는 답 단독 기재, 또는 정계수 식 변형조차 없이 원래 분수 부등식에 자연수만 대입해 찍은 경우, 무관한 응답)",
        ],
        score_levels_latex=[
            "<strong>4점</strong>: ①~④ 전 요소 충족",
            "<strong>3점</strong>: 오류 이월 포함 3개 요소 충족(예: 초기 산술 실수 후 ②~④ 일관 완결)",
            "<strong>2점</strong>: 2개 요소 충족(예: ①·② 충족 후 음수 나눗셈 부등호 방향 오류)",
            "<strong>1점</strong>: 1개 요소 충족(예: ① 정계수 변형만 성공 후 대입 확인 등)",
            "<strong>0점</strong>: 충족 요소 없음(근거 없는 단답 또는 식 변형 없는 단순 숫자 대입)",
        ],
        alt_solutions=[],  # Genuinely single-method algebraic item -> 0 forced alternatives!
        specific_guardrails_latex=[
            r"발문 준수 확인: 발문에서 '주어진 일차부등식의 해를 구하고'라고 명시했으므로 해 도출 없는 숫자 대입만으로는 ②~④를 인정하지 않음(식 변형 없는 원식 대입은 $0$점, ① 정계수 변형 후 대입은 ①만 인정하여 $1$점).",
            r"분수·대분수·소수 동치 인정: 해를 $x < \frac{25}{8}$, $x < 3\frac{1}{8}$, $x < 3.125$ 중 어느 형태로 표기해도 ③ 완전 인정.",
        ],
        specific_guardrails_plain=[
            "발문 요구사항 준수: 발문에서 '일차부등식의 해를 구하고'라고 명시했으므로, 부등식의 해 도출 없이 자연수만 대입한 풀이는 ②~④ 미충족으로 처리한다(식 변형 없이 원식에 숫자만 대입한 경우 0점, ① 정계수 변형 성공 후 대입한 경우 ①만 인정하여 1점).",
            "동치 수 표현 인정: 부등식의 해를 x < 25/8, x < 3과 1/8, x < 3.125 중 어느 것으로 나타내도 ③을 완전 인정한다.",
        ],
    )


if __name__ == "__main__":
    paths = build_all_outputs(make_spec(), EXAMPLE_DIR, max_pdf_pages=3, validate=True, keep_html=True)
    for k, v in paths.items():
        print(f"{k}: {v}")
