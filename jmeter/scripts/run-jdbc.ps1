# Ejecuta un escalon de la prueba JDBC y genera el reporte HTML.
#
# Uso:
#   .\jmeter\scripts\run-jdbc.ps1 -Threads 10 -RampUp 10 -Duration 60
#   .\jmeter\scripts\run-jdbc.ps1 -Threads 50 -RampUp 50 -Duration 120 -Label r50
#
# Requiere: JMeter en %USERPROFILE%\apache-jmeter-5.6.3 (o JMETER_HOME definido).

param(
    [int]$Threads = 10,
    [int]$RampUp = 10,
    [int]$Duration = 60,
    [string]$Label = ""
)

$ErrorActionPreference = "Stop"

$scriptsDir = $PSScriptRoot
$jmeterDir  = Split-Path -Parent $scriptsDir
$root       = Split-Path -Parent $jmeterDir
$plan       = Join-Path $jmeterDir "plans\01-jdbc-hardening.jmx"

$jmeterHome = if ($env:JMETER_HOME) { $env:JMETER_HOME } else { Join-Path $env:USERPROFILE "apache-jmeter-5.6.3" }
$jmeterBat  = Join-Path $jmeterHome "bin\jmeter.bat"
if (-not (Test-Path $jmeterBat)) { throw "No se encontro JMeter en $jmeterBat" }

# Password desde .env (no se escribe en el plan ni en el repositorio)
$envFile = Join-Path $root ".env"
if (-not (Test-Path $envFile)) { throw "Falta .env en la raiz del proyecto" }
$dbPass = (Select-String -Path $envFile -Pattern '^DB_PASSWORD=' | Select-Object -First 1)
if (-not $dbPass) { throw "DB_PASSWORD no esta definido en .env" }
$dbPass = $dbPass.Line -replace '^DB_PASSWORD=', ''

if (-not $Label) { $Label = "jdbc_${Threads}h" }

$resultsDir = Join-Path $jmeterDir "resultados"
$reportsDir = Join-Path $jmeterDir "reportes"
$jtl    = Join-Path $resultsDir "$Label.jtl"
$report = Join-Path $reportsDir $Label

New-Item -ItemType Directory -Force -Path $resultsDir, $reportsDir | Out-Null
if (Test-Path $jtl)    { Remove-Item $jtl -Force }
if (Test-Path $report) { Remove-Item $report -Recurse -Force }

Write-Host "Ejecutando: $Threads hilos, ramp-up $RampUp s, duracion $Duration s -> $Label"

& $jmeterBat -n -t $plan `
    "-Jthreads=$Threads" "-Jrampup=$RampUp" "-Jduration=$Duration" `
    "-Jdb.password=$dbPass" `
    -l $jtl -e -o $report | Out-Null

if (-not (Test-Path $jtl)) { throw "JMeter no genero el archivo $jtl" }

# Resumen calculado desde el JTL
$rows = Import-Csv $jtl
$total = $rows.Count
if ($total -eq 0) { throw "El JTL esta vacio" }

$errors = ($rows | Where-Object { $_.success -ne 'true' }).Count
$pctErr = [math]::Round(100.0 * $errors / $total, 2)
$elapsed = $rows | ForEach-Object { [double]$_.elapsed } | Sort-Object
$avg = [math]::Round(($elapsed | Measure-Object -Average).Average, 0)
$p95 = $elapsed[[math]::Floor($elapsed.Count * 0.95) - 1]
$start = [double]($rows | Select-Object -First 1).timeStamp
$end   = [double]($rows | Select-Object -Last 1).timeStamp
$rps   = [math]::Round($total / [math]::Max(($end - $start) / 1000.0, 1), 2)

Write-Host ""
Write-Host ("{0,-8} {1,6} {2,8} {3,10} {4,8} {5,10}" -f "escalon","hilos","error%","prom_ms","p95_ms","req/s")
Write-Host ("{0,-8} {1,6} {2,8} {3,10} {4,8} {5,10}" -f $Label,$Threads,$pctErr,$avg,$p95,$rps)
Write-Host ""
Write-Host "Reporte HTML: $report\index.html"
