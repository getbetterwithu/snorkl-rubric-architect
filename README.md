# Snorkl Rubric Architect 📐✨ (v14.0)

> **Snorkl(스노클) 수학 서논술형 문항 캔버스 및 AI 4단계 정밀 루브릭 설계 시스템**  
> Windows 및 macOS를 모두 지원하며, Claude Code, Google Antigravity, OpenAI Codex, Aside 등 모든 주요 AI 에이전트에서 동작하는 초고속 크로스 플랫폼 수학 문항 저작 스킬입니다.

[![Skill Standard](https://img.shields.io/badge/Agent_Skill-v14.0-blue.svg)](https://github.com/getbetterwithu/snorkl-rubric-architect)
[![Platform](https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Claude_%7C_Gemini_%7C_Codex-green.svg)](https://github.com/getbetterwithu/snorkl-rubric-architect)
[![License](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE)

---

## 🚀 1초 원클릭 설치 (터미널 / PowerShell)

### 🪟 Windows (PowerShell)

#### 1) 일반 공개 배포판 설치 (선생님용)
```powershell
irm https://raw.githubusercontent.com/getbetterwithu/snorkl-rubric-architect/main/install.ps1 | iex
```

#### 2) 비공개 개발 레포(`dev`) 설치 (내부 테스트용)
Windows PowerShell에서 비공개 개발 레포를 설치할 때는 아래 명령어를 실행하세요:
```powershell
# GitHub CLI 로그인 상태일 때:
gh repo clone getbetterwithu/snorkl-rubric-architect-dev "$env:USERPROFILE\.snorkl-rubric-architect"
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.snorkl-rubric-architect\install.ps1" -Dev
```
*(또는 Git 인증이 되어 있는 경우)*:
```powershell
git clone https://github.com/getbetterwithu/snorkl-rubric-architect-dev.git "$env:USERPROFILE\.snorkl-rubric-architect"
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.snorkl-rubric-architect\install.ps1" -Dev
```

---

### 🍎 macOS / Linux (Terminal)
```bash
curl -fsSL https://raw.githubusercontent.com/getbetterwithu/snorkl-rubric-architect/main/install.sh | bash
```

> **설치 동작**: Mac 및 Windows에 설치된 **Claude Code, Gemini/Antigravity, Codex, Aside**를 자동 감지하여 모든 에이전트 경로에 Junction/Symlink로 즉시 연동하고, 최신 업데이트 명령어(`snorkl-update`)를 등록합니다.

---

## 🔄 원클릭 업데이트

터미널이나 PowerShell 어디서든 아래 한 줄로 최신 버전으로 즉시 갱신할 수 있습니다:
```bash
snorkl-update
```

---

## 💡 v14.0 핵심 가치 및 3종 세트 산출물

### 1. 최종 산출물 3종 영구 세트 (`./snorkl_output/`)
어떤 문항이든 작업이 완료되면 아래 3종 세트가 자동으로 저장됩니다:
1. 🖼️ **`[문제제목]_문제등록화면.png`**: (2000×1000 고화질) 스노클 화이트보드 문제 등록 배경 업로드용 카드. (대수 문항은 억지 그림 없이 지문 + 학생 필기용 쾌적한 여백으로 조판)
2. 📋 **`[문제제목]_정답_평가기준.md`**: 스노클 AI 루브릭 란에 복사해 넣는 **LaTeX 100% 배제 순수 텍스트(Plain Text)** 루브릭.
3. 📄 **`[문제제목]_교사참고용_채점기준표.pdf`**: 문제 카드 이미지 + KaTeX 수식 모범답안 + 4단계 배점표 + 가드레일이 A4 규격으로 정리된 **교사용 인쇄·보관용 PDF 문서**.

### 2. 수식 표기 이원화 (검토 편의 vs 스노클 호환)
- **대화창 검토 단계 (Step 1~4)**: 교사가 읽기 편하도록 $\frac{a}{b}$, $\sqrt{x}$, 연립방정식 대괄호 등 **교과서 수준의 LaTeX 마크다운 수식**으로 미려하게 조판.
- **최종 스노클 복사본**: 스노클 웹 시스템의 제약을 고려하여 **LaTeX를 100% 배제한 Plain Text**로 자동 변환 제공.

### 3. Step 1 필수 스키마 강제 & 성실한 안내 체크포인트
- 첫 턴에 2~3줄로 대충 때우거나 A안만 일방 통보하는 꼼수를 엄격히 차단.
- 단원 분석과 함께 **A안(추천), B안, C안 3종의 구체적인 예상 발문**을 필수 제시.
- 각 단계마다 교사가 무엇을 살펴봐야 하는지 **2~3가지 구체적인 검토 체크포인트**를 정중히 안내.

### 4. 초고속 크로스 플랫폼 렌더링
- 에이전트의 불필요한 내부 Vision 재판독 루프를 차단하여 Step 2 대기 시간을 **5~8초로 단축**.
- macOS(WebKit 바이너리 캐시)와 Windows(내장 Microsoft Edge 헤드리스)를 모두 지원하며, 렌더링 즉시 OS 기본 이미지 뷰어를 자동 팝업합니다.

---

## 🏛️ 4단계 점진적 인터랙션 워크플로우

```mermaid
flowchart TD
    In["교사의 입력 접수 (이미지 / 텍스트 / 아이디어)"] --> Step1["[전체 4단계 중 1단계: 심층 분석 & 출제 방향 제안]"]
    Step1 -->|교사의 방향 선택 및 합의| Step2["[전체 4단계 중 2단계: 문제 화면(캔버스) 검토]"]
    Step2 -->|교사 검토 및 승인 ('다음')| Step3["[전체 4단계 중 3단계: 기본 모범답안 & 4단계 배점표 검토]"]
    Step3 -->|교사 검토 및 승인 ('다음')| Step4["[전체 4단계 중 4단계: 다른 풀이 & 공통 채점 원칙 검토]"]
    Step4 -->|최종 승인 ('다음'/'완료')| Final["[최종 완결: 3종 세트 저장 & 스노클 링크 제공]"]
```

---

## 📂 파일 구조

```
snorkl-rubric-architect/
├── SKILL.md                          # 에이전트 공용 프롬프트 및 지침 (v14.0)
├── install.sh                        # macOS / Linux 원클릭 설치 스크립트
├── install.ps1                       # Windows PowerShell 원클릭 설치 스크립트
├── publish.sh                        # 듀얼 레포 동기화 배포 스크립트
├── README.md                         # 사용자 안내 문서
└── scripts/
    ├── template_card.html            # KaTeX 2000x1000 캔버스 마스터 HTML 템플릿
    ├── template_teacher_sheet.html   # 교사용 A4 채점기준표 인쇄 템플릿
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
