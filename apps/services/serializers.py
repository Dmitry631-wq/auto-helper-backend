# serializers
from rest_framework import serializers
from .models import Category, Service


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon']


class ServiceSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image    = serializers.SerializerMethodField()

    class Meta:
        model  = Service
        fields = ['id', 'category', 'title', 'description', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
