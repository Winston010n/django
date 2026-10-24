from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status, viewsets

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Books, Library
from .serializers import BooksSerializers, LibrarySerializer

BOOK_TAGS = ['Книги и библиотеки']

class BookListApi(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
            tags=BOOK_TAGS,
            summary='Список книг',
            description='Публичный запрос. Книгу можно привязать к библиотеке по её ID.',
            responses={200: BooksSerializers(many=True)},
    )
    def get(self, request):
        books = Books.objects.all()
        serializer = BooksSerializers(books, many=True)
        return Response(serializer.data)

    @extend_schema(
            tags=BOOK_TAGS,
            summary='Создать книгу',
            description='Требуется аутентификация. Поле library необязательно.',
            request=BooksSerializers,
            responses={201: BooksSerializers},
        )
    def post(self, request):
        serializer = BooksSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(tags=BOOK_TAGS, summary='Список библиотек', description='Возвращает библиотеки вместе с вложенными книгами.'),
    retrieve=extend_schema(tags=BOOK_TAGS, summary='Получить библиотеку', description='Возвращает библиотеку и все связанные книги.'),
    create=extend_schema(tags=BOOK_TAGS, summary='Создать библиотеку', description='Требуется аутентификация.'),
    update=extend_schema(tags=BOOK_TAGS, summary='Обновить библиотеку', description='Полностью обновляет библиотеку. Требуется аутентификация.'),
    partial_update=extend_schema(tags=BOOK_TAGS, summary='Частично обновить библиотеку', description='Обновляет переданные поля. Требуется аутентификация.'),
    destroy=extend_schema(tags=BOOK_TAGS, summary='Удалить библиотеку', description='Удаляет библиотеку и связанные книги. Требуется аутентификация.'),
)
class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.prefetch_related('books').all()
    serializer_class = LibrarySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
