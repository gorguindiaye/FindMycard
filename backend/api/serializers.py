from rest_framework import serializers
from .models import DocumentType, LostItem, FoundItem, Match, Notification, CustomUser, VerificationRequest

class UserSerializer(serializers.ModelSerializer):
    is_admin_plateforme = serializers.SerializerMethodField()
    is_admin_public = serializers.SerializerMethodField()
    is_citoyen = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()  # For backward compatibility

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_admin', 'is_admin_plateforme', 'is_admin_public', 'is_citoyen']
        read_only_fields = ['id']

    def get_is_admin(self, obj):
        return obj.is_admin()

    def get_is_admin_plateforme(self, obj):
        return obj.is_admin_plateforme()

    def get_is_admin_public(self, obj):
        return obj.is_admin_public()

    def get_is_citoyen(self, obj):
        return obj.is_citoyen()

class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'

class LostItemSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    document_type = DocumentTypeSerializer(read_only=True)
    document_type_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = LostItem
        fields = [
            'id', 'user', 'document_type', 'document_type_id', 'first_name', 
            'last_name', 'date_of_birth', 'document_number', 'lost_date', 
            'lost_location', 'description', 'contact_phone', 'contact_email', 
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class FoundItemSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    document_type = DocumentTypeSerializer(read_only=True)
    document_type_id = serializers.IntegerField(write_only=True)
    image = serializers.ImageField(required=False)

    class Meta:
        model = FoundItem
        fields = [
            'id', 'user', 'document_type', 'document_type_id', 'image',
            'first_name', 'last_name', 'date_of_birth', 'document_number',
            'found_date', 'found_location', 'description', 'contact_phone',
            'contact_email', 'status', 'ocr_confidence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'first_name', 'last_name', 'date_of_birth',
                           'document_number', 'ocr_confidence', 'created_at', 'updated_at']

class MatchSerializer(serializers.ModelSerializer):
    lost_item = LostItemSerializer(read_only=True)
    found_item = FoundItemSerializer(read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'lost_item', 'found_item', 'confidence_score', 
            'match_criteria', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'confidence_score', 'match_criteria', 'created_at', 'updated_at']

class NotificationSerializer(serializers.ModelSerializer):
    match = MatchSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'match', 'notification_type', 'title', 
            'message', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        default='citoyen',
        required=False
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Les mots de passe ne correspondent pas.")

        # Validation du rôle - prévention de l'élévation de privilèges
        request = self.context.get('request')
        requested_role = attrs.get('role', 'citoyen')

        if requested_role != 'citoyen':
            # Seuls les admin_plateforme peuvent créer des comptes admin
            if not request or not request.user.is_authenticated or not request.user.is_admin_plateforme():
                raise serializers.ValidationError("Seuls les administrateurs plateforme peuvent créer des comptes administrateur.")

        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'citoyen')
        validated_data.pop('password_confirm')
        validated_data['username'] = validated_data['email']
        validated_data['role'] = role
        user = CustomUser.objects.create_user(**validated_data)
        return user

class OCRResultSerializer(serializers.Serializer):
    """
    Serializer pour les résultats de l'analyse OCR avancée.
    """
    document_type = serializers.CharField(max_length=100, required=False)
    first_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    document_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    place_of_birth = serializers.CharField(max_length=100, required=False, allow_blank=True)
    nationality = serializers.CharField(max_length=50, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    confidence_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    validation_status = serializers.ChoiceField(choices=['valid', 'suspect', 'invalid'])
    extracted_text = serializers.CharField(required=False, allow_blank=True)
    processing_time = serializers.FloatField(min_value=0.0, required=False)


class VerificationRequestSerializer(serializers.ModelSerializer):
    match = MatchSerializer(read_only=True)
    match_id = serializers.IntegerField(write_only=True, required=False)
    requested_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)

    class Meta:
        model = VerificationRequest
        fields = [
            'id',
            'match',
            'match_id',
            'requested_by',
            'assigned_to',
            'status',
            'notes',
            'decision_reason',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'requested_by', 'assigned_to', 'created_at', 'updated_at', 'status']
