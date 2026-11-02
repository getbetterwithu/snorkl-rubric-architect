#!/usr/bin/env bash
# ==============================================================================
# Snorkl Rubric Architect — Dual-Repo Sync & Publisher
# Pushes to Private Dev Repo and Public Distribution Repo
# Account: getbetterwithu (SSH Alias: github-getbetterwithu)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DEV_REMOTE="git@github-getbetterwithu:getbetterwithu/snorkl-rubric-architect-dev.git"
PUBLIC_REMOTE="git@github-getbetterwithu:getbetterwithu/snorkl-rubric-architect.git"

COMMIT_MSG="${1:-"Update Snorkl Rubric Architect Skill release"}"

echo "======================================================"
echo "  Snorkl Rubric Architect — 듀얼 레포 동기화 & 배포"
echo "  계정: getbetterwithu"
echo "======================================================"

# 1. Ensure git is initialized
if [ ! -d ".git" ]; then
    echo "▶ Git 초기화 중..."
    git init
    git branch -M main
fi

# 2. Add remotes if not set
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

# 3. Commit changes
git add -A
if git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "✓ 변경 사항이 이미 커밋되어 있습니다."
else
    echo "▶ 변경 사항 커밋 중: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG"
fi

# 4. Push to Private Dev Repo
echo "▶ [1/2] 비공개 개발 레포(origin: snorkl-rubric-architect-dev) 푸시 중..."
git push -u origin main

# 5. Push to Public Distribution Repo
echo "▶ [2/2] 공개 배포 레포(public: snorkl-rubric-architect) 푸시 중..."
git push -u public main

echo "======================================================"
echo "  🎉 두 저장소 모두 성공적으로 배포 및 동기화되었습니다!"
echo "  - 비공개 개발: https://github.com/getbetterwithu/snorkl-rubric-architect-dev"
echo "  - 공개 배포용: https://github.com/getbetterwithu/snorkl-rubric-architect"
echo "======================================================"
