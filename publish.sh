#!/usr/bin/env bash
# ==============================================================================
# Snorkl Rubric Architect — Dual-Repo Verified Publisher (v15.0)
# Pushes to Private Dev Repo and Public Distribution Repo after safety & test gates
# Account: getbetterwithu (SSH Alias: github-getbetterwithu)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "SKILL.md" ] || [ ! -d ".git" ]; then
    echo "[오류] SKILL.md 또는 .git 저장소를 찾을 수 없습니다. 올바른 저장소 루트에서 실행하세요." >&2
    exit 1
fi

DEV_REMOTE="git@github-getbetterwithu:getbetterwithu/snorkl-rubric-architect-dev.git"
PUBLIC_REMOTE="git@github-getbetterwithu:getbetterwithu/snorkl-rubric-architect.git"
COMMIT_MSG="${1:-"Update Snorkl Rubric Architect Skill release"}"

echo "======================================================"
echo "  Snorkl Rubric Architect — 듀얼 레포 검증 & 배포 (v15.0)"
echo "  계정: getbetterwithu"
echo "======================================================"

# 1. Safety guard against secrets or temporary output folders
FORBIDDEN_MATCHES="$(find . -maxdepth 3 \( -name ".env*" -o -name "*.pem" -o -name "*.key" -o -name "*secret*" \) -not -path "./.git/*" || true)"
if [ -n "$FORBIDDEN_MATCHES" ]; then
    echo "[보안 차단] 민감 파일 패턴이 감지되어 배포를 중단합니다:" >&2
    echo "$FORBIDDEN_MATCHES" >&2
    exit 1
fi

# 2. Run automated regression tests before publishing
PYTHON_BIN="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python"
fi
echo "▶ 자동 회귀 테스트(tests/test_core.py) 실행 중..."
"$PYTHON_BIN" -m unittest discover -s tests -v

# 3. Configure dual remotes
if ! git remote | grep -q "^origin$"; then
    git remote add origin "$DEV_REMOTE"
else
    git remote set-url origin "$DEV_REMOTE"
fi

if ! git remote | grep -q "^public$"; then
    git remote add public "$PUBLIC_REMOTE"
else
    git remote set-url public "$PUBLIC_REMOTE"
fi

echo "▶ 대상 원격 저장소 확인:"
git remote -v

# 4. Stage & commit
git add -A
if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "✓ 변경 사항이 이미 커밋되어 있습니다."
else
    echo "▶ 변경 사항 커밋 중: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
fi

# 5. Push to Private Dev Repo & Public Repo
echo "▶ [1/2] 비공개 개발 레포(origin) 푸시 중..."
git push -u origin main

echo "▶ [2/2] 공개 배포 레포(public) 푸시 중..."
git push -u public main

echo "======================================================"
echo "  🎉 검증 통과 및 두 저장소 동기화가 완료되었습니다!"
echo "======================================================"
