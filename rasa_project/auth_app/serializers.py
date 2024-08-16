from rest_framework import serializers
from .models import CustomUser
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



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