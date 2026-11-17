# Ejecuta un escalon de la prueba HTTP del modulo Dashboard y genera el reporte HTML.
#
# Uso:
#   .\jmeter\scripts\run-http.ps1 -Threads 10 -RampUp 10 -Duration 60 -Label http_10h
#   .\jmeter\scripts\run-http.ps1 -Threads 50 -RampUp 10 -Duration 60 -Label http_50h
#
# Requiere: JMeter en %USERPROFILE%\apache-jmeter-5.6.3 (o JMETER_HOME definido)
#           y el backend escuchando en http://127.0.0.1:8000

param(
    [int]$Threads = 10,
    [int]$RampUp = 10,
    [int]$Duration = 60,
    [string]$Label = "",
    [string]$ApiPassword = "Auditoria2026!"
)

$ErrorActionPreference = "Stop"

$scriptsDir = $PSScriptRoot
$jmeterDir  = Split-Path -Parent $scriptsDir
$plan       = Join-Path $jmeterDir "plans\02-http-dashboard.jmx"

$jmeterHome = if ($env:JMETER_HOME) { $env:JMETER_HOME } else { Join-Path $env:USERPROFILE "apache-jmeter-5.6.3" }
$jmeterBat  = Join-Path $jmeterHome "bin\jmeter.bat"
if (-not (Test-Path $jmeterBat)) { throw "No se encontro JMeter en $jmeterBat" }

# Verifica que el backend este arriba antes de gastar tiempo
try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health" -UseBasicParsing -TimeoutSec 5
    if ($health.StatusCode -ne 200) { throw "health devolvio $($health.StatusCode)" }
} catch {
    throw "El backend no responde en 127.0.0.1:8000. Levantelo antes de correr la prueba."
}

if (-not $Label) { $Label = "http_${Threads}h" }

$resultsDir = Join-Path $jmeterDir "resultados"
$reportsDir = Join-Path $jmeterDir "reportes"
$jtl    = Join-Path $resultsDir "$Label.jtl"
$report = Join-Path $reportsDir $Label

New-Item -ItemType Directory -Force -Path $resultsDir, $reportsDir | Out-Null
if (Test-Path $jtl)    { Remove-Item $jtl -Force }
if (Test-Path $report) { Remove-Item $report -Recurse -Force }

Write-Host "Ejecutando: $Threads usuarios, ramp-up $RampUp s, duracion $Duration s -> $Label"

& $jmeterBat -n -t $plan `
    "-Jthreads=$Threads" "-Jrampup=$RampUp" "-Jduration=$Duration" `
    "-Japi.password=$ApiPassword" `
    -l $jtl -e -o $report | Out-Null

if (-not (Test-Path $jtl)) { throw "JMeter no genero el archivo $jtl" }

$rows = Import-Csv $jtl
if ($rows.Count -eq 0) { throw "El JTL esta vacio" }

# El login del setUp no forma parte de la carga: se reporta aparte
$load = $rows | Where-Object { $_.label -ne 'POST /auth/login' }
if (-not $load) { $load = $rows }

function Get-Stats($set) {
    $n = $set.Count
    $e = ($set | Where-Object { $_.success -ne 'true' }).Count
    $el = $set | ForEach-Object { [double]$_.elapsed } | Sort-Object
    $avg = [math]::Round(($el | Measure-Object -Average).Average, 0)
    $p95 = $el[[math]::Floor($n * 0.95) - 1]
    $span = ([double]($set[-1].timeStamp) - [double]($set[0].timeStamp)) / 1000.0
    $rps = [math]::Round($n / [math]::Max($span, 1), 2)
    [pscustomobject]@{
        n = $n; err = $e; pct = [math]::Round(100.0 * $e / $n, 2)
        avg = $avg; p95 = $p95; rps = $rps
    }
}

$all = Get-Stats $load
Write-Host ""
Write-Host ("{0,-12} {1,7} {2,8} {3,8} {4,8} {5,9}" -f "escalon", "usuarios", "error%", "prom_ms", "p95_ms", "req/s")
Write-Host ("{0,-12} {1,7} {2,8} {3,8} {4,8} {5,9}" -f $Label, $Threads, $all.pct, $all.avg, $all.p95, $all.rps)
Write-Host ""
Write-Host "Detalle por peticion:"
Write-Host ("{0,-34} {1,7} {2,8} {3,8} {4,8}" -f "etiqueta", "muestras", "error%", "prom_ms", "p95_ms")
foreach ($lbl in ($load | Group-Object label | Sort-Object Name)) {
    $s = Get-Stats $lbl.Group
    Write-Host ("{0,-34} {1,7} {2,8} {3,8} {4,8}" -f $lbl.Name, $s.n, $s.pct, $s.avg, $s.p95)
}

$failed = ($load | Where-Object { $_.success -ne 'true' } | Select-Object -First 1)
if ($failed) {
    Write-Host ""
    Write-Host "Primer error: $($failed.responseCode) $($failed.responseMessage)"
}

Write-Host ""
Write-Host "Reporte HTML: $report\index.html"
