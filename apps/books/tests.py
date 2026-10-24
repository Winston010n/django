from rest_framework import status
from rest_framework.test import APITestCase

from .models import Books, Library


class LibraryApiTests(APITestCase):
    def test_library_response_contains_books_and_deletion_cascades(self):
        library = Library.objects.create(
            name="Central Library",
            address="1 Main Street",
            city="Springfield",
        )
        book = Books.objects.create(
            title="Example Book",
            author="A. Author",
            price="12.50",
            library=library,
        )

        response = self.client.get("/books/libraries/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["books"][0]["id"], book.id)
        self.assertEqual(response.data[0]["books"][0]["library"], library.id)

        delete_response = self.client.delete(f"/books/libraries/{library.id}/")

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Books.objects.filter(pk=book.pk).exists())
