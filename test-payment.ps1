# test-payment.ps1
# Скрипт для тестирования платежной системы

param(
    [string]$Email = "test@example.com",
    [string]$Password = "testpassword123",
    [int]$CourseId = 1
)

Write-Host "=== ТЕСТИРОВАНИЕ ПЛАТЕЖНОЙ СИСТЕМЫ STRIPE ===" -ForegroundColor Cyan

# 1. АВТОРИЗАЦИЯ
Write-Host ""
Write-Host "1. Получение JWT токена..." -ForegroundColor Yellow
$authBody = @{
    username = $Email
    password = $Password
} | ConvertTo-Json

try {
    $tokenResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/users/token/" `
        -Method POST `
        -Headers @{"Content-Type" = "application/json"} `
        -Body $authBody

    $accessToken = $tokenResponse.access
    Write-Host "   Токен получен: $($accessToken.Substring(0, 20))..." -ForegroundColor Green
} catch {
    Write-Host "   Ошибка авторизации: $_" -ForegroundColor Red
    exit 1
}

# 2. СОЗДАНИЕ ПЛАТЕЖА
Write-Host ""
Write-Host "2. Создание платежа для курса ID: $CourseId..." -ForegroundColor Yellow
$paymentBody = @{
    item_type = "course"
    item_id = $CourseId
} | ConvertTo-Json

try {
    $paymentResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/users/payments/buy/" `
        -Method POST `
        -Headers @{
            "Authorization" = "Bearer $accessToken"
            "Content-Type" = "application/json"
        } `
        -Body $paymentBody

    Write-Host "   Платеж создан!" -ForegroundColor Green
    Write-Host "   - ID платежа: $($paymentResponse.payment_id)" -ForegroundColor Gray
    Write-Host "   - Сумма: $($paymentResponse.amount) руб." -ForegroundColor Gray
    Write-Host "   - Название: $($paymentResponse.item_name)" -ForegroundColor Gray
    Write-Host "   - Session ID: $($paymentResponse.session_id)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Ссылка для оплаты:" -ForegroundColor Yellow
    Write-Host "   $($paymentResponse.payment_url)" -ForegroundColor Cyan

    # Сохраняем данные для следующих шагов
    $paymentId = $paymentResponse.payment_id
    $sessionId = $paymentResponse.session_id

} catch {
    Write-Host "   Ошибка создания платежа: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $errorContent = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   Детали: $($errorContent.detail)" -ForegroundColor Red
    }
    exit 1
}

# 3. ПРОВЕРКА СТАТУСА (до оплаты)
Write-Host ""
Write-Host "3. Проверка статуса платежа (до оплаты)..." -ForegroundColor Yellow
try {
    $statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/users/payments/$paymentId/status/" `
        -Method GET `
        -Headers @{"Authorization" = "Bearer $accessToken"}

    Write-Host "   Статус: $($statusResponse.status)" -ForegroundColor Green
    Write-Host "   - ID: $($statusResponse.id)" -ForegroundColor Gray
    Write-Host "   - Сумма: $($statusResponse.amount)" -ForegroundColor Gray
    Write-Host "   - Session: $($statusResponse.stripe_session_id)" -ForegroundColor Gray

} catch {
    Write-Host "   Не удалось проверить статус: $_" -ForegroundColor Yellow
}

# 4. ИНСТРУКЦИИ ДЛЯ ОПЛАТЫ
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "ИНСТРУКЦИИ ДЛЯ ТЕСТИРОВАНИЯ ОПЛАТЫ:" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host ""
Write-Host "1. Откройте ссылку для оплаты в браузере" -ForegroundColor White
Write-Host "2. Введите тестовые данные карты:" -ForegroundColor White
Write-Host "   - Номер карты: 4242 4242 4242 4242" -ForegroundColor Green
Write-Host "   - Срок: любая будущая дата" -ForegroundColor Green
Write-Host "   - CVC: любые 3 цифры" -ForegroundColor Green
Write-Host "   - Имя: любые данные" -ForegroundColor Green
Write-Host "3. Нажмите 'Оплатить'" -ForegroundColor White
Write-Host "4. После оплаты вы будете перенаправлены на страницу успеха" -ForegroundColor White

Write-Host ""
Write-Host "5. После успешной оплаты проверьте статус:" -ForegroundColor White
Write-Host "   curl -X GET http://localhost:8000/api/users/payments/$paymentId/status/ \" -ForegroundColor Gray
Write-Host "     -H \"Authorization: Bearer $($accessToken.Substring(0, 20))...\"" -ForegroundColor Gray

Write-Host ""
Write-Host "6. Проверьте вебхук (если настроен):" -ForegroundColor White
Write-Host "   В Stripe Dashboard настройте вебхук на:" -ForegroundColor Gray
Write-Host "   http://localhost:8000/api/users/payments/webhook/" -ForegroundColor Cyan

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "ТЕСТОВЫЕ ДАННЫЕ:" -ForegroundColor Yellow
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host ""
Write-Host "- Payment ID: $paymentId" -ForegroundColor White
Write-Host "- Session ID: $sessionId" -ForegroundColor White
Write-Host "- JWT Token: $($accessToken.Substring(0, 20))..." -ForegroundColor White
Write-Host "- Ссылка для оплаты сохранена в переменной" -ForegroundColor White

# Сохраняем ссылку в переменной
$global:PaymentUrl = $paymentResponse.payment_url
Write-Host ""
Write-Host "Ссылка для оплаты сохранена в `$PaymentUrl" -ForegroundColor Green
Write-Host "   Для открытия в браузере: Start-Process `$PaymentUrl" -ForegroundColor Gray

Write-Host ""
Write-Host "Тестовый сценарий готов!" -ForegroundColor Green