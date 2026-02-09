-- Этот файл выполняется после создания базы данных PostgreSQL
-- Пользователь уже создан автоматически из переменных окружения

-- Даем дополнительные права если нужно
GRANT ALL PRIVILEGES ON DATABASE kurs_project_db TO kurs_user;
ALTER DATABASE kurs_project_db OWNER TO kurs_user;
