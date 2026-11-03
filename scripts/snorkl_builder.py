#!/usr/bin/env python3
"""
snorkl_builder.py - Canonical Single-Source-of-Truth Problem Set Builder (v15.0)

Feeds a single `ProblemSpec` object into all 3 Snorkl deliverables:
  1. Problem Registration Card (`[slug]_문제등록화면.png`, 2000x1000 via local KaTeX)
  2. Snorkl `정답/평가 기준` Plain-Text Markdown (`[slug]_정답_평가기준.md`, zero LaTeX `$`)
  3. Teacher Reference A4 Rubric PDF (`[slug]_교사참고용_채점기준표.pdf`, 1-page target)

Design Guarantees:
  - Prevents condition/number/answer drift across Card, MD, and PDF by deriving all 3
    from one `ProblemSpec` and stamping a SHA-256 spec digest into generated HTML.
  - Aligns with Snorkl's official dual scoring architecture (`help.snorkl.app`):
      (a) Binary Correct / Incorrect (`정오 판단`) on the final answer, and
      (b) Integer `0, 1, 2, 3, 4` Explanation Score (`설명 점수`) — never instructs
          Snorkl AI to output fractional `0.5` scores.
  - Allows `0` alternative solutions when no genuinely distinct middle-school solution exists.
"""

from __future__ import annotations

import dataclasses
import hashlib
import html
import json
import os
import pathlib
import re
from dataclasses import dataclass, field
from typing import Sequence
from urllib.parse import quote

from render_card import VENDOR_KATEX_DIR, render_pdf, render_png

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CARD_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template_card.html")
SHEET_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template_teacher_sheet.html")


@dataclass
class CriterionRow:
    """Single observable achievement element within the 0-4 explanation rubric."""

    stage: str
    full_latex: str
    full_plain: str
    edge_note_latex: str
    edge_note_plain: str


@dataclass
class AltSolution:
    """Optional genuinely distinct middle-school alternative solution (0, 1, or 2)."""

    title: str
    process_latex: str
    process_plain: str
    mapping_latex: str
    mapping_plain: str


@dataclass
class ProblemSpec:
    """Canonical single source of truth for a Snorkl math item and its rubric."""

    title: str
    category_tag: str
    header_latex: str
    header_plain: str
    question_latex: str
    question_plain: str
    final_answer_latex: str
    final_answer_plain: str
    model_solution_latex: str
    model_solution_plain: str
    criteria: list[CriterionRow]
    score_levels_plain: list[str]
    score_levels_latex: list[str] = field(default_factory=list)
    formulas_latex: list[str] = field(default_factory=list)
    formulas_plain: list[str] = field(default_factory=list)
    condition_latex: str = ""
    condition_plain: str = ""
    svg_diagram: str = ""
    workspace_badge: str = "✏️ 풀이 과정을 자유롭게 적어 보세요"
    workspace_hint: str = "식과 이유를 함께 말하거나 적어 주면 더 정확한 피드백을 받을 수 있습니다."
    rubric_archetype: str = "calculation"  # calculation | proof | subparts | hybrid
    explanation_required: bool = True
    value_only_subparts: list[str] = field(default_factory=list)
    method_restriction_plain: str = ""
    method_restriction_latex: str = ""
    alt_solutions: list[AltSolution] = field(default_factory=list)
    specific_guardrails_latex: list[str] = field(default_factory=list)
    specific_guardrails_plain: list[str] = field(default_factory=list)
    slug: str = ""

    def resolved_slug(self) -> str:
        raw = self.slug.strip() if self.slug.strip() else self.title.strip()
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", raw)
        cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
        return cleaned or "snorkl_item"

    def spec_sha256(self) -> str:
        payload = json.dumps(dataclasses.asdict(self), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def default_common_guardrails_plain(spec: ProblemSpec) -> list[str]:
    """Generate Snorkl AI common grading guardrails reflecting v15 consensus policies."""
    if spec.explanation_required and not spec.value_only_subparts:
        answer_only_rule = (
            "근거 없는 정답 단독 기재 처리: 풀이·이유 설명을 요구하는 문항이므로 필기·도형 표시·음성 설명 중 "
            "어느 곳에도 타당한 근거 없이 최종 답만 단독 기재한 경우 설명 점수는 0점 처리한다 "
            "(정오 판단만 정답 처리 가능). 단, 암산 가능한 단순 사칙연산 중간 줄 생략은 감점하지 않는다."
        )
    elif spec.value_only_subparts:
        joined = ", ".join(spec.value_only_subparts)
        answer_only_rule = (
            f"소문항별 정답 단독 기재 구분: 값만 묻는 소문항({joined})은 과정 생략만으로 0점 처리하지 않으며, "
            "풀이·이유 서술을 요구한 소문항에 한해서만 근거 없는 답 단독 기재를 해당 성취 요소 미충족으로 판정한다."
        )
    else:
        answer_only_rule = "결과 도출의 근거를 필기·도형 표시·음성 설명 전반에서 종합적으로 확인하여 채점한다."

    if spec.method_restriction_plain.strip():
        advanced_rule = f"풀이 방법 제한 기준: {spec.method_restriction_plain.strip()}"
    else:
        advanced_rule = (
            "교육과정 외(선행) 방법 처리: 학생이 중학교 범위 밖의 공식·성질을 사용했더라도 발문에서 방법을 제한하지 않았고 "
            "수학적 논리에 오류가 없으면 불이익 없이 인정한다."
        )

    return [
        "스노클 이원 채점 준수: 최종 답의 정오 판단(Correct/Incorrect)과 설명 점수(0, 1, 2, 3, 4 정수 척도)를 분리하여 판정하며, 소수점(0.5점) 점수는 부여하지 않는다.",
        "필기·도형·음성(Voice) 통합 인정: 성취 요소 및 결론 도출의 근거를 '직전 한 줄 식'으로 한정하지 않고, 화이트보드 전체 필기·도형 위 표시·음성 녹음 설명 어디에서든 타당한 근거가 확인되면 인정한다. 말하면서 스스로 오류를 정정한 경우 최종 정정 의도를 기준으로 채점한다.",
        answer_only_rule,
        "오류 이월(중복 감점 금지): 계산·부호 등 오류가 처음 발생한 지점에서는 해당 성취 요소를 감점하되, 그 오류 값으로부터 논리적으로 일관되게 전개된 후속 단계는 중복 감점하지 않는다. 단, 핵심 개념 오류로 문항의 수학적 구조를 훼손·단순화한 경우에는 후속 이월을 인정하지 않는다.",
        advanced_rule,
        "표현·순서 다양성 인정 및 모순 기준: 교과서 특정 어휘를 강제하지 않으며 동치 수식과 풀이 순서 변경을 모두 인정한다. 단순 맞춤법·어투는 감점하지 않되, 추가 서술이 앞선 옳은 논증을 직접 부정하는 수학적 모순일 때만 감점한다. 판독 불능 필기·음성은 임의 추측 채점하지 않는다.",
    ]


def default_common_guardrails_latex(spec: ProblemSpec) -> list[str]:
    """Generate concise, teacher-readable common guardrails for the 1-page A4 PDF."""
    base = [
        "<strong>스노클 이원 채점(정오 + 0~4점 정수)</strong>: 최종 답 정오(Correct/Incorrect)와 풀이 설명 점수($0, 1, 2, 3, 4$ 정수)를 분리하며, AI 채점에 $0.5$점 단위를 강제하지 않음.",
        "<strong>필기·도형·음성(Voice) 통합 근거 인정</strong>: 결론 근거를 직전 식에 한정하지 않고 답안 전체의 필기·도형 표시·음성 설명에서 인정하며, 발화 중 자기 정정은 최종 의도 기준으로 채점.",
    ]
    if spec.explanation_required and not spec.value_only_subparts:
        base.append(
            "<strong>정답 단독 기재</strong>: 설명 요구 문항에서 필기·도형·음성 근거가 전무한 단순 정답 기재는 설명 점수 $0$점 처리(단순 암산 중간 줄 생략은 허용)."
        )
    elif spec.value_only_subparts:
        joined = ", ".join(html.escape(s) for s in spec.value_only_subparts)
        base.append(
            f"<strong>소문항별 차등 적용</strong>: 값만 묻는 소문항({joined})은 단답 기재만으로 $0$점 처리하지 않으며, 설명 요구 소문항에만 근거 의무를 적용."
        )
    base.append(
        "<strong>오류 이월(발생 지점 1회 감점)</strong>: 최초 오류 지점만 감점하고 그 결과와 논리적으로 일관된 후속 전개는 중복 감점 금지(단, 핵심 개념 훼손·난이도 붕괴 오류는 이월 불인정)."
    )
    if spec.method_restriction_latex.strip():
        base.append(f"<strong>풀이 방법 제한</strong>: {spec.method_restriction_latex.strip()}")
    else:
        base.append(
            "<strong>선행·대안 방법 및 표현 자율성</strong>: 발문의 방법 제한이 없는 한 수학적으로 타당한 선행·별해와 동치 표기·순서 변경을 인정하며, 앞선 논증을 부정하는 모순 서술만 감점."
        )
    return base


def _portable_asset_href(target_path: str, from_html_dir: str, max_up_levels: int = 4) -> str:
    """Use a portable URL-encoded relative path when nearby on the same drive; else file:/// URI."""
    target_abs = os.path.abspath(target_path)
    base_abs = os.path.abspath(from_html_dir)
    try:
        rel = os.path.relpath(target_abs, base_abs)
        up_count = sum(1 for part in rel.split(os.sep) if part == "..")
        if up_count <= max_up_levels:
            rel_posix = rel.replace("\\", "/")
            encoded = "/".join(
                seg if seg in (".", "..") else quote(seg)
                for seg in rel_posix.split("/")
            )
            if not encoded.startswith((".", "/")):
                encoded = f"./{encoded}"
            return encoded
    except ValueError:
        pass
    return pathlib.Path(target_abs).as_uri()


def _inject_local_katex(template_html: str, out_html_dir: str) -> str:
    if os.path.isdir(VENDOR_KATEX_DIR):
        katex_href = _portable_asset_href(VENDOR_KATEX_DIR, out_html_dir, max_up_levels=4).rstrip("/")
        return template_html.replace("./vendor/katex", katex_href)
    return template_html


def build_card_html(spec: ProblemSpec, out_html_path: str) -> str:
    """Generate the 1000x500 (2000x1000 @2x) Card HTML from `ProblemSpec`."""
    out_abs = os.path.abspath(out_html_path)
    out_dir = os.path.dirname(out_abs)
    with open(CARD_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        tpl = f.read()

    tpl = _inject_local_katex(tpl, out_dir)

    passage_parts = [
        f'<div class="category-tag">{html.escape(spec.category_tag)}</div>',
        f'<div class="problem-header">{spec.header_latex}</div>',
    ]
    for f_latex in spec.formulas_latex:
        formula_str = f_latex.strip()
        if not (formula_str.startswith("$$") and formula_str.endswith("$$")):
            formula_str = f"$${formula_str}$$"
        passage_parts.append(f'<div class="problem-formula">{formula_str}</div>')

    passage_parts.append(f'<div class="target-question">{spec.question_latex}</div>')
    if spec.condition_latex.strip():
        passage_parts.append(f'<div class="condition-text">{spec.condition_latex}</div>')

    passage_html = "\n      ".join(passage_parts)

    if spec.svg_diagram.strip():
        right_panel_html = f'<div class="geometry">\n      {spec.svg_diagram.strip()}\n    </div>'
    else:
        right_panel_html = (
            '<div class="student-workspace">\n'
            f'      <div class="workspace-top"><span class="workspace-badge">{html.escape(spec.workspace_badge)}</span></div>\n'
            '      <div class="workspace-middle"></div>\n'
            f'      <div class="workspace-bottom"><span class="workspace-bottom-hint">{html.escape(spec.workspace_hint)}</span></div>\n'
            "    </div>"
        )

    meta_tags = (
        f'  <meta name="snorkl-spec-sha256" content="{spec.spec_sha256()}">\n'
        f'  <meta name="snorkl-final-answer" content="{html.escape(spec.final_answer_plain)}">'
    )
    rendered = re.sub(r"(<meta charset=\"UTF-8\">)", rf"\1\n{meta_tags}", tpl, count=1)
    rendered = rendered.replace("<!-- PASSAGE_HTML_PLACEHOLDER -->", passage_html)
    rendered = rendered.replace("<!-- RIGHT_PANEL_PLACEHOLDER -->", right_panel_html)

    out_abs = os.path.abspath(out_html_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w", encoding="utf-8") as f:
        f.write(rendered)
    return out_abs


def build_snorkl_markdown(spec: ProblemSpec, out_md_path: str) -> str:
    """Generate the 100% Plain-Text (`$`-free) Snorkl `정답/평가 기준` `.md` file."""
    lines: list[str] = []

    lines.append("[문항]")
    lines.append(spec.header_plain.strip())
    for fp in spec.formulas_plain:
        if fp.strip():
            lines.append(f"  {fp.strip()}")
    lines.append(spec.question_plain.strip())
    if spec.condition_plain.strip():
        lines.append(spec.condition_plain.strip())
    lines.append("")

    lines.append("[정답 — 스노클 정오 판단 기준]")
    lines.append(spec.final_answer_plain.strip())
    lines.append("")

    lines.append("[기본 모범 풀이 (2022 개정 중학교 교과서 표준)]")
    lines.append(spec.model_solution_plain.strip())
    lines.append("")

    lines.append("[설명 점수 채점 기준: 0~4점 정수 척도]")
    lines.append("※ 스노클 AI는 정오 판단(Correct/Incorrect)과 별개로 설명 점수를 0, 1, 2, 3, 4 정수로 부여합니다.")
    lines.append("1) 핵심 성취 요소:")
    for row in spec.criteria:
        lines.append(f"  - {row.stage}: {row.full_plain.strip()} (감점·예외 기준: {row.edge_note_plain.strip()})")
    lines.append("2) 정수 점수(0~4점) 도달 기준:")
    for lvl in spec.score_levels_plain:
        lines.append(f"  - {lvl.strip()}")
    lines.append("")

    if spec.alt_solutions:
        lines.append("[다른 풀이 및 대체 성취 인정 기준]")
        for idx, alt in enumerate(spec.alt_solutions, start=1):
            lines.append(f"{idx}. {alt.title.strip()}")
            lines.append(f"  - 풀이 요약: {alt.process_plain.strip()}")
            lines.append(f"  - 대체 인정: {alt.mapping_plain.strip()}")
        lines.append("")

    lines.append("[공통 채점 가드레일]")
    for idx, rule in enumerate(default_common_guardrails_plain(spec), start=1):
        lines.append(f"{idx}. {rule}")
    lines.append("")

    if spec.specific_guardrails_plain:
        lines.append("[문항 특화 보완 원칙]")
        for rule in spec.specific_guardrails_plain:
            lines.append(f"- {rule.strip()}")
        lines.append("")

    content = "\n".join(lines).rstrip() + "\n"
    out_abs = os.path.abspath(out_md_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w", encoding="utf-8") as f:
        f.write(content)
    return out_abs


def build_teacher_sheet_html(spec: ProblemSpec, card_png_path: str, out_html_path: str) -> str:
    """Generate the Teacher Reference A4 HTML (with portable local KaTeX & card preview href)."""
    out_abs = os.path.abspath(out_html_path)
    out_dir = os.path.dirname(out_abs)
    with open(SHEET_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        tpl = f.read()

    tpl = _inject_local_katex(tpl, out_dir)
    card_png_uri = _portable_asset_href(card_png_path, out_dir, max_up_levels=2)

    blocks: list[str] = []
    blocks.append(
        '<div class="card-preview-container">\n'
        f'    <img class="card-preview" src="{card_png_uri}" alt="문제 등록 카드 미리보기">\n'
        "  </div>"
    )

    blocks.append(
        '<div class="section-title">1. 최종 정답 및 교과서 표준 모범답안</div>\n'
        '  <div class="info-box">\n'
        f'    <div id="final-answer-box" data-final-answer="{html.escape(spec.final_answer_plain)}" '
        'style="margin-bottom: 5px;">'
        f"<strong>[최종 정답 (정오 판단 기준)]</strong> {spec.final_answer_latex}</div>\n"
        f'    <div><strong>[기본 모범답안]</strong> {spec.model_solution_latex}</div>\n'
        "  </div>"
    )

    rows_html = []
    for row in spec.criteria:
        rows_html.append(
            "      <tr>\n"
            f"        <td><strong>{html.escape(row.stage)}</strong></td>\n"
            f"        <td>{row.full_latex}</td>\n"
            f"        <td>{row.edge_note_latex}</td>\n"
            "      </tr>"
        )

    levels_source = spec.score_levels_latex if spec.score_levels_latex else [html.escape(s) for s in spec.score_levels_plain]
    levels_inline = " / ".join(levels_source)

    blocks.append(
        '<div class="section-title">2. 설명 점수 채점 기준표 (스노클 0~4점 정수 척도)</div>\n'
        "  <table>\n"
        "    <thead>\n"
        "      <tr>\n"
        '        <th class="th-stage">성취 요소</th>\n'
        '        <th class="th-full">충족 기준 (필기·도형·음성 통합)</th>\n'
        '        <th class="th-partial">감점·오류 이월 및 경계 처리</th>\n'
        "      </tr>\n"
        "    </thead>\n"
        "    <tbody>\n"
        + "\n".join(rows_html)
        + "\n    </tbody>\n"
        "  </table>\n"
        f'  <div class="info-box" style="padding: 5px 10px; font-size: 10.4px;">'
        f"<strong>[0~4점 정수 매핑]</strong> {levels_inline}</div>"
    )

    if spec.alt_solutions:
        alt_items = []
        for idx, alt in enumerate(spec.alt_solutions, start=1):
            alt_items.append(
                f'<div style="margin-bottom: 4px;">'
                f"<strong>별해 {idx} ({html.escape(alt.title)})</strong>: {alt.process_latex} "
                f"<span style=\"color:#0369A1;\">➔ [인정 기준] {alt.mapping_latex}</span></div>"
            )
        blocks.append(
            '<div class="section-title">3. 다른 풀이 및 대체 인정 기준</div>\n'
            '  <div class="alt-solutions-box">\n    '
            + "\n    ".join(alt_items)
            + "\n  </div>"
        )
        guardrail_sec_no = 4
    else:
        guardrail_sec_no = 3

    guard_items: Sequence[str] = list(default_common_guardrails_latex(spec)) + [
        f"<strong>[문항 특화]</strong> {g}" for g in spec.specific_guardrails_latex
    ]
    li_tags = "\n      ".join(f"<li>{item}</li>" for item in guard_items)
    blocks.append(
        f'<div class="section-title">{guardrail_sec_no}. AI 억지감점 방지 및 문항 특화 채점 원칙</div>\n'
        '  <div class="guardrails-box">\n'
        '    <ul class="guardrails-list">\n'
        f"      {li_tags}\n"
        "    </ul>\n"
        "  </div>"
    )

    content_html = "\n\n  ".join(blocks)

    meta_tags = (
        f'  <meta name="snorkl-spec-sha256" content="{spec.spec_sha256()}">\n'
        f'  <meta name="snorkl-final-answer" content="{html.escape(spec.final_answer_plain)}">'
    )
    rendered = re.sub(r"(<meta charset=\"UTF-8\">)", rf"\1\n{meta_tags}", tpl, count=1)
    rendered = rendered.replace("<!-- TITLE_PLACEHOLDER -->", html.escape(spec.title))
    rendered = rendered.replace("<!-- CONTENT_HTML_PLACEHOLDER -->", content_html)

    out_abs = os.path.abspath(out_html_path)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    with open(out_abs, "w", encoding="utf-8") as f:
        f.write(rendered)
    return out_abs


def build_all_outputs(
    spec: ProblemSpec,
    out_dir: str,
    max_pdf_pages: int = 1,
    validate: bool = True,
) -> dict[str, str]:
    """
    Build, render, and optionally validate all 3 deliverables from a single `ProblemSpec`.
    Raises `RuntimeError` immediately if rendering or validation fails.
    """
    out_abs = os.path.abspath(out_dir)
    os.makedirs(out_abs, exist_ok=True)
    slug = spec.resolved_slug()

    card_html = os.path.join(out_abs, f"{slug}_card.html")
    card_png = os.path.join(out_abs, f"{slug}_문제등록화면.png")
    rubric_md = os.path.join(out_abs, f"{slug}_정답_평가기준.md")
    sheet_html = os.path.join(out_abs, f"{slug}_sheet.html")
    sheet_pdf = os.path.join(out_abs, f"{slug}_교사참고용_채점기준표.pdf")

    build_card_html(spec, card_html)
    if not render_png(card_html, card_png, 1000, 500):
        raise RuntimeError(f"Failed to render problem card PNG: {card_png}")

    build_snorkl_markdown(spec, rubric_md)
    build_teacher_sheet_html(spec, card_png, sheet_html)
    if not render_pdf(sheet_html, sheet_pdf):
        raise RuntimeError(f"Failed to render teacher sheet PDF: {sheet_pdf}")

    paths = {
        "card_html": card_html,
        "card_png": card_png,
        "rubric_md": rubric_md,
        "sheet_html": sheet_html,
        "sheet_pdf": sheet_pdf,
    }

    if validate:
        from validate_outputs import validate_deliverable_set

        ok, errors = validate_deliverable_set(
            png_path=card_png,
            md_path=rubric_md,
            pdf_path=sheet_pdf,
            card_html_path=card_html,
            sheet_html_path=sheet_html,
            max_pdf_pages=max_pdf_pages,
        )
        if not ok:
            joined = "\n  - ".join(errors)
            raise RuntimeError(f"Output validation failed:\n  - {joined}")

    return paths
