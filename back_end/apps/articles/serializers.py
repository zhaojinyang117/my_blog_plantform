from rest_framework import serializers
from .models import Article
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """作者序列化器"""

    class Meta:
        model = User
        fields = ["id", "username", "email", "avatar"]


class ArticleSerializer(serializers.ModelSerializer):
    """文章序列化器"""

    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "created_at",
            "updated_at",
            "status",
            "view_count",  # 阶段9：添加访问统计字段
        ]
        read_only_fields = ["id", "created_at", "author", "view_count"]


class ArticleCreateUpdateSerializer(serializers.ModelSerializer):
    """创建和更新文章序列化器"""

    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "status",
            "author",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]
