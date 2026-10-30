from django.contrib.auth.views import LoginView, PasswordResetCompleteView, PasswordResetDoneView
from django.urls import path
from django.views.generic import TemplateView

from users.apps import UsersConfig
from users.views import CustomLogoutView, UserCreateView, email_verification, CustomPasswordResetView, \
    CustomUserPasswordResetConfirmView

app_name = UsersConfig.name

urlpatterns = [
    path('users/login/', LoginView.as_view(template_name='users/login.html'), name='login'),
    path('users/logged-out/', CustomLogoutView.as_view(template_name='users/logged_out.html'), name='logout'),
    path('users/register', UserCreateView.as_view(), name='register'),
    path('users/email-confirm/<str:token>/', email_verification, name='email-confirm'),
    path('users/password-reset/', CustomPasswordResetView.as_view(), name='password-reset'),
    path('users/password_reset_confirm/<uidb64>/<token>/',
         CustomUserPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('users/password_reset_complete/',
         PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'),
         name='password_reset_complete'),
    path('users/password-reset_done/',
         PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
]
