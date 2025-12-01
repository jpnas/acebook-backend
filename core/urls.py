from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'courts', views.CourtViewSet, basename='court')
router.register(r'coaches', views.CoachViewSet, basename='coach')
router.register(r'reservations', views.ReservationViewSet, basename='reservation')
router.register(r'club-users', views.ClubUserViewSet, basename='club-user')

urlpatterns = [
    path('auth/login/', views.ClubTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/password/forgot/', views.ForgotPasswordView.as_view(), name='password_forgot'),
    path('auth/password/reset/', views.ResetPasswordView.as_view(), name='password_reset'),
    path('clubs/check-slug/', views.ClubSlugAvailabilityView.as_view(), name='club_slug_check'),
    path('me/', views.MeView.as_view(), name='me'),
    path('', include(router.urls)),
]
