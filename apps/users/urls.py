from django.urls import path

from .views import (
    JWTTokenLogOutView,
    JWTTokenRefreshView,
    JWTTokenView,
    LogOutView,
    LoginView,
    ProfileView,
    RegisterView,
    TokenLogOutView,
    TokenView,
)



urlpatterns = [
    path('login/token/', TokenView.as_view(), name='token'),
    path('logout/token/', TokenLogOutView.as_view(), name='token-out'),

    path('login/jwt/', JWTTokenView.as_view(), name='jwt-login'),
    path('refresh/jwt/', JWTTokenRefreshView.as_view(), name='jwt-refresh'),
    path('logout/jwt/', JWTTokenLogOutView.as_view(), name='jwt-logout'),
    

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogOutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
