from django.db import models
from apps.articles.models import Article
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Comment(models.Model):
    """
    评论模型
    需要关联文章, 需要关联用户
    """
    # 关联文章 当文章被删除时，相关的评论也会被级联删除
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("文章")
    )
    # 关联用户 当用户被删除时，相关的评论也会被级联删除
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("用户")
    )
    
    content = models.TextField(_("内容")) # 第一个位置参数就是 verbose_name
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _("评论")
        verbose_name_plural = _("评论")
        ordering = ["-created_at"]

    def __str__(self):
        # 显示作者用户名和评论内容的前50个字符。
        return f"{self.user.username}: {self.content[:50]}{'...' if len(self.content) > 50 else ''}"