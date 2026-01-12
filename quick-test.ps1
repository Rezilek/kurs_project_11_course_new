# quick-test.ps1
# Быстрая проверка проекта

Write-Host "Быстрая проверка проекта..." -ForegroundColor Cyan

# Проверка основных эндпоинтов
$endpoints = @(
    "http://localhost:8000/api/docs/",
    "http://localhost:8000/api/users/payments/success/",
    "http://localhost:8000/api/users/payments/cancel/",
    "http://localhost:8000/api/users/payments/buy/",
    "http://localhost:8000/api/users/payments/webhook/"
)

$results = @()

foreach ($url in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 3
        $results += @{Url = $url; Status = "✅"}
    } catch {
        $results += @{Url = $url; Status = "❌"}
    }
}

Write-Host "`nРезультаты проверки:" -ForegroundColor Yellow
foreach ($result in $results) {
    Write-Host "$($result.Status) $($result.Url)" -ForegroundColor $(if ($result.Status -eq "✅") { "Green" } else { "Red" })
}

# Проверка Stripe настроек
Write-Host "`nПроверка Stripe настроек:" -ForegroundColor Yellow
if (Test-Path .\.env) {
    $envContent = Get-Content .\.env
    if ($envContent -match "STRIPE_SECRET_KEY") {
        Write-Host "✅ STRIPE_SECRET_KEY настроен" -ForegroundColor Green
    } else {
        Write-Host "❌ STRIPE_SECRET_KEY не найден" -ForegroundColor Red
    }

    if ($envContent -match "STRIPE_PUBLISHABLE_KEY") {
        Write-Host "✅ STRIPE_PUBLISHABLE_KEY настроен" -ForegroundColor Green
    } else {
        Write-Host "❌ STRIPE_PUBLISHABLE_KEY не найден" -ForegroundColor Red
    }
} else {
    Write-Host "❌ .env файл не найден" -ForegroundColor Red
}

Write-Host "`nТест завершен!" -ForegroundColor Cyan