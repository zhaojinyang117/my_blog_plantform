from rest_framework import serializers
from .models import Comment
from apps.articles.serializers import AuthorSerializer
from utils.text_filter import filter_comment_content

class ReplySerializer(serializers.ModelSerializer):
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
    replies = ReplySerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "article",  # 文章id
            "content",
            "created_at",
            "status",  # 审核状态
            "status_display",  # 状态显示名称
            "parent", # 父评论的id
            "replies", # 子评论列表
        ]

        read_only_fields = [
            "id",
            "user",
            "article",
            "created_at",
            "status",  # 状态由系统自动设置
        ] # 除了content和parent外都是只读
    
    def validate_content(self, value):
        """
        验证评论内容，集成敏感词过滤
        """
        if not value or not value.strip():
            raise serializers.ValidationError("评论内容不能为空")
        
        # 使用敏感词过滤器检查内容
        filter_result = filter_comment_content(value)
        
        # 如果内容无效，抛出验证错误
        if not filter_result['is_valid']:
            raise serializers.ValidationError(filter_result['issues'])
        
        # 存储过滤结果供后续使用
        self.context['filter_result'] = filter_result
        
        # 返回过滤后的内容
        return filter_result['filtered_content']
    
    def create(self, validated_data):
        """
        创建评论时根据过滤结果设置审核状态
        """
        # 获取过滤结果
        filter_result = self.context.get('filter_result', {'should_auto_approve': True})
        
        # 根据过滤结果设置状态
        if filter_result['should_auto_approve']:
            validated_data['status'] = 'approved'
        else:
            validated_data['status'] = 'pending'
        
        return super().create(validated_data)
