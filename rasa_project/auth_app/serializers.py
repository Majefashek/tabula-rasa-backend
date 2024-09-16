from rest_framework import serializers
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import ValidationError
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'phonenumber']



class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get("email", "")
        password = attrs.get("password", "")
        
        # Fetch the user
        user = CustomUser.objects.filter(email=email).first()
        
        # Check if user exists
        if user is None:
            raise ValidationError({"email": "No user found with this email."})
        
        # Validate the password
        if not user.check_password(password):
            raise ValidationError({"password": "Invalid password."})

        # Check if the user account is verified
        if not user.is_verified:
            raise ValidationError({"account": "Please activate your account."})

        # If everything is valid, generate tokens using the parent class logic
        data = super().validate(attrs)
        return data






class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only =True  )
    # tokens = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name',
                  'username', 'email', 'password','tokens']
        read_only_fields= ['id',]

    def create(self, validated_data):
        # Extract the password from the validated data
        password = validated_data.pop('password', None)
        # Create a new user instance with the remaining validated data
        user = CustomUser.objects.create(**validated_data)
        # Set the password for the user
        if password:
            user.set_password(password)
            user.save()
        return user






class EmailVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=555)
    class Meta:
        model = CustomUser
        fields = ['token']


class PasswordResetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def update(self, instance, validated_data):
        # Extract the password from the validated data
        password = validated_data.get('password', None)
        # Set the password for the user
        if password:
            instance.set_password(password)
            instance.save()
        return instance
    
class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username','phonenumber']
        extra_kwargs = {
            'email': {'required': False},
        }

    def update(self, instance, validated_data):
    # List of fields to update
        fields_to_update = ['first_name', 'last_name', 'username', 'phonenumber']
        
        for field in fields_to_update:
            value = validated_data.get(field)
            if value:
                setattr(instance, field, value)  # Update the instance attribute

        instance.save()
        return instance


