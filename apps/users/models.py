from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra):
        if not phone:
            raise ValueError('Phone is required')
        user = self.model(phone=phone, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    phone      = models.CharField('Телефон', max_length=20, unique=True)
    username   = models.CharField('Имя пользователя', max_length=150, blank=True)
    email      = models.EmailField('Email', blank=True)
    name       = models.CharField('Имя', max_length=150, blank=True)
    first_name = models.CharField('Имя', max_length=100, blank=True)
    last_name  = models.CharField('Фамилия', max_length=100, blank=True)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    account_type = models.CharField('Тип аккаунта', max_length=20, default='personal')

    # Документы
    medical_cert_expiry    = models.DateField('Срок мед. справки', null=True, blank=True)
    medical_cert_issue     = models.DateField('Дата выдачи мед. справки', null=True, blank=True)
    driver_license_expiry  = models.DateField('Срок ВУ', null=True, blank=True)
    driver_license_issue   = models.DateField('Дата выдачи ВУ', null=True, blank=True)

    # FCM
    fcm_token = models.TextField('FCM Token', blank=True)

    # Сброс пароля
    reset_token = models.CharField('Токен сброса пароля', max_length=100, blank=True)

    marketing_consent = models.BooleanField('Согласие на рассылку', default=False)

    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects  = UserManager()
    USERNAME_FIELD  = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name        = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.phone


class SmsCode(models.Model):
    PURPOSE_CHOICES = [
        ('reset',    'Сброс пароля'),
        ('register', 'Регистрация'),
        ('email',    'Подтверждение email'),
    ]
    phone      = models.CharField('Телефон', max_length=20)
    code       = models.CharField('Код', max_length=10)
    purpose    = models.CharField('Назначение', max_length=20,
                                  choices=PURPOSE_CHOICES, default='reset')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'SMS-код'
        verbose_name_plural = 'SMS-коды'

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f'{self.phone} — {self.code}'
