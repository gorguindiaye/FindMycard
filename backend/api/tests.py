import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import DocumentType, LostItem, FoundItem, Match, Notification, CustomUser
from .services import MatchingService


class AuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

    def test_user_registration(self):
        """Test user registration with valid data"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('id', response.data['user'])
        self.assertEqual(response.data['user']['email'], self.user_data['email'])

    def test_user_login_with_email(self):
        """Test login with email instead of username"""
        # First register
        self.client.post(self.register_url, self.user_data, format='json')

        # Then login
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DocumentTypeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('document-types-list')

    def test_get_document_types(self):
        """Test retrieving document types"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)


class LostItemTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Create document type
        self.doc_type = DocumentType.objects.create(
            name='Carte d\'identité',
            description='Carte nationale d\'identité'
        )

        self.url = reverse('lost-item-list')
        self.lost_item_data = {
            'document_type_id': self.doc_type.id,
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'date_of_birth': '1990-01-01',
            'document_number': '123456789',
            'lost_date': '2024-01-01',
            'lost_location': 'Paris',
            'description': 'Carte perdue dans le métro',
            'contact_phone': '0123456789',
            'contact_email': 'jean@example.com'
        }

    def test_create_lost_item(self):
        """Test creating a lost item"""
        response = self.client.post(self.url, self.lost_item_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], self.lost_item_data['first_name'])
        self.assertEqual(response.data['user']['id'], self.user.id)

    def test_get_lost_items(self):
        """Test retrieving user's lost items"""
        # Create a lost item first
        self.client.post(self.url, self.lost_item_data, format='json')

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_lost_item(self):
        """Test updating a lost item"""
        # Create
        create_response = self.client.post(self.url, self.lost_item_data, format='json')
        item_id = create_response.data['id']

        # Update
        update_data = self.lost_item_data.copy()
        update_data['description'] = 'Updated description'
        update_url = reverse('lost-item-detail', kwargs={'pk': item_id})
        response = self.client.patch(update_url, {'description': 'Updated description'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')


class FoundItemTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Create document type
        self.doc_type = DocumentType.objects.create(
            name='Carte d\'identité',
            description='Carte nationale d\'identité'
        )

        self.url = reverse('found-item-list')

    def test_create_found_item(self):
        """Test creating a found item"""
        found_item_data = {
            'document_type_id': self.doc_type.id,
            'found_date': '2024-01-01',
            'found_location': 'Paris',
            'description': 'Carte trouvée dans la rue',
            'contact_phone': '0123456789',
            'contact_email': 'finder@example.com'
        }
        response = self.client.post(self.url, found_item_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['found_location'], found_item_data['found_location'])


class MatchTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # Create document type
        self.doc_type = DocumentType.objects.create(
            name='Carte d\'identité',
            description='Carte nationale d\'identité'
        )

        # Create lost item
        self.lost_item = LostItem.objects.create(
            user=self.user,
            document_type=self.doc_type,
            first_name='Jean',
            last_name='Dupont',
            date_of_birth='1990-01-01',
            document_number='123456789',
            lost_date='2024-01-01',
            lost_location='Paris',
            description='Carte perdue',
            contact_phone='0123456789',
            contact_email='jean@example.com'
        )

        # Create found item
        self.found_item = FoundItem.objects.create(
            user=self.user,
            document_type=self.doc_type,
            found_date='2024-01-01',
            found_location='Paris',
            description='Carte trouvée',
            contact_phone='0123456789',
            contact_email='finder@example.com'
        )

        self.url = reverse('match-list')

    def test_get_matches(self):
        """Test retrieving matches"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('notification-list')

    def test_get_notifications(self):
        """Test retrieving notifications"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data['results'], list)


class DeclarationToMatchingFlowTests(APITestCase):
    """
    End-to-end style tests to ensure a lost declaration and a found declaration
    can be matched through the public API endpoints plus the matching pipeline.
    """

    def setUp(self):
        self.document_type = DocumentType.objects.create(
            name="Carte d'identité",
            description="Carte nationale d'identité"
        )
        self.lost_user = CustomUser.objects.create_user(
            username='lost_user',
            email='lost@example.com',
            password='pass12345',
            role='citoyen'
        )
        self.finder_user = CustomUser.objects.create_user(
            username='finder_user',
            email='finder@example.com',
            password='pass12345',
            role='citoyen'
        )
        self.admin_user = CustomUser.objects.create_user(
            username='admin_user',
            email='admin@example.com',
            password='pass12345',
            role='admin_public'
        )

    def test_lost_and_found_flow_creates_match_and_notification(self):
        lost_payload = {
            'document_type_id': self.document_type.id,
            'first_name': 'Aminata',
            'last_name': 'Diallo',
            'date_of_birth': '1991-06-15',
            'document_number': 'CI-XYZ-12345',
            'lost_date': '2024-10-01',
            'lost_location': 'Dakar',
            'description': 'Carte perdue à la gare',
            'contact_phone': '771112233',
            'contact_email': 'aminata@example.com'
        }
        self.client.force_authenticate(user=self.lost_user)
        lost_response = self.client.post(reverse('lost-item-list'), lost_payload, format='json')
        self.assertEqual(lost_response.status_code, status.HTTP_201_CREATED)
        lost_item = LostItem.objects.get(id=lost_response.data['id'])

        found_payload = {
            'document_type_id': self.document_type.id,
            'found_date': '2024-10-02',
            'found_location': 'Dakar',
            'description': 'Carte retrouvée sur le quai',
            'contact_phone': '780000000',
            'contact_email': 'finder@example.com'
        }
        self.client.force_authenticate(user=self.finder_user)
        found_response = self.client.post(reverse('found-item-list'), found_payload, format='json')
        self.assertEqual(found_response.status_code, status.HTTP_201_CREATED)
        found_item = FoundItem.objects.get(id=found_response.data['id'])

        # Simule la mise à jour effectuée par l'OCR puis exécute le matching
        found_item.first_name = lost_item.first_name
        found_item.last_name = lost_item.last_name
        found_item.date_of_birth = lost_item.date_of_birth
        found_item.document_number = lost_item.document_number
        found_item.save()
        MatchingService.find_matches(found_item)

        self.assertEqual(Match.objects.count(), 1)
        match = Match.objects.first()
        self.assertEqual(match.lost_item_id, lost_item.id)
        self.assertEqual(match.found_item_id, found_item.id)
        self.assertGreater(match.confidence_score, 0.9)

        notification_exists = Notification.objects.filter(
            user=self.lost_user,
            notification_type='match_found'
        ).exists()
        self.assertTrue(notification_exists)

        self.client.force_authenticate(user=self.admin_user)
        list_response = self.client.get(reverse('match-list'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 1)
        self.assertEqual(list_response.data['results'][0]['id'], match.id)

