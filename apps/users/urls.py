from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    TokenRefreshCookieView,
    MeView,
    UserProfileListView,
    UserProfileDetailView,
    EncargadoActivoListCreateView,
    EncargadoActivoDetailView,
)

urlpatterns = [
    # Auth (included under api/v1/auth/)
    path("login/", LoginView.as_view(), name="auth-login"),
    path("logout/", LogoutView.as_view(), name="auth-logout"),
    path("refresh/", TokenRefreshCookieView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),

    # User management
    path("users/", UserProfileListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserProfileDetailView.as_view(), name="user-detail"),

    path("encargados/", EncargadoActivoListCreateView.as_view(), name="encargado-list"),
    path("encargados/<int:pk>/", EncargadoActivoDetailView.as_view(), name="encargado-detail"),
]
