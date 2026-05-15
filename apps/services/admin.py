from django.contrib import admin
from .models import Category, Service


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'icon', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display  = ['title', 'category', 'is_active', 'order']
    list_filter   = ['category', 'is_active']
    search_fields = ['title']
    list_editable = ['is_active', 'order']
