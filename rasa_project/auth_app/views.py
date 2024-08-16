from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework import response,status
from . import serializers, models
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt
from .utils import Util
from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .models import CustomUser
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserTokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .serializers import SignUpSerializer

@swagger_auto_schema(
    operation_description="Update user details",
    request_body=SignUpSerializer,
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="User details updated successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Operation success status"),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description="Success message"),
                    'data': SignUpSerializer
                }
            )
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad request"),
        status.HTTP_401_UNAUTHORIZED: openapi.Response(description="Authentication credentials were not provided")
    }
)

# Endpoint for updating user details
class UpdateUserDetails(generics.UpdateAPIView):
    serializer_class = SignUpSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response({
            "success": True,
            "message": "User details updated successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


# Endpoint for user login
class UserTokenObtainPairView(TokenObtainPairView):
    serializer_class = UserTokenObtainPairSerializer
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            # Customize the success response here if needed
            custom_data = {'message': 'Login successful',
                           'success': True}
            custom_data.update(response.data)
            return Response(custom_data, status=status.HTTP_200_OK)
        except Exception as e:
            return self.handle_exception(e)
        
# Endpoint for user signup
class SignUp(GenericAPIView):
    serializer_class = serializers.SignUpSerializer
    def post(self, request):
        data = request.data
        email = data.get('email')
        user_exists = CustomUser.objects.filter(email=email).exists()

        if not user_exists:
            serializer = self.serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = self.serializer_class(CustomUser.objects.get(email=email))

        user = serializer.data
        user_email = CustomUser.objects.get(email=user['email'])
        tokens = RefreshToken.for_user(user_email).access_token

        self.send_verification_email(request, user, tokens)

        if not user_exists:
            return response.Response({'success':True,'user_data': user, 'access_token': str(tokens)}, status=status.HTTP_201_CREATED)
        else:
            return response.Response({'success':False,'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

    def send_verification_email(self, request, user, tokens):
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')
        absurl = f'http://{current_site}{relative_link}?token={str(tokens)}'
        email_body = f'Hi {user["username"]}, Use the link below to verify your email \n{absurl}'
        data = {
            'email_body': email_body,
            'to_email': user['email'],
            'email_subject': 'Verify your email'
        }
        Util.send_email(data=data)

# Endpoint for email verification
class VerifyEmail(GenericAPIView ):
    serializer_class = serializers.EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            print(payload)
            user = CustomUser.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return response.Response({'success':True,'email':
                                       'Successfully activated'}, status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError as identifier:
            return response.Response({'success':False,
                                      'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return response.Response({'success':False,
                                      'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        

class PasswordRequestChange(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PasswordRequestChangeSerializer
    
    def post(self, request):
        data = request.data
        email = data.get('email')
        user_exists = CustomUser.objects.filter(email=email).exists()

        if user_exists:
            user = CustomUser.objects.get(email=email)
            tokens = RefreshToken.for_user(user).access_token
            self.send_password_reset_email(request, user, tokens)
            return response.Response({'success':True,'message': 'Password reset link sent to your email', 'access_token': str(tokens)}, status=status.HTTP_200_OK)
        else:
            return response.Response({'success':False,'error': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

    def send_password_reset_email(self, request, user, tokens):
        current_site = get_current_site(request).domain
        relative_link = reverse('password-reset')
        absurl = f'http://{current_site}{relative_link}?token={str(tokens)}'
        email_body = f'Hi {user.username}, Use the link below to reset your password \n{absurl}'
        data = {
            'email_body': email_body,
            'to_email': user.email,
            'email_subject': 'Reset your password'
        }
        Util.send_email(data=data)