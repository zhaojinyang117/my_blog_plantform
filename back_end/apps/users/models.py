from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _ # django中关于i18n的一个库,用于标记需要翻译的字符串，但它会延迟翻译，直到字符串被实际使用时才进行。

class User(AbstractUser):
    """
    用户模型
    """
    email = models.EmailField(_("邮箱"), unique=True)
    bio = models.TextField(_("个人简介"), max_length=500, blank=True)
    avatar = models.ImageField(_("头像"), upload_to="avatar/%Y/%m", blank=True)

    # 使用邮箱作为用户名
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = _("用户")
        verbose_name_plural = _("用户")

    def __str__(self):
        return self.email


