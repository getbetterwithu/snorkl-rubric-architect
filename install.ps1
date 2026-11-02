# ==============================================================================
# Snorkl Rubric Architect — Windows Multi-Agent Installer & Updater (v14.1)
# Supports: Antigravity / Gemini, Claude Code, OpenAI Codex, Aside
# Repositories:
#   - Public:  https://github.com/getbetterwithu/snorkl-rubric-architect
#   - Dev:     https://github.com/getbetterwithu/snorkl-rubric-architect-dev
# ==============================================================================

param(
    [string]$RepoUrl = "https://github.com/getbetterwithu/snorkl-rubric-architect.git",
    [string[]]$Agents = @(),
    [switch]$Dev,
    [switch]$AddToPath,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ($Dev) {
    $RepoUrl = "https://github.com/getbetterwithu/snorkl-rubric-architect-dev.git"
}

$InstallDir = "$env:USERPROFILE\.snorkl-rubric-architect"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "   Snorkl Rubric Architect Windows Installer (v14.1)  " -ForegroundColor Cyan
Write-Host "   (Claude Code · Gemini/Antigravity · Codex · Aside) " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
if ($Dev) {
    Write-Host "   [모드: 비공개 개발 레포 (snorkl-rubric-architect-dev)]" -ForegroundColor Magenta
}

# 1. Check Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[오류] Git이 설치되어 있지 않습니다. Git for Windows를 먼저 설치해 주세요." -ForegroundColor Red
    exit 1
}

# 2. Clone or Update Repository
if (Test-Path "$InstallDir\.git") {
    Write-Host "▶ 기존 설치본 발견: 최신 버전으로 업데이트합니다 (git pull --ff-only)..." -ForegroundColor Yellow
    git -C "$InstallDir" pull --ff-only origin main
} else {
    Write-Host "▶ 저장소에서 최신 스킬을 다운로드합니다 ($RepoUrl)..." -ForegroundColor Yellow
    if (Test-Path "$InstallDir") {
        if ($Force) {
            Remove-Item -Recurse -Force "$InstallDir"
        } else {
            Write-Host "[경고] 대상 디렉토리($InstallDir)가 이미 존재합니다. 덮어쓰려면 -Force 옵션을 사용하세요." -ForegroundColor Red
            exit 1
        }
    }
    git clone --depth=1 "$RepoUrl" "$InstallDir"
}

# 3. Check Python and Edge/Chrome
Write-Host "`n▶ 런타임 환경 검사..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "  ✓ Python: $(python --version)" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Python이 설치되어 있지 않거나 PATH에 없습니다. (Python 3 설치 권장)" -ForegroundColor Yellow
}

$ProgramFilesX86 = ${env:ProgramFiles(x86)}
$ProgramFiles64 = $env:ProgramFiles
$EdgePath1 = "$ProgramFilesX86\Microsoft\Edge\Application\msedge.exe"
$EdgePath2 = "$ProgramFiles64\Microsoft\Edge\Application\msedge.exe"
if ((Test-Path $EdgePath1) -or (Test-Path $EdgePath2)) {
    Write-Host "  ✓ Microsoft Edge: 고해상도 헤드리스 렌더러 및 PDF 인쇄 지원 확인" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Microsoft Edge를 찾을 수 없습니다. (Google Chrome 확인 권장)" -ForegroundColor Yellow
}

# 4. Link to Agent Skill Directories
Write-Host "`n▶ AI 에이전트 도구 감지 및 디렉토리 연결 중..." -ForegroundColor Yellow

$AgentMap = @{
    "gemini" = @{
        Name = "Antigravity / Gemini"
        Home = "$env:USERPROFILE\.gemini"
        Target = "$env:USERPROFILE\.gemini\config\skills\snorkl-rubric-architect"
    }
    "claude" = @{
        Name = "Claude Code"
        Home = "$env:USERPROFILE\.claude"
        Target = "$env:USERPROFILE\.claude\skills\snorkl-rubric-architect"
    }
    "codex" = @{
        Name = "OpenAI Codex"
        Home = "$env:USERPROFILE\.codex"
        Target = "$env:USERPROFILE\.codex\skills\snorkl-rubric-architect"
    }
    "agents" = @{
        Name = "Aside / Universal Agents"
        Home = "$env:USERPROFILE\.agents"
        Target = "$env:USERPROFILE\.agents\skills\snorkl-rubric-architect"
    }
}

$LinkedCount = 0

function Create-AgentLink($AgentKey, $AgentInfo) {
    $HomeDir = $AgentInfo.Home
    $TargetPath = $AgentInfo.Target
    $AgentName = $AgentInfo.Name

    # 감지 검사: 상위 에이전트 폴더 유무 확인 (명시적 지정이 없으면 미감지 시 건너뜀)
    if ($Agents.Count -eq 0 -and -not (Test-Path $HomeDir)) {
        Write-Host "  - $($AgentName): 미설치 (건너뜀)" -ForegroundColor DarkGray
        return 0
    }
    if ($Agents.Count -gt 0 -and $Agents -notcontains $AgentKey) {
        return 0
    }

    $ParentDir = Split-Path $TargetPath -Parent
    if (-not (Test-Path $ParentDir)) { New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null }

    # 대상 디렉토리 안전성 검사
    if (Test-Path $TargetPath) {
        $Item = Get-Item $TargetPath
        $IsJunction = ($Item.Attributes -band [IO.FileAttributes]::ReparsePoint) -or ($Item.LinkType -eq "Junction")
        if ($IsJunction) {
            # 기존 Junction 교체
            [IO.Directory]::Delete($TargetPath)
        } else {
            # 실제 폴더인 경우
            if ($Force) {
                Write-Host "  ⚠ $($AgentName): 기존 실제 폴더를 -Force에 의해 교체합니다." -ForegroundColor Yellow
                Remove-Item -Recurse -Force $TargetPath
            } else {
                Write-Host "  [주의] $TargetPath 경로는 심볼릭 링크가 아닌 실제 디렉토리입니다. 덮어쓰려면 -Force를 사용하세요." -ForegroundColor Red
                return 0
            }
        }
    }

    New-Item -ItemType Junction -Path "$TargetPath" -Target "$InstallDir" | Out-Null
    Write-Host "  ✓ $AgentName 연결 완료: $TargetPath" -ForegroundColor Green
    return 1
}

foreach ($Key in $AgentMap.Keys) {
    $LinkedCount += Create-AgentLink $Key $AgentMap[$Key]
}

# 5. Create snorkl-update command
$BinDir = "$env:USERPROFILE\bin"
if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }
$UpdateScript = @"
@echo off
echo [Snorkl] Checking for skill updates...
git -C "%USERPROFILE%\.snorkl-rubric-architect" pull --ff-only origin main
echo [Snorkl] Skill update complete.
"@
Set-Content -Path "$BinDir\snorkl-update.cmd" -Value $UpdateScript -Encoding Ascii

if ($AddToPath) {
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($UserPath -notlike "*$BinDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
        Write-Host "  ✓ 사용자 PATH에 $BinDir 추가 완료" -ForegroundColor Green
    }
} else {
    Write-Host "`n  [안내] $BinDir 경로를 PATH에 등록하지 않았습니다. (-AddToPath 옵션으로 등록 가능)" -ForegroundColor DarkGray
}

Write-Host "`n======================================================" -ForegroundColor Green
Write-Host "  🎉 Windows AI 에이전트에 스킬 설치가 완료되었습니다!  " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "총 $LinkedCount 개의 감지된 에이전트 경로에 Junction으로 연동되었습니다."
Write-Host "이제 Claude Code, Gemini, Codex 어디서든 스노클 문항 제작을 요청하시면 됩니다."
Write-Host "`n- 업데이트 명령어: $BinDir\snorkl-update.cmd (또는 git -C `"$InstallDir`" pull --ff-only)"
Write-Host "- 설치 원본 디렉토리: $InstallDir"
