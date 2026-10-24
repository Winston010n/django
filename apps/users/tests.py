from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.profile_url = reverse('profile')

        self.user_password = 'StrongPassword123'
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password=self.user_password
        )

    def test_register_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePassword456',
            'password2': 'SecurePassword456'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], 'newuser')
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertIn('jwt', response.data['tokens'])
        self.assertTrue(Token.objects.filter(user__username='newuser').exists())

    def test_django_token_login_and_logout(self):
        response = self.client.post(
            reverse('token'),
            {'username': 'existinguser', 'password': self.user_password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['token']

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        logout_response = self.client.post(reverse('token-out'))
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(key=token).exists())

    def test_jwt_login_refresh_and_logout(self):
        login_response = self.client.post(
            reverse('jwt-login'),
            {'username': 'existinguser', 'password': self.user_password},
            format='json',
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access = login_response.data['access']
        refresh = login_response.data['refresh']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

        refresh_response = self.client.post(
            reverse('jwt-refresh'),
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

        logout_response = self.client.post(
            reverse('jwt-logout'),
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        revoked_refresh_response = self.client.post(
            reverse('jwt-refresh'),
            {'refresh': refresh},
            format='json',
        )
        self.assertEqual(revoked_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_register_password_mismatch(self):
        data = {
            'username': 'newuser2',
            'password': 'Password123',
            'password2': 'DifferentPassword456'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data)

    def test_register_short_password(self):
        data = {
            'username': 'newuser3',
            'password': '123',
            'password2': '123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_success(self):
        data = {
            'username': 'existinguser',
            'password': self.user_password
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'existinguser')

    def test_login_invalid_credentials(self):
        data = {
            'username': 'existinguser',
            'password': 'WrongPassword!'
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_unauthorized(self):
        response = self.client.get(self.profile_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_profile_authorized_and_patch(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'existinguser')

        patch_data = {'email': 'updated@example.com'}
        patch_res = self.client.patch(self.profile_url, patch_data, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updated@example.com')

    def test_logout(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
