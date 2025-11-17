from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, UserView, DocumentTypeViewSet, LostItemViewSet,
    FoundItemViewSet, MatchViewSet, NotificationViewSet, CustomTokenObtainPairView,
    OCRAnalyseView, HomeView, UserViewSet
)

router = DefaultRouter()
router.register(r'document-types', DocumentTypeViewSet, basename='document-types')
router.register(r'lost-items', LostItemViewSet, basename='lost-item')
router.register(r'found-items', FoundItemViewSet, basename='found-item')
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('users/me/', UserView.as_view(), name='user_me'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/user/', UserView.as_view(), name='user'),
    path('ocr-analyse/', OCRAnalyseView.as_view(), name='ocr_analyse'),
]
