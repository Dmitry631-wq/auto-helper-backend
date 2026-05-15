from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = [
            'id', 'phone', 'username', 'email', 'name',
            'first_name', 'last_name', 'middle_name', 'account_type',
            'medical_cert_expiry', 'medical_cert_issue',
            'driver_license_expiry', 'driver_license_issue',
            'marketing_consent', 'created_at',
        ]
        read_only_fields = ['id', 'phone', 'created_at']


class RegisterSerializer(serializers.Serializer):
    phone             = serializers.CharField(max_length=20)
    password          = serializers.CharField(write_only=True, min_length=6)
    marketing_consent = serializers.BooleanField(default=False)

