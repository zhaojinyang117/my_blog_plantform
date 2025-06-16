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

class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户个人资料序列化器
    """
    class Meta:
        model = User
        fields = ["username", "email", "bio", "avatar"]
        read_only_fields = ["email"]

    def validate_avatar(self, value):
        """
        验证头像文件
        """
        # 限制文件大小
        if value.size > 1024 * 1024 * 2:
            raise serializers.ValidationError("头像文件太大了，不能超过2MB")
        
        # 检查文件类型
        allowed_extensions = ["image/jpeg", "image/png", "image/gif"]
        if value.content_type not in allowed_extensions:
            raise serializers.ValidationError("只支持JPEG、PNG、GIF格式")
        return value
    ####################
    #待添加自动裁剪头像功能#
    ####################

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
