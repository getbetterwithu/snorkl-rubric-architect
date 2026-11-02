#!/usr/bin/env bash
# ==============================================================================
# Snorkl Rubric Architect — Universal Multi-Agent Installer & Updater (v14.1)
# Supports: Antigravity / Gemini, Claude Code, OpenAI Codex, Aside
# Repository: https://github.com/getbetterwithu/snorkl-rubric-architect
# ==============================================================================

set -e

INSTALL_DIR="$HOME/.snorkl-rubric-architect"
REPO_URL="https://github.com/getbetterwithu/snorkl-rubric-architect.git"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dev) REPO_URL="https://github.com/getbetterwithu/snorkl-rubric-architect-dev.git" ;;
        --force) FORCE=1 ;;
        *) echo "알 수 없는 옵션: $1"; exit 1 ;;
    esac
    shift
done

COLOR_GREEN="\033[0;32m"
COLOR_BLUE="\033[0;34m"
COLOR_YELLOW="\033[1;33m"
COLOR_GRAY="\033[1;30m"
COLOR_RESET="\033[0m"

echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}   Snorkl Rubric Architect Multi-Agent Installer v14.1 ${COLOR_RESET}"
echo -e "${COLOR_BLUE}   (Claude Code · Gemini/Antigravity · Codex · Aside) ${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"

# 1. Clone or Pull the repository
if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "${COLOR_YELLOW}▶ 기존 설치본 발견: 최신 버전으로 업데이트합니다 (pull --ff-only)...${COLOR_RESET}"
    git -C "$INSTALL_DIR" pull --ff-only origin main
else
    echo -e "${COLOR_YELLOW}▶ 최신 스킬을 다운로드합니다 ($REPO_URL)...${COLOR_RESET}"
    if [ -d "$INSTALL_DIR" ]; then
        if [ "$FORCE" = "1" ]; then
            rm -rf "$INSTALL_DIR"
        else
            echo "오류: 대상 폴더($INSTALL_DIR)가 이미 존재합니다. 덮어쓰려면 --force 옵션을 사용하세요."
            exit 1
        fi
    fi
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

# 3. Detect and link to detected agent directories
echo -e "\n${COLOR_YELLOW}▶ AI 에이전트 도구 감지 및 심볼릭 링크 연결 중...${COLOR_RESET}"

LINKED_COUNT=0

link_agent() {
    local AGENT_NAME="$1"
    local AGENT_HOME="$2"
    local TARGET_DIR="$3"

    if [ -d "$AGENT_HOME" ]; then
        mkdir -p "$(dirname "$TARGET_DIR")"
        if [ -e "$TARGET_DIR" ] && [ ! -L "$TARGET_DIR" ]; then
            if [ "$FORCE" = "1" ]; then
                rm -rf "$TARGET_DIR"
            else
                echo -e "  ${COLOR_YELLOW}⚠ $AGENT_NAME:${COLOR_RESET} $TARGET_DIR 경로가 실제 디렉토리입니다. (--force 필요)"
                return
            fi
        fi
        ln -sfn "$INSTALL_DIR" "$TARGET_DIR"
        echo -e "  ${COLOR_GREEN}✓ $AGENT_NAME${COLOR_RESET} 연결 완료: $TARGET_DIR"
        LINKED_COUNT=$((LINKED_COUNT + 1))
    else
        echo -e "  ${COLOR_GRAY}- $AGENT_NAME: 미설치 (건너뜀)${COLOR_RESET}"
    fi
}

link_agent "Antigravity / Gemini" "$HOME/.gemini" "$HOME/.gemini/config/skills/snorkl-rubric-architect"
link_agent "Claude Code" "$HOME/.claude" "$HOME/.claude/skills/snorkl-rubric-architect"
link_agent "OpenAI Codex" "$HOME/.codex" "$HOME/.codex/skills/snorkl-rubric-architect"
link_agent "Aside / Universal Agents" "$HOME/.agents" "$HOME/.agents/skills/snorkl-rubric-architect"

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
echo -e "${COLOR_GREEN}  🎉 감지된 AI 에이전트에 스킬 설치가 완료되었습니다!  ${COLOR_RESET}"
echo -e "${COLOR_GREEN}======================================================${COLOR_RESET}"
echo -e "총 ${LINKED_COUNT}개의 에이전트 경로에 단일 소스로 연동되었습니다."
echo -e "이제 Claude, Gemini, Codex 어디서든 스노클 문항 제작을 요청하시면 됩니다."
echo -e "\n- 업데이트 명령어: ${COLOR_YELLOW}$BIN_DIR/snorkl-update${COLOR_RESET}"
echo -e "- 설치 원본 디렉토리: ${COLOR_BLUE}$INSTALL_DIR${COLOR_RESET}"
