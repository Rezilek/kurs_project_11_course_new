# courses/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonViewSet, SubscriptionViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='courses')  # будет /api/courses/courses/
router.register(r'lessons', LessonViewSet, basename='lessons')  # будет /api/courses/lessons/
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')


urlpatterns = [
    path('', include(router.urls)),
    #path('courses/subscribe/', SubscriptionViewSet.as_view({'post': 'create'}), name='course-subscribe'),
]
