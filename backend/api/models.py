from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """Modèle User personnalisé avec gestion des rôles"""
    ROLE_CHOICES = [
        ('citoyen', 'Citoyen'),
        ('admin_public', 'Administration Publique'),
        ('admin_plateforme', 'Administrateur Plateforme'),
    ]

    ROLE_HIERARCHY = {
        'citoyen': 1,
        'admin_public': 2,
        'admin_plateforme': 3,
    }

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='citoyen',
        verbose_name='Rôle'
    )

    def is_citoyen(self):
        return self.role == 'citoyen'

    def is_admin_public(self):
        return self.role == 'admin_public'

    def is_admin_plateforme(self):
        return self.role == 'admin_plateforme'

    def is_admin(self):
        # Alias for backward compatibility, but now checks for admin_plateforme
        return self.is_admin_plateforme()

    def has_role_or_higher(self, required_role):
        """Vérifie si l'utilisateur a le rôle requis ou un rôle supérieur dans la hiérarchie"""
        user_level = self.ROLE_HIERARCHY.get(self.role, 0)
        required_level = self.ROLE_HIERARCHY.get(required_role, 0)
        return user_level >= required_level

    def __str__(self):
        return f"{self.username} - {self.role}"

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'


class DocumentType(models.Model):
    """Types de documents supportés"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class LostItem(models.Model):
    """Déclaration de perte d'une pièce d'identité"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('found', 'Trouvée'),
        ('closed', 'Fermée'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    document_number = models.CharField(max_length=50, blank=True)
    lost_date = models.DateField()
    lost_location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.document_type.name}"

class FoundItem(models.Model):
    """Déclaration de trouvaille d'une pièce d'identité"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processed', 'Traité'),
        ('matched', 'Correspondance trouvée'),
        ('handed_over', 'Remis'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='found_items/')
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    document_number = models.CharField(max_length=50, blank=True)
    found_date = models.DateField()
    found_location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ocr_confidence = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pièce trouvée - {self.document_type.name}"

class Match(models.Model):
    """Correspondance entre une pièce perdue et une pièce trouvée"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('rejected', 'Rejetée'),
        ('handed_over', 'Remise effectuée'),
    ]
    
    lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='matches')
    found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='matches')
    confidence_score = models.FloatField()
    match_criteria = models.JSONField()  # Critères de correspondance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['lost_item', 'found_item']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Match: {self.lost_item} ↔ {self.found_item}"


class VerificationRequest(models.Model):
    """Demandes de vérification adressées à l'administration publique"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_review', 'En cours de vérification'),
        ('confirmed', 'Authentifié'),
        ('rejected', 'Rejeté'),
        ('supervised', 'Restitution supervisée'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='verification_requests')
    requested_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='verification_requests_created')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verification_requests_assigned')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    decision_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"VerificationRequest Match#{self.match_id} - {self.status}"


class Notification(models.Model):
    """Notifications pour les utilisateurs"""
    TYPE_CHOICES = [
        ('match_found', 'Correspondance trouvée'),
        ('match_confirmed', 'Correspondance confirmée'),
        ('item_handed_over', 'Pièce remise'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class Historique(models.Model):
    """Historique des actions"""
    ACTION_CHOICES = [
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('register', 'Inscription'),
        ('lost_declaration', 'Déclaration de perte'),
        ('found_declaration', 'Déclaration de trouvaille'),
        ('match_found', 'Correspondance trouvée'),
        ('match_confirmed', 'Correspondance confirmée'),
        ('match_rejected', 'Correspondance rejetée'),
        ('item_handed_over', 'Pièce remise'),
        ('profile_update', 'Mise à jour profil'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    related_object_id = models.PositiveIntegerField(null=True, blank=True)  # ID de l'objet lié
    related_object_type = models.CharField(max_length=50, blank=True)  # Type de l'objet lié
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"

    @staticmethod
    def enregistrerAction(user, action, description, related_object=None):
        """Enregistre une action dans l'historique"""
        historique = Historique.objects.create(
            user=user,
            action=action,
            description=description,
            related_object_id=related_object.id if related_object else None,
            related_object_type=related_object.__class__.__name__ if related_object else ''
        )
        return historique

    @staticmethod
    def consulterHistorique(user=None, action=None, date_debut=None, date_fin=None):
        """Consulte l'historique avec filtres"""
        queryset = Historique.objects.all()

        if user:
            queryset = queryset.filter(user=user)
        if action:
            queryset = queryset.filter(action=action)
        if date_debut:
            queryset = queryset.filter(created_at__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(created_at__lte=date_fin)

        return queryset

    @staticmethod
    def filtrerParUtilisateur(user):
        """Filtre l'historique par utilisateur"""
        return Historique.objects.filter(user=user)
