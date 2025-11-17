from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.db.models import Q
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import DocumentType, LostItem, FoundItem, Match, Notification, CustomUser
from .serializers import (
    UserSerializer, DocumentTypeSerializer, LostItemSerializer,
    FoundItemSerializer, MatchSerializer, NotificationSerializer, RegisterSerializer,
    OCRResultSerializer
)
from .services import MatchingService
from ocr.services import OCRService

import logging
logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        authenticate_kwargs = {
            'username': attrs[self.username_field],
            'password': attrs['password'],
        }
        self.user = authenticate(**authenticate_kwargs)
        if self.user is None or not self.user.is_active:
            raise serializers.ValidationError(
                'No active account found with the given credentials'
            )
        refresh = self.get_token(self.user)
        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        # Ajouter les informations de rôle
        user_data = UserSerializer(self.user).data
        data['user'] = user_data
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            return Response({'detail': 'No active account found with the given credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

class HomeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'message': 'Bienvenue sur l\'API FindMyID',
            'version': '1.0',
            'endpoints': {
                'api': '/api/',
                'admin': '/admin/',
                'docs': '/api/'  # Assuming DRF browsable API
            }
        })

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Utilisateur créé avec succès',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class DocumentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentType.objects.all()
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]

class LostItemViewSet(viewsets.ModelViewSet):
    serializer_class = LostItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see all items
            return LostItem.objects.all()
        return LostItem.objects.filter(user=user)
    
    def perform_create(self, serializer):
        lost_item = serializer.save(user=self.request.user)
        logger.info(f"Created LostItem: {lost_item.id}")
        # No OCR for lost items, matching triggered by signal
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        lost_item = self.get_object()
        lost_item.status = 'closed'
        lost_item.save()
        return Response({'message': 'Déclaration fermée'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class FoundItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoundItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see all items
            return FoundItem.objects.all()
        return FoundItem.objects.filter(user=user)
    
    def perform_create(self, serializer):
        found_item = serializer.save(user=self.request.user)
        logger.info(f"Created FoundItem: {found_item.id}")
        # OCR processing
        try:
            if hasattr(OCRService, 'process_image_async'):
                OCRService.process_image_async(found_item)
            else:
                OCRService.process_image(found_item)
        except Exception as e:
            logger.error(f"OCR failed for FoundItem {found_item.id}: {e}")
        # Matching will be triggered by signal
    
    @action(detail=True, methods=['post'])
    def process_ocr(self, request, pk=None):
        found_item = self.get_object()
        try:
            ocr_data = OCRService.process_image(found_item.image.path)
            structured_info = ocr_data.get('structured_info', {})
            found_item.first_name = structured_info.get('first_name', '')
            found_item.last_name = structured_info.get('last_name', '')
            found_item.date_of_birth = structured_info.get('date_of_birth')
            found_item.document_number = structured_info.get('document_number', '')
            found_item.ocr_confidence = ocr_data.get('confidence', 0.0)
            found_item.status = 'processed'

            # Associer le type de document si détecté
            doc_type_name = ocr_data.get('document_type', 'inconnu')
            try:
                doc_type = DocumentType.objects.get(name=doc_type_name.replace('_', ' ').title())
                found_item.document_type = doc_type
            except DocumentType.DoesNotExist:
                pass

            found_item.save()

            # Recherche de correspondances
            MatchingService.find_matches(found_item)

            return Response({
                'message': 'OCR traité avec succès',
                'ocr_data': ocr_data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see all matches
            return Match.objects.all()
        return Match.objects.filter(
            Q(lost_item__user=user) |
            Q(found_item__user=user)
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        match = self.get_object()
        if match.lost_item.user == request.user:
            match.status = 'confirmed'
            match.save()
            
            # Créer notification pour le trouveur
            Notification.objects.create(
                user=match.found_item.user,
                match=match,
                notification_type='match_confirmed',
                title='Correspondance confirmée',
                message=f'La personne ayant perdu {match.lost_item.document_type.name} a confirmé la correspondance.'
            )
            
            return Response({'message': 'Correspondance confirmée'})
        return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        match = self.get_object()
        if match.lost_item.user == request.user:
            match.status = 'rejected'
            match.save()
            return Response({'message': 'Correspondance rejetée'})
        return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def hand_over(self, request, pk=None):
        match = self.get_object()
        if match.found_item.user == request.user:
            match.status = 'handed_over'
            match.save()
            
            # Mettre à jour les statuts
            match.lost_item.status = 'found'
            match.lost_item.save()
            match.found_item.status = 'handed_over'
            match.found_item.save()
            
            # Créer notification
            Notification.objects.create(
                user=match.lost_item.user,
                match=match,
                notification_type='item_handed_over',
                title='Pièce remise',
                message=f'Votre {match.lost_item.document_type.name} a été remise avec succès.'
            )
            
            return Response({'message': 'Pièce remise avec succès'})
        return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            # Admin can see all notifications
            return Notification.objects.all()
        return Notification.objects.filter(user=user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marquée comme lue'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'message': 'Toutes les notifications marquées comme lues'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return CustomUser.objects.all()

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        admin_users = CustomUser.objects.filter(is_staff=True).count()
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
        })

    def perform_create(self, serializer):
        user = serializer.save()
        user.is_staff = True  # New admins
        user.save()


class OCRAnalyseView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Analyse OCR d'une image de document d'identité.
        Reçoit une image et retourne les données structurées avec niveau de confiance.
        """
        if 'image' not in request.FILES:
            return Response({'error': 'Aucune image fournie'}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']

        # Validation du type de fichier
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg']
        if image_file.content_type not in allowed_types:
            return Response({'error': 'Type de fichier non supporté. Utilisez JPEG ou PNG.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validation de la taille (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response({'error': 'Fichier trop volumineux. Maximum 10MB.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Sauvegarde temporaire de l'image
            file_name = default_storage.save(f'temp_ocr/{image_file.name}', ContentFile(image_file.read()))
            temp_path = default_storage.path(file_name)

            # Traitement OCR avec le nouveau pipeline
            ocr_result = OCRService.analyse_document(temp_path)

            # Nettoyage du fichier temporaire
            default_storage.delete(file_name)

            # Sérialisation du résultat
            serializer = OCRResultSerializer(ocr_result)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Nettoyage en cas d'erreur
            if 'file_name' in locals():
                try:
                    default_storage.delete(file_name)
                except:
                    pass
            return Response({'error': f'Erreur lors de l\'analyse OCR: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
