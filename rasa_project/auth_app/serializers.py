from rest_framework import serializers
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'username', 'phonenumber']




class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        data = super().validate(attrs)
        email = attrs.get("email", "")
        password = attrs.get("password", "")

        # Validate student credentials
        user = CustomUser.objects.filter(email=email,is_verified=True).first()
        if user and user.check_password(password):
            return data
        else:
            raise serializers.ValidationError("Invalid credentials")







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
        fields = ['first_name', 'last_name', 'username']
        extra_kwargs = {
            'email': {'required': False},
        }

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.save()
        return instance


