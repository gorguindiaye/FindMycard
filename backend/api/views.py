from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.db.models import Q
from datetime import datetime
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import DocumentType, LostItem, FoundItem, Match, Notification, CustomUser, Historique, VerificationRequest
from .serializers import (
    UserSerializer, DocumentTypeSerializer, LostItemSerializer,
    FoundItemSerializer, MatchSerializer, NotificationSerializer, RegisterSerializer,
    OCRResultSerializer, VerificationRequestSerializer
)
from .permissions import (
    AdminPermission,
    AdminPlateformePermission,
    IsOwnerOrAdminPermission,
    IsOwner,
    IsAdminPlatform,
    IsAdminPublic
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
    permission_classes = [IsOwnerOrAdminPermission.for_role('admin_public')]

    def get_queryset(self):
        user = self.request.user
        if user.has_role_or_higher('admin_public'):
            # Admins can see all items
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

    @action(
        detail=True,
        methods=['post'],
        url_path='confirm-receipt',
        permission_classes=[IsOwner]
    )
    def confirm_receipt(self, request, pk=None):
        """
        Permet au déclarant de confirmer qu'il a récupéré sa pièce.
        """
        lost_item = self.get_object()
        lost_item.status = 'found'
        lost_item.save()

        Historique.enregistrerAction(
            user=request.user,
            action='match_confirmed',
            description=f"Confirmation de restitution pour la déclaration #{lost_item.id}",
            related_object=lost_item
        )

        Notification.objects.create(
            user=request.user,
            notification_type='item_handed_over',
            title='Restitution confirmée',
            message=f'Vous avez confirmé la restitution de votre {lost_item.document_type.name}.'
        )
        return Response({'message': 'Restitution confirmée'}, status=status.HTTP_200_OK)

class FoundItemViewSet(viewsets.ModelViewSet):
    serializer_class = FoundItemSerializer
    permission_classes = [IsOwnerOrAdminPermission.for_role('admin_public')]

    def get_queryset(self):
        user = self.request.user
        if user.has_role_or_higher('admin_public'):
            # Admins can see all items
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
            payload = ocr_data.get('structured_payload', {})
            found_item.first_name = payload.get('prenom', structured_info.get('first_name', '')).title()
            found_item.last_name = payload.get('nom', structured_info.get('last_name', '')).title()
            date_naissance = payload.get('date_naissance')
            if date_naissance:
                try:
                    found_item.date_of_birth = datetime.strptime(date_naissance, '%Y-%m-%d').date()
                except ValueError:
                    found_item.date_of_birth = structured_info.get('date_of_birth')
            else:
                found_item.date_of_birth = structured_info.get('date_of_birth')
            found_item.document_number = payload.get('num_document') or structured_info.get('document_number', '')
            found_item.ocr_confidence = ocr_data.get('confidence', 0.0)
            found_item.status = 'processed'

            # Associer le type de document si détecté
            doc_type_key = ocr_data.get('document_type', 'autre')
            doc_type_name = OCRService.DOCUMENT_LABELS.get(doc_type_key, doc_type_key.replace('_', ' ').title())
            try:
                doc_type = DocumentType.objects.get(name=doc_type_name)
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

    @action(
        detail=True,
        methods=['post'],
        url_path='respond',
        permission_classes=[IsOwner]
    )
    def respond(self, request, pk=None):
        """
        Permet au trouveur de répondre à une sollicitation (message, point de dépôt, disponibilité).
        """
        found_item = self.get_object()
        response_message = request.data.get('message', '')
        drop_off_point = request.data.get('drop_off_point', '')
        availability = request.data.get('availability', '')

        note_parts = [
            found_item.description or '',
            f"Réponse du trouveur: {response_message}" if response_message else '',
            f"Point de dépôt proposé: {drop_off_point}" if drop_off_point else '',
            f"Disponibilité: {availability}" if availability else '',
        ]
        found_item.description = '\n'.join([part for part in note_parts if part])
        found_item.save()

        Historique.enregistrerAction(
            user=request.user,
            action='match_confirmed',
            description=f"Réponse du trouveur pour la trouvaille #{found_item.id}",
            related_object=found_item
        )

        Notification.objects.create(
            user=found_item.user,
            notification_type='match_found',
            title='Réponse envoyée',
            message='Votre réponse a été prise en compte et sera partagée avec le déclarant.'
        )

        return Response({'message': 'Réponse enregistrée'}, status=status.HTTP_200_OK)

class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [IsOwnerOrAdminPermission.for_role('admin_public')]

    def get_queryset(self):
        user = self.request.user
        if user.has_role_or_higher('admin_public'):
            # Admins can see all matches
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

    @action(
        detail=True,
        methods=['post'],
        url_path='validate',
        permission_classes=[IsAdminPlatform]
    )
    def validate_match(self, request, pk=None):
        """
        Validation par un administrateur plateforme.
        """
        match = self.get_object()
        match.status = 'confirmed'
        match.save()

        match.lost_item.status = 'found'
        match.lost_item.save()
        match.found_item.status = 'processed'
        match.found_item.save()

        Notification.objects.bulk_create([
            Notification(
                user=match.lost_item.user,
                match=match,
                notification_type='match_confirmed',
                title='Correspondance validée',
                message='L\'administrateur a validé la correspondance. Préparez la restitution.'
            ),
            Notification(
                user=match.found_item.user,
                match=match,
                notification_type='match_confirmed',
                title='Correspondance validée',
                message='L\'administrateur a validé la correspondance. Coordonnez-vous avec le propriétaire.'
            ),
        ])

        Historique.enregistrerAction(
            user=request.user,
            action='match_confirmed',
            description=f'Validation admin plateforme du match #{match.id}',
            related_object=match
        )

        return Response({'message': 'Correspondance validée'}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        url_path='invalidate',
        permission_classes=[IsAdminPlatform]
    )
    def invalidate_match(self, request, pk=None):
        """
        Invalidation par l'administrateur plateforme (avec motif).
        """
        match = self.get_object()
        reason = request.data.get('reason', 'Décision administrative')

        match.status = 'rejected'
        criteria = match.match_criteria or {}
        criteria['admin_decision'] = {'status': 'rejected', 'reason': reason}
        match.match_criteria = criteria
        match.save()

        Notification.objects.bulk_create([
            Notification(
                user=match.lost_item.user,
                match=match,
                notification_type='match_found',
                title='Correspondance rejetée',
                message=f'La correspondance a été rejetée. Motif : {reason}'
            ),
            Notification(
                user=match.found_item.user,
                match=match,
                notification_type='match_found',
                title='Correspondance rejetée',
                message=f'La correspondance a été rejetée. Motif : {reason}'
            ),
        ])

        Historique.enregistrerAction(
            user=request.user,
            action='match_rejected',
            description=f'Rejet admin plateforme du match #{match.id} : {reason}',
            related_object=match
        )

        return Response({'message': 'Correspondance rejetée'}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post'],
        url_path='request-auth-check',
        permission_classes=[IsAdminPlatform]
    )
    def request_auth_check(self, request, pk=None):
        """
        Permet de solliciter l'administration publique pour vérifier l'authenticité.
        """
        match = self.get_object()
        criteria = match.match_criteria or {}
        criteria['needs_admin_public_review'] = True
        match.match_criteria = criteria
        match.save()

        verification, created = VerificationRequest.objects.get_or_create(
            match=match,
            defaults={
                'requested_by': request.user,
                'notes': request.data.get('notes', '')
            }
        )

        if not created:
            verification.status = 'pending'
            verification.notes = request.data.get('notes', verification.notes)
            verification.decision_reason = ''
            verification.save()

        admin_public_users = CustomUser.objects.filter(role='admin_public')
        Notification.objects.bulk_create([
            Notification(
                user=admin_user,
                match=match,
                notification_type='match_found',
                title='Vérification requise',
                message='Un dossier nécessite une vérification d\'authenticité.'
            ) for admin_user in admin_public_users
        ])

        Historique.enregistrerAction(
            user=request.user,
            action='match_confirmed',
            description=f'Demande de vérification admin public pour le match #{match.id}',
            related_object=match
        )

        return Response({'message': 'Demande de vérification transmise'}, status=status.HTTP_200_OK)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsOwnerOrAdminPermission.for_role('admin_public')]

    def get_queryset(self):
        user = self.request.user
        if user.has_role_or_higher('admin_public'):
            # Admins can see all notifications
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
    
    @action(
        detail=False,
        methods=['post'],
        url_path='send',
        permission_classes=[IsAdminPlatform]
    )
    def send_notification(self, request):
        """
        Permet aux administrateurs plateforme d'envoyer une notification ciblée.
        """
        user_id = request.data.get('user_id')
        title = request.data.get('title', 'Notification')
        message = request.data.get('message', '')
        match_id = request.data.get('match_id')

        if not user_id or not message:
            return Response({'error': 'user_id et message sont requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

        match = None
        if match_id:
            try:
                match = Match.objects.get(id=match_id)
            except Match.DoesNotExist:
                return Response({'error': 'Match introuvable'}, status=status.HTTP_404_NOT_FOUND)

        notification = Notification.objects.create(
            user=target_user,
            match=match,
            notification_type='match_found',
            title=title,
            message=message
        )

        Historique.enregistrerAction(
            user=request.user,
            action='item_handed_over',
            description=f'Notification envoyée à {target_user.email}',
            related_object=match or target_user
        )

        return Response({'message': 'Notification envoyée', 'id': notification.id}, status=status.HTTP_201_CREATED)


class VerificationRequestViewSet(viewsets.ModelViewSet):
    serializer_class = VerificationRequestSerializer
    queryset = VerificationRequest.objects.select_related(
        'match',
        'match__lost_item',
        'match__found_item',
        'requested_by',
        'assigned_to'
    )
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create']:
            return [IsAdminPlatform()]
        return [IsAdminPublic()]

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset
        if user.has_role_or_higher('admin_plateforme'):
            return base_qs
        if user.role == 'admin_public':
            return base_qs.filter(
                Q(assigned_to=user) | Q(status__in=['pending', 'in_review'])
            ).distinct()
        return base_qs.filter(requested_by=user)

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        verification = self.get_object()
        reason = request.data.get('reason', 'Authenticité confirmée')
        verification.status = 'confirmed'
        verification.decision_reason = reason
        verification.save()

        match = verification.match
        match.status = 'confirmed'
        match.save()

        Notification.objects.bulk_create([
            Notification(
                user=match.lost_item.user,
                match=match,
                notification_type='match_confirmed',
                title='Authenticité confirmée',
                message='L\'administration a confirmé l\'authenticité de votre document.'
            ),
            Notification(
                user=match.found_item.user,
                match=match,
                notification_type='match_confirmed',
                title='Authenticité confirmée',
                message='Vous pouvez préparer la restitution officielle.'
            )
        ])

        Historique.enregistrerAction(
            user=request.user,
            action='match_confirmed',
            description=f'Vérification confirmée pour le match #{match.id}',
            related_object=match
        )

        return Response({'message': 'Vérification confirmée'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        verification = self.get_object()
        reason = request.data.get('reason', 'Authenticité refusée')
        verification.status = 'rejected'
        verification.decision_reason = reason
        verification.save()

        match = verification.match
        match.status = 'rejected'
        match.save()

        Notification.objects.bulk_create([
            Notification(
                user=match.lost_item.user,
                match=match,
                notification_type='match_found',
                title='Authenticité refusée',
                message=f'L\'administration a refusé la correspondance : {reason}'
            ),
            Notification(
                user=match.found_item.user,
                match=match,
                notification_type='match_found',
                title='Authenticité refusée',
                message=f'L\'administration a refusé la correspondance : {reason}'
            )
        ])

        Historique.enregistrerAction(
            user=request.user,
            action='match_rejected',
            description=f'Refus de vérification pour le match #{match.id} : {reason}',
            related_object=match
        )

        return Response({'message': 'Vérification rejetée'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='supervise-restitution')
    def supervise_restitution(self, request, pk=None):
        verification = self.get_object()
        verification.status = 'supervised'
        verification.decision_reason = request.data.get('notes', 'Restitution supervisée')
        verification.save()

        match = verification.match
        match.status = 'handed_over'
        match.save()
        match.lost_item.status = 'found'
        match.lost_item.save()
        match.found_item.status = 'handed_over'
        match.found_item.save()

        Notification.objects.bulk_create([
            Notification(
                user=match.lost_item.user,
                match=match,
                notification_type='item_handed_over',
                title='Restitution supervisée',
                message='La restitution a été supervisée par l\'administration.'
            ),
            Notification(
                user=match.found_item.user,
                match=match,
                notification_type='item_handed_over',
                title='Restitution supervisée',
                message='La restitution a été supervisée et confirmée.'
            )
        ])

        Historique.enregistrerAction(
            user=request.user,
            action='item_handed_over',
            description=f'Restitution supervisée pour le match #{match.id}',
            related_object=match
        )

        return Response({'message': 'Supervision enregistrée'}, status=status.HTTP_200_OK)

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        """
        Permet une logique de permission dynamique basée sur l'action.
        """
        if self.action in ['create']:
            permission_classes = [AdminPlateformePermission]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_plateforme():
            # Admin plateforme can see all users
            return CustomUser.objects.all()
        elif user.is_admin_public():
            # Admin public can see citoyens and themselves
            return CustomUser.objects.filter(role__in=['citoyen', 'admin_public'])
        return CustomUser.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = self.request.user
        if not user.has_role_or_higher('admin_public'):
            return Response({'error': 'Non autorisé'}, status=status.HTTP_403_FORBIDDEN)

        total_users = CustomUser.objects.count()
        active_users = CustomUser.objects.filter(is_active=True).count()
        citoyens = CustomUser.objects.filter(role='citoyen').count()
        admin_public = CustomUser.objects.filter(role='admin_public').count()
        admin_plateforme = CustomUser.objects.filter(role='admin_plateforme').count()
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'citoyens': citoyens,
            'admin_public': admin_public,
            'admin_plateforme': admin_plateforme,
        })

    def perform_create(self, serializer):
        user = self.request.user
        if not user.is_admin_plateforme():
            raise serializers.ValidationError("Seuls les administrateurs plateforme peuvent créer des utilisateurs.")
        new_user = serializer.save()
        # Set appropriate staff status based on role
        if new_user.role in ['admin_public', 'admin_plateforme']:
            new_user.is_staff = True
        new_user.save()
        # Log the creation of new user
        logger.info(f"Admin {user.username} created user {new_user.username} with role {new_user.role}")


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

class HistoriqueView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        # For now, return empty list as history is not implemented yet
        # In future, could aggregate user actions from various models
        historique = []
        return Response(historique)
