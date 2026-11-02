#!/usr/bin/env bash
# ==============================================================================
# Snorkl Rubric Architect — Universal Multi-Agent Installer & Updater
# Supports: Antigravity / Gemini, Claude Code, OpenAI Codex, Aside
# Repository: https://github.com/getbetterwithu/snorkl-rubric-architect
# ==============================================================================

set -e

INSTALL_DIR="$HOME/.snorkl-rubric-architect"
REPO_URL="https://github.com/getbetterwithu/snorkl-rubric-architect.git"

COLOR_GREEN="\033[0;32m"
COLOR_BLUE="\033[0;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_RESET="\033[0m"

echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}   Snorkl Rubric Architect Multi-Agent Installer      ${COLOR_RESET}"
echo -e "${COLOR_BLUE}   (Claude Code · Gemini/Antigravity · Codex · Aside) ${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"

# 1. Clone or Pull the repository
if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "${COLOR_YELLOW}▶ 기존 설치본 발견: 최신 버전으로 업데이트합니다...${COLOR_RESET}"
    git -C "$INSTALL_DIR" fetch origin main
    git -C "$INSTALL_DIR" reset --hard origin/main
else
    echo -e "${COLOR_YELLOW}▶ GitHub에서 최신 스킬을 다운로드합니다...${COLOR_RESET}"
    rm -rf "$INSTALL_DIR"
    git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
fi

# 2. Check dependencies (swift, python3)
echo -e "\n${COLOR_YELLOW}▶ 런타임 의존성 검사 중...${COLOR_RESET}"
if command -v python3 >/dev/null 2>&1; then
    echo -e "  ✓ Python 3: $(python3 --version)"
else
    echo -e "  ⚠ Python 3이 설치되어 있지 않습니다."
fi

if command -v swift >/dev/null 2>&1; then
    echo -e "  ✓ Swift (WebKit Renderer 지원): 사용 가능"
else
    echo -e "  ⚠ Swift를 찾을 수 없습니다. (macOS 환경 필요)"
fi

# 3. Detect and link to all agent directories
echo -e "\n${COLOR_YELLOW}▶ AI 에이전트 도구 자동 감지 및 심볼릭 링크 연결 중...${COLOR_RESET}"

LINKED_COUNT=0

# 3-1. Antigravity / Gemini
GEMINI_SKILLS_DIR="$HOME/.gemini/config/skills"
mkdir -p "$GEMINI_SKILLS_DIR"
ln -sfn "$INSTALL_DIR" "$GEMINI_SKILLS_DIR/snorkl-rubric-architect"
echo -e "  ${COLOR_GREEN}✓ Antigravity / Gemini${COLOR_RESET} 연결 완료: $GEMINI_SKILLS_DIR/snorkl-rubric-architect"
LINKED_COUNT=$((LINKED_COUNT + 1))

# 3-2. Claude Code
CLAUDE_SKILLS_DIR="$HOME/.claude/skills"
mkdir -p "$CLAUDE_SKILLS_DIR"
ln -sfn "$INSTALL_DIR" "$CLAUDE_SKILLS_DIR/snorkl-rubric-architect"
echo -e "  ${COLOR_GREEN}✓ Claude Code${COLOR_RESET} 연결 완료: $CLAUDE_SKILLS_DIR/snorkl-rubric-architect"
LINKED_COUNT=$((LINKED_COUNT + 1))

# 3-3. OpenAI Codex
CODEX_SKILLS_DIR="$HOME/.codex/skills"
mkdir -p "$CODEX_SKILLS_DIR"
ln -sfn "$INSTALL_DIR" "$CODEX_SKILLS_DIR/snorkl-rubric-architect"
echo -e "  ${COLOR_GREEN}✓ Codex${COLOR_RESET} 연결 완료: $CODEX_SKILLS_DIR/snorkl-rubric-architect"
LINKED_COUNT=$((LINKED_COUNT + 1))

# 3-4. Aside / Universal Agents
AGENTS_SKILLS_DIR="$HOME/.agents/skills"
mkdir -p "$AGENTS_SKILLS_DIR"
ln -sfn "$INSTALL_DIR" "$AGENTS_SKILLS_DIR/snorkl-rubric-architect"
echo -e "  ${COLOR_GREEN}✓ Aside / Universal Agents${COLOR_RESET} 연결 완료: $AGENTS_SKILLS_DIR/snorkl-rubric-architect"
LINKED_COUNT=$((LINKED_COUNT + 1))

# 4. Install update CLI command
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
cat << 'UPDATE_EOF' > "$BIN_DIR/snorkl-update"
#!/usr/bin/env bash
echo "▶ Snorkl Rubric Architect 업데이트 확인 중..."
git -C "$HOME/.snorkl-rubric-architect" pull --ff-only origin main
echo "✓ 최신 버전으로 업데이트되었습니다."
UPDATE_EOF
chmod +x "$BIN_DIR/snorkl-update"

echo -e "\n${COLOR_GREEN}======================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}  🎉 모든 AI 에이전트에 스킬 설치가 완료되었습니다!  ${COLOR_RESET}"
echo -e "${COLOR_GREEN}======================================================${COLOR_RESET}"
echo -e "총 ${LINKED_COUNT}개의 에이전트 경로에 단일 소스로 연동되었습니다."
echo -e "이제 Claude, Gemini, Codex 어디서든 스노클 문항 제작을 요청하시면 됩니다."
echo -e "\n- 수동 업데이트 명령어: ${COLOR_YELLOW}snorkl-update${COLOR_RESET} (또는 ~/.local/bin/snorkl-update)"
echo -e "- 설치 원본 디렉토리: ${COLOR_BLUE}$INSTALL_DIR${COLOR_RESET}"
