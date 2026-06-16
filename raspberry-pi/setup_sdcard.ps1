# ============================================================
# DustCheck - SD 카드 boot 파티션 설정 스크립트
# ============================================================
# Raspberry Pi Imager로 OS를 구운 후, SD 카드를 다시 꽂고
# 이 스크립트를 실행하면 DustCheck에 필요한 모든 설정을 합니다.
#
# 실행: powershell -ExecutionPolicy Bypass -File setup_sdcard.ps1
# ============================================================

param(
    [string]$BootDrive = "D:",
    [string]$ProjectDir = (Split-Path -Parent $PSScriptRoot)
)

$RpiDir = Join-Path $ProjectDir "raspberry-pi"
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🌬️  DustCheck SD 카드 설정 스크립트         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────────────
# 1. boot 파티션 확인
# ─────────────────────────────────────────────
Write-Host "📁 [1/4] boot 파티션 확인 중..." -ForegroundColor Yellow

if (-not (Test-Path $BootDrive)) {
    Write-Host "❌ $BootDrive 드라이브를 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "   SD 카드가 꽂혀있는지 확인하세요." -ForegroundColor Red
    exit 1
}

$configTxt = Join-Path $BootDrive "config.txt"
if (-not (Test-Path $configTxt)) {
    Write-Host "❌ $configTxt 를 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "   Raspberry Pi OS boot 파티션이 맞는지 확인하세요." -ForegroundColor Red
    exit 1
}

Write-Host "✅ boot 파티션 확인: $BootDrive" -ForegroundColor Green

# ─────────────────────────────────────────────
# 2. config.txt에 I2C 활성화 추가
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "🔌 [2/4] I2C 활성화 설정..." -ForegroundColor Yellow

$configContent = Get-Content $configTxt -Raw

# I2C가 이미 활성화되어 있는지 확인
if ($configContent -match "(?m)^dtparam=i2c_arm=on") {
    Write-Host "✅ I2C가 이미 활성화되어 있습니다" -ForegroundColor Green
} else {
    # 주석 처리된 I2C 라인을 활성화
    if ($configContent -match "#dtparam=i2c_arm=on") {
        $configContent = $configContent -replace "#dtparam=i2c_arm=on", "dtparam=i2c_arm=on"
        Write-Host "✅ I2C 주석 해제 완료" -ForegroundColor Green
    } else {
        # [all] 섹션 앞에 추가
        $configContent = $configContent -replace "(?m)^\[all\]", "dtparam=i2c_arm=on`n`n[all]"
        Write-Host "✅ I2C 설정 추가 완료" -ForegroundColor Green
    }
    # UTF-8 BOM 없이 저장 (리눅스 호환)
    [System.IO.File]::WriteAllText($configTxt, $configContent, [System.Text.UTF8Encoding]::new($false))
}

# ─────────────────────────────────────────────
# 3. DustCheck 코드 복사
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "📂 [3/4] DustCheck 코드를 boot 파티션에 복사..." -ForegroundColor Yellow

$destDir = Join-Path $BootDrive "dustcheck-files"

# 기존 폴더가 있으면 삭제
if (Test-Path $destDir) {
    Remove-Item $destDir -Recurse -Force
}

New-Item -ItemType Directory -Path $destDir -Force | Out-Null

# 필요한 파일만 복사
$filesToCopy = @(
    "config.py",
    "sensor.py",
    "display.py",
    "monitor.py",
    "firebase_uploader.py",
    "csv_logger.py",
    "requirements.txt",
    "serviceAccountKey.json",
    "setup.sh",
    "setup_autostart.sh",
    "firstboot_setup.sh"
)

$copiedCount = 0
foreach ($file in $filesToCopy) {
    $src = Join-Path $RpiDir $file
    if (Test-Path $src) {
        Copy-Item $src -Destination $destDir
        $copiedCount++
        Write-Host "  ✅ $file" -ForegroundColor DarkGreen
    } else {
        Write-Host "  ⚠️  $file 없음 (건너뜀)" -ForegroundColor DarkYellow
    }
}

Write-Host "✅ $copiedCount 개 파일 복사 완료" -ForegroundColor Green

# ─────────────────────────────────────────────
# 4. cloud-init user-data에 firstboot 명령 추가
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "☁️ [4/4] cloud-init firstboot 설정..." -ForegroundColor Yellow

$userDataPath = Join-Path $BootDrive "user-data"

if (Test-Path $userDataPath) {
    $userData = Get-Content $userDataPath -Raw

    # 이미 dustcheck firstboot이 설정되어 있는지 확인
    if ($userData -match "firstboot_setup") {
        Write-Host "✅ firstboot 설정이 이미 존재합니다" -ForegroundColor Green
    } else {
        # runcmd 섹션에 firstboot 스크립트 실행 명령 추가
        if ($userData -match "(?m)^runcmd:") {
            # 기존 runcmd 섹션 끝에 추가
            $firstbootCmd = @"

  - [ chmod, +x, /boot/firmware/dustcheck-files/firstboot_setup.sh ]
  - [ /boot/firmware/dustcheck-files/firstboot_setup.sh ]
"@
            $userData = $userData.TrimEnd() + "`n" + $firstbootCmd + "`n"
        } else {
            # runcmd 섹션 새로 생성
            $firstbootCmd = @"

runcmd:
  - [ chmod, +x, /boot/firmware/dustcheck-files/firstboot_setup.sh ]
  - [ /boot/firmware/dustcheck-files/firstboot_setup.sh ]
"@
            $userData = $userData.TrimEnd() + "`n" + $firstbootCmd + "`n"
        }

        [System.IO.File]::WriteAllText($userDataPath, $userData, [System.Text.UTF8Encoding]::new($false))
        Write-Host "✅ cloud-init에 firstboot 명령 추가 완료" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  user-data 파일이 없습니다. Raspberry Pi Imager에서 사용자 설정을 했는지 확인하세요." -ForegroundColor DarkYellow
    Write-Host "   → 수동으로 firstboot_setup.sh를 실행해야 합니다." -ForegroundColor DarkYellow
}

# ─────────────────────────────────────────────
# 완료 요약
# ─────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ SD 카드 설정 완료!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  다음 단계:" -ForegroundColor White
Write-Host "  1. SD 카드를 안전하게 제거하세요" -ForegroundColor White
Write-Host "  2. 라즈베리파이 3에 SD 카드를 넣으세요" -ForegroundColor White
Write-Host "  3. SPS30 센서와 LCD를 연결하세요" -ForegroundColor White
Write-Host "  4. 이더넷 케이블을 연결하세요" -ForegroundColor White
Write-Host "  5. 전원을 켜세요 → 자동으로 DustCheck가 설치됩니다!" -ForegroundColor White
Write-Host ""
Write-Host "  첫 부팅 후 확인:" -ForegroundColor Yellow
Write-Host "  - SSH 접속: ssh lh@lh.local" -ForegroundColor Yellow
Write-Host "  - 설치 로그: cat /var/log/dustcheck-firstboot.log" -ForegroundColor Yellow
Write-Host "  - 서비스 상태: sudo systemctl status dustcheck" -ForegroundColor Yellow
Write-Host ""
