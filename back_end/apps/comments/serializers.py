from rest_framework import serializers
from .models import Comment
from apps.articles.serializers import AuthorSerializer


class CommentSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "article",  # 文章id
            "content",
            "created_at",
        ]

        read_only_fields = [
            "id", 
            "user", 
            "article", 
            "created_at"
        ] # 除了content 外都是只读
