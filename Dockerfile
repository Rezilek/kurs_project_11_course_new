# Dockerfile
# Базовый образ с Python
FROM python:3.11-slim

# Защита от записи .pyc файлов и буферизации вывода в консоль
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем pip и устанавливаем зависимости
# Сначала копируем только файл с зависимостями, чтобы использовать кэширование слоев Docker
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем весь проект в рабочую директорию
COPY . /app/