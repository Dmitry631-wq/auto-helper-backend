from django.urls import path
from . import views

urlpatterns = [
    path('register/',           views.RegisterView.as_view()),
    path('login/',              views.LoginView.as_view()),
    path('profile/',            views.ProfileView.as_view()),
    path('change-password/',    views.ChangePasswordView.as_view()),
    path('send-code/',          views.SendSmsCodeView.as_view()),
    path('verify-code/',        views.VerifySmsCodeView.as_view()),
    path('recovery/send-code/', views.SendSmsCodeView.as_view()),
    path('recovery/verify-code/', views.VerifySmsCodeView.as_view()),
    path('recovery/reset/',     views.ResetPasswordView.as_view()),
    path('reset-password/',     views.ResetPasswordView.as_view()),
    path('refresh/',            views.RefreshTokenView.as_view()),
    path('fcm-token/',          views.SaveFcmTokenView.as_view()),
    path('email/send-code/',    views.SendEmailCodeView.as_view()),
    path('email/verify/',       views.VerifyEmailCodeView.as_view()),
    path('ask-question/',       views.AskQuestionView.as_view()),
    path('delete-account/',     views.DeleteAccountView.as_view()),
    path('recovery/send-email-code/', views.SendEmailRecoveryCodeView.as_view()),
]