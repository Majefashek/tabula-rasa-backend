from django.test import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UserEndpointTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_user_details(self):
        url = reverse('get_user_details')  # Update with the correct URL name
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['username'], 'testuser')

    def test_update_user_details(self):
        url = reverse('update_user_details')  # Update with the correct URL name
        data = {'username': 'newusername'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['message'], 'User details updated successfully')
        self.assertEqual(response.data['data']['username'], 'newusername')

    def test_user_login(self):
        url = reverse('login')  # Update with the correct URL name
        data = {'username': 'testuser', 'password': 'password123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_signup(self):
        url = reverse('register')  # Update with the correct URL name
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'newpassword123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['user_data']['username'], 'newuser')

    def test_verify_email_success(self):
        # Generate a valid token for the user
        token = str(RefreshToken.for_user(self.user).access_token)
        url = reverse('verify_email')  # Update with the correct URL name
        response = self.client.get(url, {'token': token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['email'], 'Successfully activated')

    def test_verify_email_invalid_token(self):
        url = reverse('verify_email')  # Update with the correct URL name
        response = self.client.get(url, {'token': 'invalid_token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'Invalid token')

    def test_password_request_change(self):
        url = reverse('password_request_change')  # Update with the correct URL name
        data = {'email': 'testuser@example.com'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['message'], 'Password reset link sent to your email')

    def test_password_reset_success(self):
        token = str(RefreshToken.for_user(self.user).access_token)
        url = reverse('password_reset')  # Update with the correct URL name
        data = {'password': 'newpassword123'}
        response = self.client.post(url + f'?token={token}', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['message'], 'Password reset successful')

    def test_password_reset_invalid_token(self):
        url = reverse('password_reset')  # Update with the correct URL name
        data = {'password': 'newpassword123'}
        response = self.client.post(url + '?token=invalid_token', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['error'], 'Invalid token')
