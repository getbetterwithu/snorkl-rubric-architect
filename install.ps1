# ==============================================================================
# Snorkl Rubric Architect — Windows Multi-Agent Installer & Updater (PowerShell)
# Supports: Antigravity / Gemini, Claude Code, OpenAI Codex, Aside
# Repository: https://github.com/getbetterwithu/snorkl-rubric-architect
# ==============================================================================

$ErrorActionPreference = "Stop"

$InstallDir = "$env:USERPROFILE\.snorkl-rubric-architect"
$RepoUrl = "https://github.com/getbetterwithu/snorkl-rubric-architect.git"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   Snorkl Rubric Architect Windows Installer (v13.0)  " -ForegroundColor Cyan
Write-Host "   (Claude Code · Gemini/Antigravity · Codex · Aside) " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Check Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[오류] Git이 설치되어 있지 않습니다. Git for Windows를 먼저 설치해 주세요." -ForegroundColor Red
    exit 1
}

# 2. Clone or Update Repository
if (Test-Path "$InstallDir\.git") {
    Write-Host "▶ 기존 설치본 발견: 최신 버전으로 업데이트합니다..." -ForegroundColor Yellow
    git -C "$InstallDir" fetch origin main
    git -C "$InstallDir" reset --hard origin/main
} else {
    Write-Host "▶ GitHub에서 최신 스킬을 다운로드합니다..." -ForegroundColor Yellow
    if (Test-Path "$InstallDir") { Remove-Item -Recurse -Force "$InstallDir" }
    git clone --depth=1 "$RepoUrl" "$InstallDir"
}

# 3. Check Python and Edge/Chrome
Write-Host "`n▶ 런타임 환경 검사..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Python: $(python --version)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Python이 설치되어 있지 않거나 PATH에 없습니다. (Python 3 설치 권장)" -ForegroundColor Yellow
}

$EdgePath1 = "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe"
$EdgePath2 = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
if ((Test-Path $EdgePath1) -or (Test-Path $EdgePath2)) {
    Write-Host "  ✓ Microsoft Edge: 고해상도 헤드리스 렌더러 지원 확인" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Microsoft Edge를 찾을 수 없습니다. (기본 브라우저 사용)" -ForegroundColor Yellow
}

# 4. Link to Agent Skill Directories (Junction on Windows works without admin rights)
Write-Host "`n▶ AI 에이전트 도구 자동 감지 및 디렉토리 연결 중..." -ForegroundColor Yellow

$LinkedCount = 0

function Create-AgentLink($AgentName, $TargetPath) {
    param($AgentName, $TargetPath)
    $ParentDir = Split-Path $TargetPath -Parent
    if (-not (Test-Path $ParentDir)) { New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null }
    if (Test-Path $TargetPath) {
        # Check if already junction/symlink or folder
        cmd /c rmdir "$TargetPath" 2>$null
        if (Test-Path $TargetPath) { Remove-Item -Recurse -Force "$TargetPath" }
    }
    New-Item -ItemType Junction -Path "$TargetPath" -Target "$InstallDir" | Out-Null
    Write-Host "  ✓ $AgentName 연결 완료: $TargetPath" -ForegroundColor Green
    return 1
}

# 4-1. Gemini / Antigravity
$LinkedCount += Create-AgentLink "Antigravity / Gemini" "$env:USERPROFILE\.gemini\config\skills\snorkl-rubric-architect"

# 4-2. Claude Code
$LinkedCount += Create-AgentLink "Claude Code" "$env:USERPROFILE\.claude\skills\snorkl-rubric-architect"

# 4-3. OpenAI Codex
$LinkedCount += Create-AgentLink "OpenAI Codex" "$env:USERPROFILE\.codex\skills\snorkl-rubric-architect"

# 4-4. Aside / Universal Agents
$LinkedCount += Create-AgentLink "Aside / Universal Agents" "$env:USERPROFILE\.agents\skills\snorkl-rubric-architect"

# 5. Create snorkl-update command
$BinDir = "$env:USERPROFILE\bin"
if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }
$UpdateScript = @"
@echo off
echo ▶ Snorkl Rubric Architect 업데이트 확인 중...
git -C "%USERPROFILE%\.snorkl-rubric-architect" pull --ff-only origin main
echo ✓ 최신 버전으로 업데이트되었습니다.
pause
"@
Set-Content -Path "$BinDir\snorkl-update.cmd" -Value $UpdateScript -Encoding Ascii

# Add to user PATH if not present
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
}

Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "  🎉 Windows AI 에이전트에 스킬 설치가 완료되었습니다!  " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "총 $LinkedCount 개의 에이전트 경로에 Junction으로 연동되었습니다."
Write-Host "이제 Claude Code, Gemini, Codex 어디서든 스노클 문항 제작을 요청하시면 됩니다."
Write-Host "`n- 수동 업데이트 명령어: snorkl-update (또는 $BinDir\snorkl-update.cmd)"
Write-Host "- 설치 원본 디렉토리: $InstallDir"
