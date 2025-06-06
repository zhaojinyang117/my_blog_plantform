from rest_framework import serializers
from .models import Comment
from apps.articles.serializers import AuthorSerializer

class RepalySerializer(serializers.ModelSerializer):
    """用于嵌套回复的序列化器"""
    user = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "article",  # 文章id
            "content",
            "created_at",
            "parent", # 父评论的id
        ]
        read_only_fields = [
            "id", 
            "user", 
            "article", 
            "created_at",
            "parent",
        ]


class CommentSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)
    replies:list = RepalySerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "article",  # 文章id
            "content",
            "created_at",
            "parent", # 父评论的id
            "replies", # 子评论列表
        ]

        read_only_fields = [
            "id", 
            "user", 
            "article", 
            "created_at",
        ] # 除了content和parent外都是只读
