# deploy_to_mydevil.ps1
# PowerShell script to deploy Flask app to MyDevil.net

param(
    [string]$User = "Ryba",
    [string]$Server = "panel77.mydevil.net",
    [string]$RemotePath = "~/app",
    [string]$VenvPath = "~/flaskenv"
)

Write-Host "🚀 Starting deployment to MyDevil.net..." -ForegroundColor Cyan

# === STEP 1: Run local prep ===
if (Test-Path "prepare_mydevil_setup.py") {
    Write-Host "🧰 Running local setup script..."
    python prepare_mydevil_setup.py
} else {
    Write-Host "⚠️ No prepare_mydevil_setup.py found. Skipping preparation."
}

# === STEP 2: Upload files ===
# You need PuTTY's pscp.exe in PATH (or WinSCP CLI)
Write-Host "`n📦 Uploading project files to $User@$Server\:$RemotePath ..."

# Exclude virtual environments and caches
$exclude = @("venv", "__pycache__", ".git", ".venv")
$excludeArgs = $exclude | ForEach-Object { "--exclude=`"$_`"" } | Out-String

# Use tar + scp to compress and upload faster
$archive = "deploy_tmp.tar.gz"
if (Test-Path $archive) { Remove-Item $archive }

tar -czf $archive --exclude=.git --exclude=__pycache__ --exclude=venv --exclude=.venv *

if (-Not (Get-Command pscp -ErrorAction SilentlyContinue)) {
    Write-Host "❌ pscp.exe not found! Please install PuTTY and add pscp to PATH." -ForegroundColor Red
    Write-Host "Download: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html"
    exit 1
}

# Upload archive
pscp -r $archive "$User@$Server\:$RemotePath/"

# === STEP 3: Connect remotely to unpack and restart ===
Write-Host "`n Connecting via SSH to unpack and restart webapp..."
$commands = @"
cd $RemotePath
tar -xzf deploy_tmp.tar.gz
rm deploy_tmp.tar.gz
source $VenvPath/bin/activate
pip install -r requirements.txt
mkdir -p tmp
touch tmp/restart.txt
"@

# Save temporary command file
$cmdFile = "remote_cmds.txt"
$commands | Out-File $cmdFile -Encoding utf8

plink "$User@$Server" -m $cmdFile

Remove-Item $cmdFile
Remove-Item $archive
Write-Host "Deployment completed successfully!"