$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$backend = Join-Path $project 'backend'
$envFile = Join-Path $backend '.env'
$docker = Get-Command docker -ErrorAction SilentlyContinue
$installedPostgres = Test-Path 'C:\Program Files\PostgreSQL\17\data\PG_VERSION'

if (-not (Test-Path $envFile)) {
  $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
  $adminBytes = New-Object byte[] 36
  $agentBytes = New-Object byte[] 36
  $rng.GetBytes($adminBytes)
  $rng.GetBytes($agentBytes)
  $admin = [Convert]::ToBase64String($adminBytes)
  $agent = [Convert]::ToBase64String($agentBytes)
  $rng.Dispose()
  $content = Get-Content -LiteralPath (Join-Path $backend '.env.example') -Raw
  $content = $content.Replace('replace-with-a-long-random-admin-secret', $admin).Replace('replace-with-a-long-random-agent-secret', $agent)
  if ($installedPostgres) {
    $content = $content.Replace('DATABASE_URL=postgresql://netcompare:netcompare_local_dev@localhost:5432/netcompare?schema=public', 'DATABASE_URL=postgresql://postgres:CHANGE_ME@localhost:5432/postgres?schema=public')
  }
  Set-Content -LiteralPath $envFile -Value $content
  Write-Host 'Created backend/.env with local development credentials.'
}

if (Select-String -LiteralPath $envFile -Pattern '^DATABASE_URL=.*CHANGE_ME' -Quiet) {
  throw 'Set the PostgreSQL password in backend\.env first. Open it with: notepad .\backend\.env, replace CHANGE_ME, save, and rerun this script.'
}

$ready = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $ready -and $installedPostgres) {
  try {
    $postgresService = Get-Service -Name 'postgresql-x64-17' -ErrorAction Stop
    if ($postgresService.Status -ne 'Running') { Start-Service -Name $postgresService.Name }
  } catch {
    Write-Host 'Could not start the PostgreSQL service. If access is denied, rerun this script from an elevated PowerShell window.'
  }
}
if (-not $ready) {
  $ready = Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue
}
if (-not $ready -and $docker) {
  Push-Location $project
  try { docker compose up -d db } finally { Pop-Location }
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if (Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue) { $ready = $true; break }
    Start-Sleep -Seconds 2
  }
}
if (-not $ready) {
  throw 'No PostgreSQL server is listening on localhost:5432. Start the PostgreSQL service from an elevated PowerShell, then rerun this script.'
}

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw 'Node.js 20+ is required. Install Node.js and rerun.' }
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
  $cli = Join-Path $project 'work\npm-bootstrap\package\bin\npm-cli.js'
  if (-not (Test-Path $cli)) { throw 'npm is not on PATH and the project npm bootstrap is missing. Install Node.js with npm.' }
  $shimDir = Join-Path $project 'work\npm-bootstrap\shim'
  New-Item -ItemType Directory -Force -Path $shimDir | Out-Null
  $shim = Join-Path $shimDir 'npm.cmd'
  $shimContent = "@echo off" + [Environment]::NewLine + '"%NETCOMPARE_NODE%" "%NETCOMPARE_NPM_CLI%" %*'
  Set-Content -LiteralPath $shim -Value $shimContent
  $env:NETCOMPARE_NODE = $node.Source
  $env:NETCOMPARE_NPM_CLI = $cli
  $env:PATH = "$shimDir;$env:PATH"
}

Push-Location $backend
try {
  npm install
  npm run prisma:generate
  npm run prisma:migrate
  npm run dev
} finally { Pop-Location }