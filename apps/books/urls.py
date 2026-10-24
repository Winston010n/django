from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookListApi, LibraryViewSet

router = DefaultRouter()
router.register('libraries', LibraryViewSet, basename='library')

urlpatterns = [
    path('books/', BookListApi.as_view()),
    path('', include(router.urls)),
]
