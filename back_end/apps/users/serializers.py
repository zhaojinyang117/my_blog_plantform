from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "bio", "avatar"]
        read_only_fields = ["id", "email"]


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    """

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2"]

    def validate(self, attrs: dict):
        """
        验证俩密码是否一致
        """
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "两次密码不一致"})
        return attrs

    def create(self, validated_data: dict):
        """
        创建用户
        """
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user
