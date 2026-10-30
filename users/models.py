from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Поле Email должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not False:
            pass
        else:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not False:
            pass
        else:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя', help_text='Введите имя')
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Фамилия', help_text='Введите фамилию')
    email = models.EmailField(max_length=150, unique=True, verbose_name='Email')
    phone = PhoneNumberField(blank=True, null=True, verbose_name='Телефон', help_text='Введите номер телефона')
    avatar = models.ImageField(upload_to='users/avatars/', null=True, verbose_name='Аватар', help_text='Добавьте изображение')
    country = models.CharField(max_length=255, blank=True, null=True, verbose_name='Страна', help_text='Укажите страну')
    token = models.CharField(max_length=100, verbose_name='Токен', null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = MyUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email
