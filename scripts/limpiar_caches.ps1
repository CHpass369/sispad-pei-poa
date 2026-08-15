# ============================================================
# PIP-GAMS: Limpieza de caches regenerables
# Uso (PowerShell):  .\scripts\limpiar_caches.ps1
# ============================================================
# Elimina SOLO artefactos regenerables: caché de compilación
# Angular, caches de pytest y __pycache__ de Python.
# NO toca: node_modules, .venv, dist, media, .git, datos.
# Los caches se regeneran solos en el próximo build/test.
# ============================================================

$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $PSScriptRoot

$borrado = 0.0

# 1. Caché de compilación Angular (se regenera en ng build/test)
$angularCache = Join-Path $root 'frontend\sispoa\.angular\cache'
if (Test-Path -LiteralPath $angularCache) {
    $s = (Get-ChildItem -Path $angularCache -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
    Remove-Item -LiteralPath $angularCache -Recurse -Force
    $borrado += $s
    Write-Output ("OK  .angular/cache  ({0:N2} GB)" -f ($s / 1GB))
}

# 2. Caché de pytest
$pytestCache = Join-Path $root 'backend\.pytest_cache'
if (Test-Path -LiteralPath $pytestCache) {
    Remove-Item -LiteralPath $pytestCache -Recurse -Force
    Write-Output "OK  .pytest_cache"
}

# 3. Directorios __pycache__ de Python
$n = 0
Get-ChildItem -Path (Join-Path $root 'backend') -Recurse -Directory -Filter '__pycache__' -Force | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
    $n++
}
if ($n -gt 0) { Write-Output "OK  $n directorios __pycache__" }

# 4. Caché de Node (opcional: --todo la borra; requiere npm install luego)
$param = $args[0]
if ($param -eq '--todo') {
    $nodeCache = Join-Path $root 'frontend\sispoa\node_modules\.cache'
    if (Test-Path -LiteralPath $nodeCache) {
        Remove-Item -LiteralPath $nodeCache -Recurse -Force
        Write-Output "OK  node_modules/.cache"
    }
    $npmCache = Join-Path $env:LOCALAPPDATA 'npm-cache'
    if (Test-Path -LiteralPath $npmCache) {
        $s = (Get-ChildItem -Path $npmCache -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum
        Remove-Item -LiteralPath $npmCache -Recurse -Force
        $borrado += $s
        Write-Output ("OK  npm cache global  ({0:N2} GB)" -f ($s / 1GB))
    }
}

Write-Output ("Total liberado: {0:N2} GB" -f ($borrado / 1GB))
