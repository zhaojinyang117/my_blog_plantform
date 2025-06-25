from django.db import models
from apps.articles.models import Article
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from guardian.models import UserObjectPermissionAbstract, GroupObjectPermissionAbstract

User = get_user_model()

class Comment(models.Model):
    """
    评论模型
    需要关联文章, 需要关联用户
    """
    
    # 审核状态选择
    APPROVAL_STATUS_CHOICES = [
        ('pending', _('待审核')),
        ('approved', _('已通过')),
        ('rejected', _('已拒绝')),
    ]
    # 关联文章 当文章被删除时，相关的评论也会被级联删除
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("文章")
    )
    # 关联用户 当用户被删除时，相关的评论也会被级联删除(这个其实可以存疑, 因为用户更多是封号,移除激活状态, 而不是真的删除)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("用户")
    )
    
    content = models.TextField(_("内容")) # 第一个位置参数就是 verbose_name
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    
    # 审核状态字段
    status = models.CharField(
        _("审核状态"),
        max_length=10,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name='replies', # 通过 parent_comment.replies.all() 获取所有回复
        null=True,
        blank=True,
        verbose_name=_("父评论")
    )

    class Meta:
        verbose_name = _("评论")
        verbose_name_plural = _("评论")
        ordering = ['parent_id', 'created_at'] # 先按父评论分组，再按创建时间排序
        # 自定义权限
        permissions = [
            # ('edit_comment', _('可以编辑评论')),  # 评论不允许编辑
            ('moderate_comment', _('可以审核评论')),
            ('reply_comment', _('可以回复评论')),
            ('manage_comment', _('可以管理评论')),
        ]

    def __str__(self):
        if self.parent:
            return f"回复给:{self.parent.user.username}: {self.content[:50]}{'...' if len(self.content) > 50 else ''}"
        # 显示作者用户名和评论内容的前50个字符。
        return f"{self.user.username}: {self.content[:50]}{'...' if len(self.content) > 50 else ''}"


class CommentUserObjectPermission(UserObjectPermissionAbstract):
    """
    评论用户对象权限模型

    用于存储用户对特定评论的权限
    """
    content_object = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        verbose_name=_("评论")
    )

    class Meta:
        verbose_name = _("评论用户权限")
        verbose_name_plural = _("评论用户权限")


class CommentGroupObjectPermission(GroupObjectPermissionAbstract):
    """
    评论组对象权限模型

    用于存储用户组对特定评论的权限
    """
    content_object = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        verbose_name=_("评论")
    )

    class Meta:
        verbose_name = _("评论组权限")
        verbose_name_plural = _("评论组权限")