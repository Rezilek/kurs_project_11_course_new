from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from courses.models import Course, Lesson, Subscription
from django.core.exceptions import ValidationError
from courses.validators import validate_youtube_url, validate_no_external_links


User = get_user_model()


class SubscriptionTests(APITestCase):
    def setUp(self):
        # Создаем группу модераторов
        self.moderator_group, _ = Group.objects.get_or_create(name='moderators')

        # Создаем пользователя и делаем его модератором
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.user.groups.add(self.moderator_group)

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )

        # Создаем курс от имени пользователя (теперь он модератор, видит все)
        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание тестового курса',
            owner=self.user  # Пользователь владелец и модератор
        )

        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

    def test_create_subscription_via_subscribe_action(self):
        """Тест: создание подписки через action subscribe"""
        # Используем курс из setUp
        url = f'/api/courses/courses/{self.course.id}/subscribe/'
        print(f"Используем курс ID: {self.course.id}")

        response = self.client.post(url)
        print(f"URL: {url}")
        print(f"Статус: {response.status_code}")
        print(f"Данные: {response.data}")

        # Должен быть 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем данные
        self.assertEqual(response.data.get('status'), 'success')
        self.assertTrue(response.data.get('is_subscribed', False))

        # Проверяем в базе
        self.assertTrue(Subscription.objects.filter(
            user=self.user,
            course=self.course,
            is_active=True
        ).exists())

    def test_create_subscription_via_subscriptions_endpoint(self):
        """Тест: создание подписки через endpoint /subscriptions/"""
        url = '/api/courses/subscriptions/'

        # Вариант 1: Просто ID курса
        data = {'course': self.course.id}

        print(f"URL: {url}")
        print(f"Данные POST: {data}")
        print(f"Тип course.id: {type(self.course.id)}")

        response = self.client.post(url, data, format='json')
        print(f"Статус: {response.status_code}")
        print(f"Данные ответа: {response.data}")

        # Отладка: если ошибка валидации
        if response.status_code == 400:
            print(f"Ошибка валидации: {response.data}")

        # Должен быть 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем в базе
        self.assertTrue(Subscription.objects.filter(
            user=self.user,
            course=self.course
        ).exists())


class LessonCRUDTests(APITestCase):
    def setUp(self):
        # Создаем пользователей
        self.owner = User.objects.create_user(
            email='owner@example.com',
            password='testpass123'
        )

        # Создаем группу модераторов
        self.moderator_group, _ = Group.objects.get_or_create(name='moderators')
        self.moderator = User.objects.create_user(
            email='moderator@example.com',
            password='testpass123'
        )
        self.moderator.groups.add(self.moderator_group)

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )

        # Создаем курс
        self.course = Course.objects.create(
            title='Тестовый курс',
            description='Описание курса',
            owner=self.owner
        )

        # Создаем урок с правильным полем video_url
        self.lesson = Lesson.objects.create(
            title='Тестовый урок',
            description='Описание урока',
            video_url='https://youtube.com/test',
            course=self.course,
            owner=self.owner
        )

    def test_lesson_update_by_moderator(self):
        """Тест: обновление урока модератором"""
        self.client.force_authenticate(user=self.moderator)

        url = f'/api/courses/lessons/{self.lesson.id}/'
        updated_data = {
            'title': 'Обновленный урок',
            'description': 'Обновленное описание',
            'video_url': 'https://youtube.com/new_video'
        }

        response = self.client.patch(url, updated_data)

        # Модератор должен иметь доступ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, 'Обновленный урок')
        self.assertEqual(self.lesson.video_url, 'https://youtube.com/new_video')

    def test_lesson_delete_by_other_user_denied(self):
        """Тест: запрет удаления урока другим пользователем"""
        self.client.force_authenticate(user=self.other_user)

        url = f'/api/courses/lessons/{self.lesson.id}/'
        response = self.client.delete(url)

        # Обычный пользователь не видит чужой урок - 404
        # Или если видит (через модераторские права), но не может удалить - 403
        # В вашем случае get_queryset скрывает чужие уроки, поэтому 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Урок должен остаться
        self.assertTrue(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_lesson_delete_by_owner_allowed(self):
        """Тест: удаление урока владельцем разрешено"""
        self.client.force_authenticate(user=self.owner)

        url = f'/api/courses/lessons/{self.lesson.id}/'
        response = self.client.delete(url)

        # Владелец может удалить свой урок
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_lesson_create_with_invalid_url(self):
        """Тест: создание урока с невалидной (не YouTube) ссылкой"""
        self.client.force_authenticate(user=self.owner)

        url = '/api/courses/lessons/'
        data = {
            'title': 'Урок с невалидной ссылкой',
            'description': 'Описание урока',
            'video_url': 'https://vimeo.com/123456',  # Не YouTube!
            'course': self.course.id
        }

        response = self.client.post(url, data)

        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_url', response.data)

    def test_lesson_create_with_valid_url(self):
        """Тест: создание урока с валидной YouTube ссылкой"""
        self.client.force_authenticate(user=self.owner)

        url = '/api/courses/lessons/'
        data = {
            'title': 'Урок с валидной ссылкой',
            'description': 'Описание урока',
            'video_url': 'https://youtube.com/watch?v=abc123',  # YouTube!
            'course': self.course.id
        }

        response = self.client.post(url, data)

        # Должен быть успех
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 2)  # Один уже был в setUp


class ValidatorTests(TestCase):
    """Тесты для валидаторов"""

    def test_youtube_url_validator_valid_urls(self):
        """Тест: валидные YouTube ссылки"""
        valid_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'http://youtube.com/watch?v=test123',
            'https://youtu.be/dQw4w9WgXcQ',
            'http://youtu.be/test123',
            'www.youtube.com/watch?v=test',
            'youtube.com/watch?v=test',
        ]

        for url in valid_urls:
            try:
                validate_youtube_url(url)
            except ValidationError:
                self.fail(f"Валидная YouTube ссылка не прошла проверку: {url}")

    def test_youtube_url_validator_invalid_urls(self):
        """Тест: невалидные (не YouTube) ссылки"""
        invalid_urls = [
            'https://vimeo.com/123456',
            'http://rutube.ru/video/123',
            'https://example.com/video',
            'ftp://youtube.com/fake',  # Не HTTPS/HTTP
            'mailto:test@example.com',
        ]

        for url in invalid_urls:
            with self.assertRaises(ValidationError):
                validate_youtube_url(url)

    def test_no_external_links_validator_valid_text(self):
        """Тест: текст без внешних ссылок"""
        valid_texts = [
            'Простой текст без ссылок',
            'Текст с YouTube ссылкой: https://youtube.com/watch?v=123',
            'Множество YouTube ссылок: https://youtu.be/abc и http://youtube.com/watch?v=def',
            '',
            None,
        ]

        for text in valid_texts:
            try:
                validate_no_external_links(text)
            except ValidationError:
                self.fail(f"Валидный текст не прошел проверку: {text}")

    def test_no_external_links_validator_invalid_text(self):
        """Тест: текст с внешними ссылками"""
        invalid_cases = [
            {
                'text': 'Ссылка на Vimeo: https://vimeo.com/123',
                'expected_error': 'vimeo.com'
            },
            {
                'text': 'Множество ссылок: https://youtube.com/123 и https://example.com/456',
                'expected_error': 'example.com'
            },
            {
                'text': 'Ссылка на Rutube: http://rutube.ru/video/789',
                'expected_error': 'rutube.ru'
            },
        ]

        for case in invalid_cases:
            with self.assertRaises(ValidationError) as context:
                validate_no_external_links(case['text'])

            # Проверяем, что ошибка содержит информацию о запрещенной ссылке
            self.assertIn(case['expected_error'], str(context.exception))

    def test_lesson_model_validation(self):
        """Тест: валидация модели Lesson"""
        from courses.models import Lesson, Course
        from django.contrib.auth import get_user_model
        from django.core.exceptions import ValidationError

        User = get_user_model()

        # Создаем тестовые данные
        user = User.objects.create_user(email='test_validation@example.com', password='testpass')
        course = Course.objects.create(title='Тестовый курс', description='Описание', owner=user)

        print("\n=== Тест 1: Невалидная видео ссылка ===")

        # Тест 1: Невалидная ссылка
        lesson1 = Lesson(
            title='Урок с невалидной ссылкой',
            description='Простое описание без ссылок',
            video_url='https://vimeo.com/123456',  # Не YouTube!
            course=course,
            owner=user
        )

        # Проверяем, что full_clean() вызывает ошибку
        with self.assertRaises(ValidationError) as context:
            lesson1.full_clean()

        print(f"Успех: full_clean() вызвал ValidationError")
        self.assertIn('video_url', context.exception.message_dict)

        print("\n=== Тест 2: Валидная YouTube ссылка ===")

        # Тест 2: Валидная ссылка
        lesson2 = Lesson(
            title='Урок с валидной ссылкой',
            description='Простое описание без ссылок',
            video_url='https://youtube.com/watch?v=abc123',  # YouTube!
            course=course,
            owner=user
        )

        # Должно пройти без ошибок
        try:
            lesson2.full_clean()
            lesson2.save()
            print("Успех: Урок с валидной ссылкой сохранен")
        except ValidationError as e:
            self.fail(f"Ошибка: Урок с валидной YouTube ссылкой вызвал ошибку: {e}")

        print("\n=== Тест 3: Внешние ссылки в описании ===")

        # Тест 3: Внешние ссылки в описании
        lesson3 = Lesson(
            title='Урок с внешними ссылками',
            description='Смотрите на Vimeo: https://vimeo.com/123',
            video_url='https://youtube.com/watch?v=abc123',  # YouTube - OK
            course=course,
            owner=user
        )

        # Должна быть ошибка из-за внешних ссылок в описании
        with self.assertRaises(ValidationError) as context:
            lesson3.full_clean()

        print(f"Успех: Обнаружены внешние ссылки в описании")

        print("\n=== Тест 4: YouTube ссылки в описании разрешены ===")

        # Тест 4: YouTube ссылки в описании (разрешены)
        lesson4 = Lesson(
            title='Урок с YouTube ссылками',
            description='Смотрите также: https://youtube.com/watch?v=def456',
            video_url='https://youtube.com/watch?v=abc123',
            course=course,
            owner=user
        )

        try:
            lesson4.full_clean()
            lesson4.save()
            print("Успех: YouTube ссылки в описании разрешены")
        except ValidationError as e:
            self.fail(f"Ошибка: YouTube ссылки в описании вызвали ошибку: {e}")

        # Проверяем итоговое количество
        self.assertEqual(Lesson.objects.count(), 2)  # lesson2 и lesson4

    def test_course_model_validation(self):
        """Тест: валидация модели Course"""
        from courses.models import Course
        from django.contrib.auth import get_user_model
        from django.core.exceptions import ValidationError

        User = get_user_model()

        # Создаем пользователя
        user = User.objects.create_user(email='test_course@example.com', password='testpass')

        print("\n=== Тест 1: Курс с внешними ссылками в описании ===")

        # Тест 1: Внешние ссылки в описании курса
        course1 = Course(
            title='Курс с внешними ссылками',
            description='Посетите наш сайт: https://example.com и Vimeo: https://vimeo.com/123',
            owner=user
        )

        # Должна быть ошибка из-за внешних ссылок
        with self.assertRaises(ValidationError) as context:
            course1.full_clean()

        print(f"Успех: Обнаружены внешние ссылки в описании курса")

        print("\n=== Тест 2: Курс с YouTube ссылками в описании ===")

        # Тест 2: YouTube ссылки в описании курса (разрешены)
        course2 = Course(
            title='Курс с YouTube ссылками',
            description='Дополнительные материалы: https://youtube.com/watch?v=abc123',
            owner=user
        )

        try:
            course2.full_clean()
            course2.save()
            print("Успех: YouTube ссылки в описании курса разрешены")
        except ValidationError as e:
            self.fail(f"Ошибка: YouTube ссылки в описании курса вызвали ошибку: {e}")

        # Проверяем сохранение
        self.assertEqual(Course.objects.filter(owner=user).count(), 1)


class ValidatorAPITests(APITestCase):
    """API тесты для валидаторов"""

    def test_lesson_create_with_invalid_url_api(self):
        """Тест: создание урока через API с невалидной ссылкой"""
        from django.contrib.auth import get_user_model
        from courses.models import Course

        User = get_user_model()

        # Создаем пользователя и курс
        user = User.objects.create_user(email='apitest@example.com', password='testpass')
        course = Course.objects.create(title='API тест курс', description='Описание', owner=user)

        self.client.force_authenticate(user=user)

        url = '/api/courses/lessons/'
        data = {
            'title': 'Урок с невалидной ссылкой через API',
            'description': 'Описание урока',
            'video_url': 'https://vimeo.com/123456',  # Не YouTube!
            'course': course.id
        }

        response = self.client.post(url, data, format='json')

        # Должна быть ошибка валидации (400 Bad Request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_url', response.data)

    def test_lesson_create_with_valid_url_api(self):
        """Тест: создание урока через API с валидной YouTube ссылкой"""
        from django.contrib.auth import get_user_model
        from courses.models import Course

        User = get_user_model()

        # Создаем пользователя и курс
        user = User.objects.create_user(email='apitest2@example.com', password='testpass')
        course = Course.objects.create(title='API тест курс 2', description='Описание', owner=user)

        self.client.force_authenticate(user=user)

        url = '/api/courses/lessons/'
        data = {
            'title': 'Урок с валидной ссылкой через API',
            'description': 'Описание урока',
            'video_url': 'https://youtube.com/watch?v=abc123',  # YouTube!
            'course': course.id
        }

        response = self.client.post(url, data, format='json')

        # Должен быть успех (201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['video_url'], 'https://youtube.com/watch?v=abc123')