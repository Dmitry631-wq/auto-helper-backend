from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    path('',                    views.home,             name='home'),
    path('catalog/',            views.catalog,          name='catalog'),
    path('catalog/<int:pk>/',   views.org_detail,       name='org_detail'),
    path('catalog/<int:pk>/review/',  views.add_review, name='add_review'),
    path('review/<int:pk>/delete/',   views.delete_review, name='delete_review'),
    path('reviews/',            views.reviews,          name='reviews'),
    path('faq/',                views.faq,              name='faq'),
    path('login/',              views.login_view,       name='login'),
    path('register/',           views.register_view,    name='register'),
    path('logout/',             views.logout_view,      name='logout'),
    path('profile/',            views.profile,          name='profile'),
    path('profile/edit/',       views.edit_profile,     name='edit_profile'),
    path('garage/',             views.garage,           name='garage'),
    path('garage/add/',         views.add_car,          name='add_car'),
    path('garage/<int:pk>/delete/', views.delete_car,   name='delete_car'),
    path('garage/<int:pk>/edit/',   views.edit_car,     name='edit_car'),
    path('rate-app/',           views.rate_app,         name='rate_app'),
    path('forgot-password/',    views.forgot_password,  name='forgot_password'),
]
