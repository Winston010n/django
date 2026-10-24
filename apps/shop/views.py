from rest_framework import permissions, viewsets

from .models import Category, Product, Shop
from .serializer import CategorySerializer, ProductSerializer, ShopSer
from .pagination import ShopPagination
from .permissions import IsOwnerOrReadOnly

from django_filters.rest_framework import DjangoFilterBackend 
from rest_framework.filters import SearchFilter, OrderingFilter

from drf_spectacular.utils import extend_schema, extend_schema_view

SHOP = ['Магазины']


@extend_schema_view(
    list=extend_schema(tags=SHOP, summary='Список магазинов', description='Публичный список с фильтрацией, поиском и сортировкой.'),
    retrieve=extend_schema(tags=SHOP, summary='Получить магазин', description='Публичный просмотр магазина.'),
    create=extend_schema(tags=SHOP, summary='Создать магазин', description='Требуется аутентификация. Создатель автоматически становится владельцем.'),
    update=extend_schema(tags=SHOP, summary='Обновить магазин', description='Полностью обновляет магазин. Доступно владельцу или администратору.'),
    partial_update=extend_schema(tags=SHOP, summary='Частично обновить магазин', description='Обновляет переданные поля. Доступно владельцу или администратору.'),
    destroy=extend_schema(tags=SHOP, summary='Удалить магазин', description='Доступно владельцу или администратору.'),
)
class ShopViewSets(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSer
    pagination_class = ShopPagination
    permission_classes = [IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'color']
    search_fields = ['name', 'color']
    ordering_fields = ['name', 'id']
    ordering = ['id']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(tags=SHOP, summary='Список категорий', description='Публичный список категорий каталога.'),
    retrieve=extend_schema(tags=SHOP, summary='Получить категорию', description='Публичный просмотр категории.'),
    create=extend_schema(tags=SHOP, summary='Создать категорию', description='Требуется аутентификация.'),
    update=extend_schema(tags=SHOP, summary='Обновить категорию', description='Полностью обновляет категорию. Требуется аутентификация.'),
    partial_update=extend_schema(tags=SHOP, summary='Частично обновить категорию', description='Обновляет переданные поля. Требуется аутентификация.'),
    destroy=extend_schema(tags=SHOP, summary='Удалить категорию', description='Требуется аутентификация. Удаляет связанные товары.'),
)
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@extend_schema_view(
    list=extend_schema(tags=SHOP, summary='Список товаров', description='Фильтры: price, price__gte, price__lte, category, shop. Поиск: search. Сортировка: ordering.'),
    retrieve=extend_schema(tags=SHOP, summary='Получить товар', description='Публичный просмотр товара.'),
    create=extend_schema(tags=SHOP, summary='Создать товар', description='Требуется аутентификация.'),
    update=extend_schema(tags=SHOP, summary='Обновить товар', description='Полностью обновляет товар. Требуется аутентификация.'),
    partial_update=extend_schema(tags=SHOP, summary='Частично обновить товар', description='Обновляет переданные поля. Требуется аутентификация.'),
    destroy=extend_schema(tags=SHOP, summary='Удалить товар', description='Требуется аутентификация.'),
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('shop', 'category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'price': ['exact', 'gte', 'lte'],
        'category': ['exact'],
        'shop': ['exact'],
    }
    search_fields = ['title']
    ordering_fields = ['price', 'title', 'id']
    ordering = ['id']
