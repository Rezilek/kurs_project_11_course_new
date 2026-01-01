# Демонстрация работы образовательной платформы

## Тестирование API

### 1. Тест кодировки UTF-8

GET http://localhost:8000/api/users/test-encoding/

Ответ:

json
{
  "message": "Тест русских символов",
  "data": {
    "city": "Москва",
    "name": "Иван Петров",
    "description": "Тестирование кодировки UTF-8 в Django DRF"
  },
  "status": "success",
  "test": "Привет мир! Санкт-Петербург, Казань, Екатеринбург"
}

### 2. JWT авторизация

POST http://localhost:8000/api/users/token/
{
  "email": "test@example.com",
  "password": "testpass123"
}

Ответ:

json
{
  "refresh": "eyJ0eXAiOiJKV1Qi...",
  "access": "eyJ0eXAiOiJKV1Qi..."
}

### 3. Профиль пользователя

GET http://localhost:8000/api/users/users/me/
Authorization: Bearer <ваш_token>

### 4. Фильтрация платежей

GET http://localhost:8000/api/users/payments/?ordering=-payment_date
GET http://localhost:8000/api/users/payments/?payment_method=cash

### 5. API курсов

GET http://localhost:8000/api/courses/courses/
Authorization: Bearer <ваш_token>

#### Структура проекта

config/           # Настройки Django
├── settings.py   # Основные настройки с UTF-8
├── urls.py       # Маршруты
└── middleware.py # Middleware для кодировки

users/            # Приложение пользователей
├── models.py     # Кастомная модель User
├── views.py      # ViewSets и API endpoints
├── serializers.py # Сериализаторы с динамическим выводом
├── permissions.py # Права доступа (IsOwner, IsModerator)
└── urls.py       # Маршруты пользователей

courses/          # Приложение курсов
├── models.py     # Модели Course и Lesson
├── views.py      # ViewSets для курсов и уроков
└── serializers.py # Сериализаторы курсов

### Проверка работоспособности

Запустите: python test_final.py
