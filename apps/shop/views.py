from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .models import Category, Product, Shop
from .serializer import CategorySerializer, ProductSerializer, ShopSer
from .pagination import ShopPagination
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

from django_filters.rest_framework import DjangoFilterBackend 
from rest_framework.filters import SearchFilter, OrderingFilter

from drf_spectacular.utils import extend_schema, OpenApiResponse, extend_schema_view

SHOP = ['МАРКЕТ']


@extend_schema_view(
    list=extend_schema(tags=SHOP, summary='ПОЛУЧЕНИЕ СПИСКА МАРКЕТОВ'),
    retrieve=extend_schema(tags=SHOP, summary='ДЕТАЛЬНЫЙЙ ПРОСМОТР МАРКЕТЫ'),
    create=extend_schema(tags=SHOP, summary='СОЗДАНИЕ МАРКЕТАА'),
    update=extend_schema(tags=SHOP, summary='ПОЛНОЕ ОБНОВЛЕНИЕ МАРКЕТА'),
    partial_update=extend_schema(tags=SHOP, summary='ЧАСТИЧНОЕ ОБНОВЛЕНИЕ МАРКЕТА'),
    destroy=extend_schema(tags=SHOP, summary='УДАЛЕНИЕ МАРКЕТА'),
)

class ShopViewSets(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSer
    pagination_class = ShopPagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['name', 'color']
    search_fields = ['name', 'color']
    ordering_fields = ['name', 'id']
    ordering = ['id']

    # def get_permissions(self):
    #     if self.action in ['list', 'retrieve']:
    #         self.permission_classes = [permissions.AllowAny]
    #     elif self.action == 'create':
    #         self.permission_classes = [permissions.IsAuthenticated]
    #     if self.action in ['update', 'partial_update', 'destroy']:
    #         self.permission_classes = [IsAdminOrReadOnly]
    #     else:
    #         self.permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    #     return[permission() for permission in self.permission_classes]


    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('shop', 'category').all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'price': ['exact', 'gte', 'lte'],
        'category': ['exact'],
        'shop': ['exact'],
    }
    search_fields = ['title']
    ordering_fields = ['price', 'title', 'id']
    ordering = ['id']
