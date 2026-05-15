from django.contrib import admin
from .models import Vehicle, MaintenanceRecord


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display  = ['brand', 'model', 'year', 'mileage', 'drive_style', 'user', 'is_active']
    list_filter   = ['drive_style', 'is_active']
    search_fields = ['brand', 'model', 'user__phone']


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display  = ['vehicle', 'work_type', 'date', 'mileage', 'cost']
    list_filter   = ['work_type']
    search_fields = ['vehicle__brand', 'vehicle__model']
