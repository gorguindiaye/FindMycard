from rest_framework import permissions
from .models import CustomUser

class RoleBasedPermission(permissions.BasePermission):
    """
    Permission personnalisée pour vérifier si l'utilisateur a un rôle spécifique ou supérieur.
    """
    def __init__(self, required_role='citoyen'):
        self.required_role = required_role

    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        return user.has_role_or_higher(self.required_role)

class AdminPlateformePermission(RoleBasedPermission):
    """Permission pour les administrateurs plateforme uniquement."""
    def __init__(self):
        super().__init__('admin_plateforme')


class IsAdminPlatform(AdminPlateformePermission):
    """Alias plus explicite pour la plateforme."""
    pass


class AdminPermission(RoleBasedPermission):
    """Permission pour les administrateurs (public ou plateforme)."""
    def __init__(self):
        super().__init__('admin_public')


class IsAdminPublic(AdminPermission):
    """Alias explicite pour l'administration publique."""
    pass

class IsOwnerOrAdminPermission(permissions.BasePermission):
    """
    Permission pour permettre l'accès aux objets appartenant à l'utilisateur
    ou aux administrateurs avec le rôle approprié.
    """
    def __init__(self, required_role='admin_public'):
        self.required_role = required_role

    @classmethod
    def for_role(cls, required_role):
        """
        Fabrique dynamiquement une classe de permission liée à un rôle précis
        afin de pouvoir être utilisée directement dans permission_classes.
        """
        class _IsOwnerOrAdminPermission(cls):
            def __init__(self):
                super().__init__(required_role)

        _IsOwnerOrAdminPermission.__name__ = f"{cls.__name__}_{required_role}"
        return _IsOwnerOrAdminPermission

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_authenticated and (user.id == obj.user.id or user.has_role_or_higher(self.required_role)):
            return True
        return False

    def has_permission(self, request, view):
        # Pour les actions qui ne nécessitent pas d'objet spécifique (list, create)
        user = request.user
        if not user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            # Lecture : permettre aux admins
            return user.has_role_or_higher(self.required_role)
        # Écriture : permettre aux propriétaires ou admins
        return True  # La vérification détaillée se fait dans has_object_permission


class IsOwner(permissions.BasePermission):
    """
    Permission stricte pour vérifier que l'objet appartient à l'utilisateur courant.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        owner = getattr(obj, 'user', None) or getattr(obj, 'owner', None)
        return owner is not None and owner.id == user.id


class IsPerdant(permissions.BasePermission):
    """
    Vérifie que l'utilisateur est un citoyen effectuant une déclaration de perte.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'citoyen'


class IsTrouveur(IsPerdant):
    """
    Alias sémantique pour les trouveurs (même rôle citoyen côté modèle actuel).
    """
    pass
