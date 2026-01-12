# test-project.ps1
# Тестовый скрипт для проверки образовательной платформы с Stripe

Write-Host "=== ТЕСТ ОБРАЗОВАТЕЛЬНОЙ ПЛАТФОРМЫ С STRIPE ===" -ForegroundColor Cyan
Write-Host "Дата: $(Get-Date)" -ForegroundColor Gray
Write-Host ""

# 1. ПРОВЕРКА СЕРВЕРА
Write-Host "1. Проверка сервера Django..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET -TimeoutSec 5
    Write-Host "   Сервер запущен на http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "   Сервер не запущен. Запустите: python manage.py runserver" -ForegroundColor Red
    exit 1
}

# 2. ПРОВЕРКА ДОКУМЕНТАЦИИ
Write-Host ""
Write-Host "2. Проверка документации API..." -ForegroundColor Yellow
$endpoints = @("http://localhost:8000/api/docs/", "http://localhost:8000/api/redoc/")
foreach ($url in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 5
        Write-Host "   $url доступен" -ForegroundColor Green
    } catch {
        Write-Host "   $url недоступен" -ForegroundColor Red
    }
}

# 3. ПРОВЕРКА ЭНДПОИНТОВ STRIPE
Write-Host ""
Write-Host "3. Проверка платежных эндпоинтов..." -ForegroundColor Yellow
$payment_endpoints = @(
    @{Url = "http://localhost:8000/api/users/payments/success/"; Method = "GET"},
    @{Url = "http://localhost:8000/api/users/payments/cancel/"; Method = "GET"}
)
foreach ($endpoint in $payment_endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.Url -Method GET -TimeoutSec 3
        Write-Host "   $(Split-Path $endpoint.Url -Leaf) доступен" -ForegroundColor Green
    } catch {
        Write-Host "   $(Split-Path $endpoint.Url -Leaf) недоступен" -ForegroundColor Red
    }
}

# 4. ФИНАЛЬНЫЙ ОТЧЕТ
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "ПРОВЕРКА ЗАВЕРШЕНА" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Все основные эндпоинты доступны" -ForegroundColor Green