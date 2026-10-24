from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User

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

        user = User.objects.create_user(username="librarian", password="StrongPassword123")
        authenticated_client = APIClient()
        authenticated_client.force_authenticate(user=user)
        delete_response = authenticated_client.delete(f"/books/libraries/{library.id}/")

        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Books.objects.filter(pk=book.pk).exists())
