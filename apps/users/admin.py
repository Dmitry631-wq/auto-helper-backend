from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SmsCode


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['phone', 'username', 'account_type', 'is_active', 'created_at']
    list_filter   = ['account_type', 'is_active', 'is_staff']
    search_fields = ['phone', 'username', 'email']
    ordering      = ['-created_at']
    fieldsets = (
        (None, {'fields': ('phone', 'username', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name', 'middle_name', 'email', 'account_type')}),
        ('Документы', {'fields': ('medical_cert_expiry', 'medical_cert_issue', 'driver_license_expiry', 'driver_license_issue')}),
        ('Настройки', {'fields': ('marketing_consent', 'fcm_token')}),
        ('Права', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('phone', 'username', 'password1', 'password2')}),
    )


@admin.register(SmsCode)
class SmsCodeAdmin(admin.ModelAdmin):
    list_display  = ['phone', 'code', 'purpose', 'created_at']
    list_filter   = ['purpose']
    search_fields = ['phone']
    readonly_fields = ['created_at']