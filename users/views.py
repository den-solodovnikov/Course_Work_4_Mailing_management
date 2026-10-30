import secrets

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView, PasswordResetView, PasswordResetConfirmView
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView

from config.settings import EMAIL_HOST_USER
from users.forms import UserRegisterForm, CustomPasswordResetForm, CustomSetPasswordForm
from users.models import User


class UserCreateView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        user.is_active = False
        token = secrets.token_hex(16)
        user.token = token
        user.save()
        host = self.request.get_host()
        url = f'http://{host}/users/email-confirm/{token}/'
        send_mail(
            subject='Подтверждение почты',
            message=f'Здравствуйте. Вы зарегистрировались на сайте Mailings (Сервис управления рассылками). '
                    f'Для подтверждения регистрации, перейдите по ссылке {url}',
            from_email=EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('users:logout')
    # template_name = 'users/logged_out.html'
    success_url = reverse_lazy('mailing:index')

def email_verification(request, token):
    user = get_object_or_404(User, token=token)
    user.is_active = True
    user.save()
    return redirect(reverse('users:login'))


class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')


class CustomUserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    form_class = CustomSetPasswordForm