from django.urls import path
from . import views

urlpatterns = [
    path('',              views.ServiceListView.as_view()),
    path('<int:pk>/',     views.ServiceDetailView.as_view()),
    path('categories/',   views.CategoryListView.as_view()),
    path('2gis/search/',  views.TwoGisSearchView.as_view()),
    path('2gis/reviews/', views.TwoGisReviewsView.as_view()),
]
