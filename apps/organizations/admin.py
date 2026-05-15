from django.contrib import admin
from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display      = ['name', 'address', 'org_type', 'rating', 'reviews_count', 'is_active']
    list_filter       = ['org_type', 'categories', 'is_active']
    search_fields     = ['name', 'address']
    list_editable     = ['is_active', 'rating']
    filter_horizontal = ['categories']
    fieldsets = (
        ('Основное', {'fields': ('name', 'address', 'phone', 'org_type', 'is_active')}),
        ('Координаты', {'fields': ('latitude', 'longitude')}),
        ('Логотип', {'fields': ('logo', 'logo_text', 'logo_color')}),
        ('Рейтинг', {'fields': ('rating', 'reviews_count')}),
        ('Режим работы', {'fields': ('work_hours',)}),
        ('Категории', {'fields': ('categories',)}),
    )
