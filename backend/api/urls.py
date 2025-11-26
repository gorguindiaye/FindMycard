from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'lost-items', views.LostItemViewSet)
router.register(r'found-items', views.FoundItemViewSet)
router.register(r'matches', views.MatchViewSet)
router.register(r'notifications', views.NotificationViewSet)
router.register(r'verification-requests', views.VerificationRequestViewSet)
router.register(r'document-types', views.DocumentTypeViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('auth/user/', views.UserView.as_view(), name='current_user'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
]
