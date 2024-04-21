import unittest
from app import app, auth
from firebase_admin import auth as firebase_auth


class AuthTestCase(unittest.TestCase):

    def setUp(self):
        # Setting up the test client
        self.client = app.test_client()
        self.client.testing = True

    def test_register_user(self):
        # Define the payload with the user's data
        payload = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpass',
            'confirm_password': 'testpass'
        }
        # Send a POST request to the register endpoint with the payload
        response = self.client.post('/register', data=payload)
        # Check the response status code
        self.assertEqual(response.status_code, 200)

        # Clean up (delete) the user created during the test
        try:
            user = firebase_auth.get_user_by_email(payload['email'])
            firebase_auth.delete_user(user.uid)
        except firebase_auth.NotFoundError:
            pass

    def test_login_user(self):
        # Assuming a user already exists in your system
        payload = {
            'email': 'test1@gmail.com',
            'password': '123test1'
        }
        response = self.client.post('/signin', data=payload)
        # Check the response status code
        self.assertEqual(response.status_code, 200)
        # Check if the response data contains expected content (e.g., a welcome message)
        self.assertIn('Welcome', response.get_data(as_text=True))

    def test_logout_user(self):
        # This test assumes user is logged in (would need a mock here)
        response = self.client.get('/logout', follow_redirects=True)
        # Check the response status code
        self.assertEqual(response.status_code, 200)
        # Check if the response data shows user is logged out (e.g., sign-in link is present)
        self.assertIn('Sign In', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
