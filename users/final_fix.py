# users/final_fix.py
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
def payment_success_final(request):
    """Исправленная версия успешного платежа"""
    session_id = request.GET.get('session_id', '')

    # Если нет session_id, показываем тестовую страницу
    if not session_id:
        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Тест кодировки</title>
    <style>
        body { font-family: Arial; padding: 50px; text-align: center; }
        h1 { color: #4CAF50; }
    </style>
</head>
<body>
    <h1>✅ Тест кодировки UTF-8</h1>
    <p>Русский текст: Привет мир! Тестирование кодировки</p>
    <p>Спецсимволы: ✅ ❌ 🔥 💯 ⭐ 🎉</p>
    <p>Добавьте ?session_id=... для проверки реального платежа</p>
</body>
</html>'''
        return HttpResponse(html, content_type='text/html; charset=utf-8')

    # Ищем платеж в базе данных
    from .models import Payment

    try:
        payment = Payment.objects.get(stripe_session_id=session_id)

        # Получаем название товара
        if payment.paid_course:
            item_name = payment.paid_course.title
        elif payment.paid_lesson:
            item_name = payment.paid_lesson.title
        else:
            item_name = "Неизвестный товар"

        status_color = "#4CAF50" if payment.status == 'paid' else "#FFA500"
        status_icon = "✅" if payment.status == 'paid' else "⏳"

        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Платеж #{payment.id}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            padding: 50px; 
            text-align: center;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(50,50,93,0.1), 0 5px 15px rgba(0,0,0,0.07);
            padding: 40px;
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{ 
            color: {status_color}; 
            margin-bottom: 30px;
            font-size: 2.5rem;
        }}
        .icon {{
            font-size: 70px;
            margin-bottom: 20px;
        }}
        .details {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
            text-align: left;
            border-left: 5px solid {status_color};
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eaeaea;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .label {{ font-weight: bold; color: #555; }}
        .value {{ font-weight: 500; color: #333; }}
        a {{
            display: inline-block;
            margin: 10px;
            padding: 12px 25px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }}
        a:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">{status_icon}</div>
        <h1>Оплата успешно завершена!</h1>

        <div class="details">
            <div class="detail-row">
                <span class="label">ID платежа:</span>
                <span class="value">{payment.id}</span>
            </div>
            <div class="detail-row">
                <span class="label">Товар:</span>
                <span class="value">{item_name}</span>
            </div>
            <div class="detail-row">
                <span class="label">Сумма:</span>
                <span class="value" style="font-size: 1.4rem; color: {status_color}; font-weight: bold;">
                    {payment.amount} {payment.currency.upper()}
                </span>
            </div>
            <div class="detail-row">
                <span class="label">Статус:</span>
                <span class="value" style="color: {status_color}; font-weight: bold;">
                    {payment.status.upper()}
                </span>
            </div>
            <div class="detail-row">
                <span class="label">Дата:</span>
                <span class="value">{payment.created_at.strftime('%d.%m.%Y %H:%M')}</span>
            </div>
        </div>

        <div>
            <a href="/api/courses/">📚 Перейти к курсам</a>
            <a href="/api/docs/" style="background: #6c757d;">📖 Документация API</a>
        </div>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 0.9rem;">
            <p>Session ID: <code>{session_id[:30]}...</code></p>
            <p>Если возникли проблемы, напишите на support@example.com</p>
        </div>
    </div>
</body>
</html>'''

        return HttpResponse(html, content_type='text/html; charset=utf-8')

    except Payment.DoesNotExist:
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Платеж не найден</title>
    <style>
        body {{ font-family: Arial; padding: 50px; text-align: center; }}
        h1 {{ color: #dc3545; }}
    </style>
</head>
<body>
    <h1>❌ Платеж не найден</h1>
    <p>Платеж с указанным session_id не найден.</p>
    <p><strong>Session ID:</strong> {session_id}</p>
    <p><a href="/api/docs/">Вернуться к документации</a></p>
</body>
</html>'''

        return HttpResponse(html, content_type='text/html; charset=utf-8', status=404)

    except Exception as e:
        logger.error(f"Ошибка в payment_success_final: {e}")

        html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Ошибка сервера</title>
</head>
<body>
    <h1>🔥 Ошибка сервера</h1>
    <p>Произошла внутренняя ошибка. Попробуйте позже.</p>
    <p><a href="/api/docs/">Вернуться к документации</a></p>
</body>
</html>'''

        return HttpResponse(html, content_type='text/html; charset=utf-8', status=500)


@csrf_exempt
def payment_cancel_final(request):
    """Исправленная версия отмены платежа"""
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Оплата отменена</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            padding: 50px; 
            text-align: center;
            background: linear-gradient(135deg, #fdf6f6 0%, #f8d7da 100%);
            min-height: 100vh;
            margin: 0;
        }}
        .container {{
            background: white;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(50,50,93,0.1), 0 5px 15px rgba(0,0,0,0.07);
            padding: 40px;
            max-width: 600px;
            margin: 0 auto;
        }}
        h1 {{ color: #dc3545; }}
        .icon {{ font-size: 70px; margin-bottom: 20px; }}
        a {{
            display: inline-block;
            margin: 10px;
            padding: 12px 25px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">❌</div>
        <h1>Оплата отменена</h1>
        <p>Вы отменили процесс оплаты.</p>
        <p>Вы можете вернуться и повторить попытку в любое время.</p>
        <div>
            <a href="/api/courses/">📚 Вернуться к курсам</a>
            <a href="/api/docs/" style="background: #6c757d;">📖 Документация API</a>
        </div>
    </div>
</body>
</html>'''

    return HttpResponse(html, content_type='text/html; charset=utf-8')