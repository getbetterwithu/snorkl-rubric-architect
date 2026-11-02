# Snorkl Rubric Architect 📐✨ (v13.1)

> **Snorkl(스노클) 수학 서논술형 문항 캔버스 및 AI 4단계 정밀 루브릭 설계 시스템**  
> Windows 및 macOS를 모두 지원하며, Claude Code, Google Antigravity, OpenAI Codex, Aside 등 모든 주요 AI 에이전트에서 동작하는 초고속 크로스 플랫폼 수학 문항 저작 스킬입니다.

[![Skill Standard](https://img.shields.io/badge/Agent_Skill-v13.1-blue.svg)](https://github.com/getbetterwithu/snorkl-rubric-architect)
[![Platform](https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Claude_%7C_Gemini_%7C_Codex-green.svg)](https://github.com/getbetterwithu/snorkl-rubric-architect)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

---

## 🚀 1초 원클릭 설치 (터미널 / PowerShell)

사용하시는 운영체제(OS)에 맞춰 아래 한 줄 명령어를 복사해 터미널 또는 PowerShell에 붙여넣으세요:

### 🪟 Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/getbetterwithu/snorkl-rubric-architect/main/install.ps1 | iex
```

### 🍎 macOS / Linux (Terminal)
```bash
curl -fsSL https://raw.githubusercontent.com/getbetterwithu/snorkl-rubric-architect/main/install.sh | bash
```

> **설치 동작**: Mac 및 Windows에 설치된 **Claude Code, Gemini/Antigravity, Codex, Aside**를 자동 감지하여 모든 에이전트 경로에 스킬을 즉시 연동하고, 최신 업데이트 명령어(`snorkl-update`)를 등록합니다.

---

## 🔄 원클릭 업데이트

터미널이나 PowerShell 어디서든 아래 한 줄로 최신 버전으로 즉시 갱신할 수 있습니다:
```bash
snorkl-update
```

---

## ⚡ v13.1 핵심 가치 및 속도 최적화

### 1. 초고속 단회 렌더링 (자가 판독 루프 전면 차단)
- AI 모델이 생성된 이미지를 스스로 읽고 고치는 내부 반복 루프를 금지하여, Step 2 대기 시간을 **40~50초에서 5~8초로 대폭 단축**했습니다.
- macOS에서는 네이티브 WebKit 바이너리 캐시로 0.8초 만에 렌더링하며, Windows에서는 내장 Microsoft Edge 헤드리스 엔진을 활용합니다.

### 2. 문항 유형별 스마트 분기 (도형 vs 순수 대수 0초 직행)
- **기하/도형 문항**: KaTeX 지문과 교과서 표준 순수 원호 치수선, 올록볼록 클라우드 마스크가 적용된 2000×1000 고화질 기하 카드를 작도합니다.
- **순수 대수/방정식 문항**: 억지로 오른쪽 영역에 무언가를 채우려다 풀이나 힌트를 노출하는 오류를 원천 차단하고, 이미지 렌더링 과정을 건너뛰어 지문 확인 후 곧바로 루브릭 설계로 직행합니다.

### 3. 직관적인 산출물 명명 및 `./snorkl_output/` 자동 저장
- 파일의 역할을 한눈에 파악할 수 있도록 표준 명칭으로 영구 저장합니다:
  - `./snorkl_output/[문제제목]_정답_평가기준.md` (스노클 복사용 통합 루브릭)
  - `./snorkl_output/[문제제목]_문제등록화면.png` (2000×1000 화이트보드 등록용 카드)

### 4. 스노클 붙여넣기용 순수 텍스트 루브릭 (LaTeX 100% 배제)
- 스노클(Snorkl) 웹 시스템은 LaTeX 문법을 렌더링하지 못하므로, **최종 복사용 루브릭은 키보드 및 표준 유니코드 기반의 순수 일반 텍스트(Plain Text)로만 작성**하여 스노클에 붙여넣었을 때 코드가 깨지지 않습니다.

### 5. 전 단계 진행 상황 가시화 및 비재촉형 정중한 검토 유도
- 매 턴 첫 줄에 `[전체 4단계 중 M단계 진행 중: 단계명]`을 명시하여 현재 위치와 완결까지의 여정을 안내합니다.
- *"내용을 살펴보시고 틀린 점, 개선해야 할 점, 의견이 있으시면 편하게 말씀해 주세요. 없으시면 '다음'(또는 '좋아')이라고 말씀해 주시면 다음 단계로 진행하겠습니다."*

### 6. 교사 커스텀 답안 반영 옵션 (Step 3)
- AI가 기본 초안을 먼저 주되, 선생님만의 모범답안 텍스트나 손풀이 사진을 보내주시면 그 호흡에 맞춰 4단계 배점표(0.5점 기준)를 재구성해 드립니다.

### 7. 스노클 교사 대시보드 바로가기 링크 제공
- 작업 완료 시 곧바로 스노클로 이동해 과제를 배부할 수 있도록 `[Snorkl 교사 대시보드 바로가기](https://teacher.snorkl.app/home)` 링크를 안내합니다.

---

## 🏛️ 4단계 점진적 인터랙션 워크플로우

```mermaid
flowchart TD
    In["교사의 입력 접수 (이미지 / 텍스트 / 아이디어)"] --> Step1["[전체 4단계 중 1단계: 심층 분석 & 출제 방향 제안]"]
    Step1 -->|교사의 방향 선택 및 합의| Step2["[전체 4단계 중 2단계: 문제 화면(캔버스) 검토]"]
    Step2 -->|교사 검토 및 승인 ('다음')| Step3["[전체 4단계 중 3단계: 기본 모범답안 & 4단계 배점표 검토]"]
    Step3 -->|교사 검토 및 승인 ('다음')| Step4["[전체 4단계 중 4단계: 다른 풀이 & 공통 채점 원칙 검토]"]
    Step4 -->|최종 승인 ('다음'/'완료')| Final["[최종 완결: snorkl_output/ 저장 & 스노클 링크 제공]"]
```

---

## 📂 파일 구조

```
snorkl-rubric-architect/
├── SKILL.md                          # 에이전트 공용 프롬프트 및 지침 (v13.1)
├── install.sh                        # macOS / Linux 원클릭 설치 스크립트
├── install.ps1                       # Windows PowerShell 원클릭 설치 스크립트
├── publish.sh                        # 듀얼 레포 동기화 배포 스크립트
├── README.md                         # 사용자 안내 문서
└── scripts/
    ├── template_card.html            # KaTeX 2000x1000 캔버스 마스터 HTML 템플릿
    ├── snorkl_geometry_engine.py     # 기하 벡터 그래픽 및 클라우드 마스크 엔진
    ├── render_card.py                # Windows(Edge) & macOS(WebKit 바이너리 캐시) 초고속 렌더러
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
