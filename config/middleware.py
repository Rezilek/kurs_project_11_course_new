# config/middleware.py
import re
from django.utils.deprecation import MiddlewareMixin


class ForceUTF8Middleware(MiddlewareMixin):
    """
    Middleware для принудительной установки кодировки UTF-8
    в заголовках ответов Django
    """

    def process_response(self, request, response):
        # Проверяем, является ли ответ HTML
        content_type = response.get('Content-Type', '')

        if 'text/html' in content_type or 'text/plain' in content_type:
            # Если в Content-Type нет charset, добавляем его
            if 'charset=' not in content_type.lower():
                response['Content-Type'] = f"{content_type}; charset=utf-8"

            # Также проверяем содержимое HTML
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')

                # Добавляем meta charset если его нет
                if '<head>' in content and '<meta charset=' not in content.lower():
                    content = content.replace('<head>', '<head>\n    <meta charset="UTF-8">')
                    response.content = content.encode('utf-8')

        elif 'application/json' in content_type:
            # Для JSON ответов тоже добавляем charset
            if 'charset=' not in content_type.lower():
                response['Content-Type'] = f"{content_type}; charset=utf-8"

        return response