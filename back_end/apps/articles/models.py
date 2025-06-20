from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from guardian.models import UserObjectPermissionAbstract, GroupObjectPermissionAbstract

User = get_user_model()


class Article(models.Model):
    """
    文章模型
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("草稿")
        PUBLISHED = "published", _("已发布")

    title = models.CharField(_("标题"), max_length=255)
    content = models.TextField(_("内容"))
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles",
        verbose_name=_("作者"),
    )  # 级联删除
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)  # 记录创建时间
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)  # 记录最后修改时间
    status = models.CharField(
        _("状态"), max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    
    # 阶段9：文章访问统计字段
    view_count = models.PositiveIntegerField(
        _("访问次数"),
        default=0,
        help_text=_("文章被访问的次数")
    )

    class Meta:
        verbose_name = _("文章")
        verbose_name_plural = _("文章")
        ordering = ["-created_at"]
        # 自定义权限
        permissions = [
            ('edit_article', _('可以编辑文章')),
            ('publish_article', _('可以发布文章')),
            ('view_draft_article', _('可以查看草稿文章')),
            ('manage_article', _('可以管理文章')),
        ]
        # 搜索优化：添加数据库索引
        indexes = [
            models.Index(fields=['-created_at']),  # 按创建时间排序的索引
            models.Index(fields=['status', '-created_at']),  # 状态+时间组合索引
            models.Index(fields=['author', 'status']),  # 作者+状态组合索引
            models.Index(fields=['-view_count']),  # 按访问量排序的索引
            models.Index(fields=['title']),  # 标题搜索索引
        ]

    def __str__(self):
        return str(self.title)


class ArticleUserObjectPermission(UserObjectPermissionAbstract):
    """
    文章用户对象权限模型

    用于存储用户对特定文章的权限
    """
    content_object = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        verbose_name=_("文章")
    )

    class Meta:
        verbose_name = _("文章用户权限")
        verbose_name_plural = _("文章用户权限")


class ArticleGroupObjectPermission(GroupObjectPermissionAbstract):
    """
    文章组对象权限模型

    用于存储用户组对特定文章的权限
    """
    content_object = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        verbose_name=_("文章")
    )

    class Meta:
        verbose_name = _("文章组权限")
        verbose_name_plural = _("文章组权限")
