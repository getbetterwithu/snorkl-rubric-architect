# Snorkl Rubric Architect 📐✨ (v14.1)

> **Snorkl(스노클) 수학 서논술형 문항 캔버스 및 AI 4단계 정밀 루브릭 설계 시스템**  
> Windows 및 macOS를 모두 지원하며, Claude Code, Google Antigravity, OpenAI Codex, Aside 등 모든 주요 AI 에이전트에서 동작하는 크로스 플랫폼 수학 문항 저작 스킬입니다.

[![Skill Standard](https://img.shields.io/badge/Agent_Skill-v14.1-blue.svg)](https://github.com/getbetterwithu/snorkl-rubric-architect)
[![Platform](https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Claude_%7C_Gemini_%7C_Codex-green.svg)](https://github.com/getbetterwithu/snorkl-rubric-architect)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

---

## 🚀 1초 원클릭 설치 (터미널 / PowerShell)

> 💡 **보안 안내**: 스크립트 실행 전 내용을 직접 확인하시려면 [install.ps1](https://github.com/getbetterwithu/snorkl-rubric-architect/blob/main/install.ps1) 또는 [install.sh](https://github.com/getbetterwithu/snorkl-rubric-architect/blob/main/install.sh)에서 코드를 검토하실 수 있습니다.

### 🪟 Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/getbetterwithu/snorkl-rubric-architect/main/install.ps1 | iex
```

### 🍎 macOS / Linux (Terminal)
```bash
curl -fsSL https://raw.githubusercontent.com/getbetterwithu/snorkl-rubric-architect/main/install.sh | bash
```

> **자동 감지 및 연동**: 시스템에 이미 설치된 **Claude Code, Gemini/Antigravity, Codex, Aside** 상위 폴더를 자동 감지하여 해당 에이전트 경로에만 심볼릭 링크/Junction으로 안전하게 연동합니다.

---

## 🔄 원클릭 업데이트

터미널이나 PowerShell 어디서든 아래 한 줄로 최신 버전으로 즉시 갱신할 수 있습니다:
```bash
snorkl-update
```

---

## 💡 v14.1 핵심 기능

### 1. 2022 개정 대한민국 중학 수학 전수 표준화 (`references/`)
- 중1부터 중3까지 총 21개 전체 대단원의 **교과서 대표 풀이(1순위)**를 의무화.
- 연립방정식 해의 개수 문제에서 고교 대수식 억지 증명($0 \cdot x = 0$)을 금지하고, 계수비($\frac{a}{a'} = \frac{b}{b'} = \frac{c}{c'}$)와 직선의 일치를 강제.
- 역비(Reverse Ratio), 사후 비례 설명, 부호 1회 이월 등 실전 교실형 방어 원칙 내장.

### 2. 1턴 1단계 Hard Stop 강제 (AI 자가 폭주 방지)
- AI가 자의적으로 단계를 건너뛰거나 한 번에 결과물을 쏟아내지 못하도록, 매 턴마다 출력을 즉시 중단하고 교사의 승인(`다음`, `좋아`)을 기다리도록 통제.

### 3. 최종 산출물 3종 세트 완결 (`./snorkl_output/`)
1. 🖼️ **`[문제제목]_문제등록화면.png`**: (2000×1000 고화질) 스노클 화이트보드 문제 등록 배경 업로드용 카드.
2. 📋 **`[문제제목]_정답_평가기준.md`**: 스노클 AI 루브릭 란에 복사해 넣는 **LaTeX 100% 배제 순수 텍스트(Plain Text)** 루브릭.
3. 📄 **`[문제제목]_교사참고용_채점기준표.pdf`**: 문제 카드 이미지 + KaTeX 수식 모범답안 + 4단계 배점표가 1~2페이지로 컴팩트하게 정리된 **교사용 인쇄·보관용 PDF 문서**.

### 4. 수식 표기 이원화 (검토 편의 vs 스노클 호환)
- **대화창 검토 단계 (Step 1~4)**: 교사가 읽기 편하도록 $\frac{a}{b}$, $\sqrt{x}$, 연립방정식 대괄호 등 **교과서 수준의 LaTeX 마크다운 수식**으로 미려하게 조판.
- **최종 스노클 복사본**: 스노클 웹 시스템의 제약을 고려하여 **LaTeX를 100% 배제한 Plain Text**로 자동 변환 제공.

---

## 🏛️ 4단계 점진적 인터랙션 파이프라인

```mermaid
flowchart TD
    In["교사의 입력 접수 (이미지 / 텍스트 / 아이디어)"] --> Step1["[1단계: 심층 분석 & 출제 방향 제안]"]
    Step1 --> Stop1["🛑 즉시 출력 중단 (Hard Stop) & 교사 피드백 대기"]
    Stop1 -->|교사의 방향 선택 및 승인| Step2["[2단계: 문제 화면(캔버스) 검토]"]
    Step2 --> Stop2["🛑 즉시 출력 중단 (Hard Stop) & 교사 피드백 대기"]
    Stop2 -->|교사 검토 및 승인 ('다음')| Step3["[3단계: 기본 모범답안 & 4단계 배점표 검토]"]
    Step3 --> Stop3["🛑 즉시 출력 중단 (Hard Stop) & 교사 피드백 대기"]
    Stop3 -->|교사 검토 및 승인 ('다음')| Step4["[4단계: 다른 풀이 & 공통 채점 원칙 검토]"]
    Step4 --> Stop4["🛑 즉시 출력 중단 (Hard Stop) & 교사 피드백 대기"]
    Stop4 -->|최종 승인 ('다음'/'완료')| Final["[최종 완결: 3종 세트 저장 & 스노클 링크 제공]"]
```

---

## 📂 파일 구조

```
snorkl-rubric-architect/
├── SKILL.md                          # 에이전트 공용 프롬프트 및 지침 (v14.1)
├── install.sh                        # macOS / Linux 원클릭 설치 스크립트
├── install.ps1                       # Windows PowerShell 원클릭 설치 스크립트
├── publish.sh                        # 듀얼 레포 동기화 배포 스크립트
├── README.md                         # 사용자 안내 문서
├── references/
│   └── korean_middle_math_standards.md # 2022 개정 중학 수학 21개 대단원 전수 표준 풀이 가이드
└── scripts/
    ├── template_card.html            # KaTeX 2000x1000 캔버스 마스터 HTML 템플릿
    ├── template_teacher_sheet.html   # 교사용 A4 1~2페이지 컴팩트 채점기준표 템플릿
    ├── snorkl_geometry_engine.py     # 기하 벡터 그래픽 및 클라우드 마스크 엔진
    ├── render_card.py                # Windows(Edge) & macOS(WebKit) 초고속 PNG/PDF 렌더러
    └── render_webkit.swift           # macOS WebKit 소스
```

---

## 🛠️ 지원 환경

- **OS**: Windows 10/11 (Microsoft Edge 기본 탑재), macOS (WebKit 지원)
- **AI 에이전트**:
  - Google Antigravity / Gemini CLI (`~/.gemini/config/skills/`)
  - Anthropic Claude Code (`~/.claude/skills/`)
  - OpenAI Codex (`~/.codex/skills/`)
  - Aside 및 Universal Agent Skills 지원 플랫폼 (`~/.agents/skills/`)

---

## 📄 라이선스

MIT License © 2026 BetterwithU & getbetterwithu. All rights reserved.
