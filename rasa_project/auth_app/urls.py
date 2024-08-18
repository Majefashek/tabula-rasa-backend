from django.urls import path
from . import views

urlpatterns = [
    
    path('login/', views.UserTokenObtainPairView.as_view(), name='login'),
    path('signup/',views.SignUp.as_view(), name='register'),
    path('email-verify/', views.VerifyEmail.as_view(), name="email-verify"),  
    path('update-user/', views.UpdateUserDetails.as_view(), name='update'),
    path('request-password-change/', views.PasswordRequestChange.as_view(), name='password-change'),
    path('reset-password/', views.PasswordReset.as_view(),name='password-reset')
]
