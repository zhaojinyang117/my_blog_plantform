from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

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

    class Meta:
        verbose_name = _("文章")
        verbose_name_plural = _("文章")
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.title)
