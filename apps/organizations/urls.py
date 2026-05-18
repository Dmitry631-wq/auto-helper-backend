from django.urls import path
from .serializers_and_views import (
    OrganizationListView, OrganizationDetailView,
    FavoriteListView, FavoriteToggleView, ReviewListCreateView,ReviewDetailView,AppRatingView
)

urlpatterns = [
    path('',                       OrganizationListView.as_view()),
    path('<int:pk>/',              OrganizationDetailView.as_view()),
    path('favorites/',             FavoriteListView.as_view()),
    path('<int:org_id>/favorite/', FavoriteToggleView.as_view()),
    path('<int:org_id>/reviews/',  ReviewListCreateView.as_view()),
    path('<int:org_id>/reviews/<int:review_id>/',  ReviewDetailView.as_view()),
    path('app-rating/', AppRatingView.as_view()),
]
