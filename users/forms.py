from django.contrib.auth import forms, password_validation
from django.contrib.auth import forms
from django.forms import BooleanField

from users.models import User


class StyleFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fild_name, fild_value in self.fields.items():
            if isinstance(fild_value, BooleanField):
                fild_value.widget.attrs['class'] = 'form-check-input'
            else:
                fild_value.widget.attrs['class'] = 'form-control'


class UserRegisterForm(StyleFormMixin, forms.UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'phone', 'avatar', 'country', 'password1', 'password2',)


class CustomPasswordResetForm(forms.PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите Email',
            'autocomplete': 'email',
            'max_length': '150'
        })


class CustomSetPasswordForm(forms.SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Изменяем сообщение об ошибке несовпадения паролей
        self.error_messages['password_mismatch'] = "Пароли не совпадают"

        # Кастомизируем первое поле (Новый пароль)
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите новый пароль',
            'autocomplete': 'new-password'
        })

        # Кастомизируем второе поле (Подтверждение пароля)
        self.fields['new_password2'].label = 'Подтверждение нового пароля'
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль',
            'autocomplete': 'new-password'
        })
