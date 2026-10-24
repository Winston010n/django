from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets

from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import Books, Library
from .serializers import BooksSerializers, LibrarySerializer

BOOK_TAGS = ['Книга']

class BookListApi(APIView):

    @extend_schema(
            tags=BOOK_TAGS,
            summary='СПИСОК ВСЕХ КНИГ',
            responses={200: BooksSerializers(many=True)}
    )
    def get(self, request):
        books = Books.objects.all()
        serializer = BooksSerializers(books, many=True)
        return Response(serializer.data)

    @extend_schema(
            tags=BOOK_TAGS,
            summary='Добавить книгу в список',
            request=BooksSerializers,
            responses={201: BooksSerializers}
        )
    def post(self, request):
        serializer = BooksSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LibraryViewSet(viewsets.ModelViewSet):
    queryset = Library.objects.prefetch_related('books').all()
    serializer_class = LibrarySerializer
