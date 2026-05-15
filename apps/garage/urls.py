from django.urls import path
from . import views

urlpatterns = [
    path('vehicles/',                              views.VehicleListCreateView.as_view()),
    path('vehicles/<int:pk>/',                     views.VehicleDetailView.as_view()),
    path('vehicles/<int:vehicle_id>/records/',     views.MaintenanceRecordListCreateView.as_view()),
    path('records/<int:pk>/',                      views.MaintenanceRecordDetailView.as_view()),
    path('vehicles/<int:vehicle_id>/predict/',     views.MaintenancePredictView.as_view()),
    path('vehicles/<int:vehicle_id>/export/',      views.MaintenancePDFView.as_view()),
    path('car-brands/',                            views.CarBrandsView.as_view()),
    path('car-models/',                            views.CarModelsView.as_view()),
]
