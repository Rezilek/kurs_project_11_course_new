from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_youtube_url(value):
    """
    Валидатор для проверки, что ссылка ведет на YouTube.
    Разрешаются только ссылки на youtube.com
    """
    if not value:
        return

    # Паттерны для проверки YouTube ссылок
    youtube_patterns = [
        r'^(https?://)?(www\.)?youtube\.com/',
        r'^(https?://)?(www\.)?youtu\.be/',
    ]

    # Проверяем каждый паттерн
    is_valid = any(re.match(pattern, value) for pattern in youtube_patterns)

    if not is_valid:
        raise ValidationError(
            _('Ссылка должна вести на YouTube. Пример: https://www.youtube.com/watch?v=... или https://youtu.be/...'),
            code='invalid_youtube_url'
        )


def validate_no_external_links(value):
    """
    Валидатор для проверки отсутствия внешних ссылок в тексте.
    Исключение составляют только ссылки на YouTube.
    """
    if not value:
        return

    # Паттерн для поиска URL в тексте
    url_pattern = r'(https?://[^\s]+)'

    # Находим все ссылки в тексте
    urls = re.findall(url_pattern, value)

    for url in urls:
        # Проверяем, что это YouTube ссылка
        youtube_patterns = [
            r'^(https?://)?(www\.)?youtube\.com/',
            r'^(https?://)?(www\.)?youtu\.be/',
        ]

        is_youtube = any(re.match(pattern, url) for pattern in youtube_patterns)

        if not is_youtube:
            raise ValidationError(
                _('Запрещены ссылки на сторонние ресурсы, кроме YouTube. '
                  'Найдена ссылка: %(url)s'),
                code='external_link_found',
                params={'url': url}
            )