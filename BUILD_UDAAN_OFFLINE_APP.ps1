$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Frontend = Join-Path $Root 'frontend'
$Backend = Join-Path $Root 'backend'
$Desktop = Join-Path $Root 'desktop'
$BuildVenv = Join-Path $Desktop '.build-venv'
$BuildPython = Join-Path $BuildVenv 'Scripts\python.exe'
$BuildDir = Join-Path $Desktop 'build'
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

function Step($Message) { Write-Host "`n================================================" -ForegroundColor Cyan; Write-Host $Message -ForegroundColor Cyan; Write-Host "================================================" -ForegroundColor Cyan }
function CheckExit($Message) { if ($LASTEXITCODE -ne 0) { throw "$Message failed with exit code $LASTEXITCODE" } }

try {
  Step '1/5 - Build the React frontend'
  Push-Location $Frontend
  npm install
  CheckExit 'Frontend npm install'
  npm run build
  CheckExit 'Frontend build'
  Pop-Location
  $BuildFrontend = Join-Path $BuildDir 'frontend\dist'
  New-Item -ItemType Directory -Force -Path $BuildFrontend | Out-Null
  Copy-Item -Path (Join-Path $Frontend 'dist\*') -Destination $BuildFrontend -Recurse -Force

  Step '2/5 - Prepare an isolated Python build environment'
  if (-not (Test-Path $BuildPython)) { python -m venv $BuildVenv; CheckExit 'Create build venv' }
  & $BuildPython -m pip install --upgrade pip
  CheckExit 'Upgrade build pip'
  & $BuildPython -m pip install -r (Join-Path $Backend 'requirements.txt') pyinstaller
  CheckExit 'Install backend/build dependencies'

  Step '3/5 - Bundle the Uvicorn server launcher as a local Windows executable'
  New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
  $DistBackend = Join-Path $BuildDir 'backend'
  $WorkPath = Join-Path $BuildDir 'pyinstaller-work'
  $SpecPath = Join-Path $BuildDir 'spec'
  & $BuildPython -m PyInstaller --noconfirm --clean --onedir --name UdaanBackend --distpath $DistBackend --workpath $WorkPath --specpath $SpecPath --paths $Backend --collect-all fastapi --collect-all starlette --collect-all pydantic --collect-all uvicorn --collect-all pypdf --collect-all docx (Join-Path $Backend 'launcher.py')
  CheckExit 'PyInstaller backend packaging'
  if (-not (Test-Path (Join-Path $DistBackend 'UdaanBackend\UdaanBackend.exe'))) { throw 'PyInstaller finished but UdaanBackend.exe was not found.' }

  Step '4/5 - Install desktop-shell build dependencies'
  Push-Location $Desktop
  npm install
  CheckExit 'Desktop npm install'

  Step '5/5 - Create the Windows installer'
  npm run dist:win
  CheckExit 'Electron Windows installer build'
  Pop-Location

  # Ensure the packaged launcher really includes a long-running Uvicorn entry point.
  $Installer = Get-ChildItem -Path (Join-Path $Desktop 'release') -Filter 'Udaan-Learning-Setup-*.exe' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if ($Installer) {
    Write-Host "`nSUCCESS! Installer created at:`n$($Installer.FullName)" -ForegroundColor Green
    Write-Host 'After installing, Udaan opens as a desktop app. Core lessons/quizzes use bundled local files and the local SQLite database.' -ForegroundColor Green
    Write-Host 'For AI translation / AI quiz generation offline, install/download the Ollama model once, then keep Ollama running locally.' -ForegroundColor Yellow
  } else {
    Write-Host "Build completed, but no installer file was found in desktop\release. Inspect build output above." -ForegroundColor Yellow
  }
} catch {
  Write-Host "`nBUILD STOPPED: $($_.Exception.Message)" -ForegroundColor Red
  Write-Host 'Keep this terminal open and share the last 20 lines of the error output for troubleshooting.' -ForegroundColor Yellow
  exit 1
} finally {
  if ((Get-Location).Path -eq $Frontend -or (Get-Location).Path -eq $Backend -or (Get-Location).Path -eq $Desktop) { Pop-Location -ErrorAction SilentlyContinue }
}
