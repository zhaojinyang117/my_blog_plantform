from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import (
    gettext_lazy as _,
)  # django中关于i18n的一个库,用于标记需要翻译的字符串，但它会延迟翻译，直到字符串被实际使用时才进行。
import uuid
import os
from urllib.parse import quote


def user_avatar_upload_path(instance, filename):
    """
    自定义头像上传路径函数
    解决中文文件名编码问题
    """
    ###################################################################################################
    #[18/Jun/2025 22:19:52] "PATCH /api/users/me/avatar/ HTTP/1.1" 200 113                            #
    #Not Found: /media/avatar/2025/06/捕获.PNG                                                        #
    #[18/Jun/2025 22:19:53] "GET /media/avatar/2025/06/%E6%8D%95%E8%8E%B7.PNG HTTP/1.1" 404 2589      #
    #[18/Jun/2025 22:20:10] "GET /api/users/me/ HTTP/1.1" 200 149                                    #
    #Not Found: /media/avatar/2025/06/捕获.PNG                                                        #
    #[18/Jun/2025 22:20:11] "GET /media/avatar/2025/06/%E6%8D%95%E8%8E%B7.PNG HTTP/1.1" 404 2589      #
    ###################################################################################################
    # 获取文件扩展名
    ext = filename.split('.')[-1].lower()

    # 生成唯一的文件名，避免中文字符问题
    unique_filename = f"user_{instance.id}_avatar_{uuid.uuid4().hex[:8]}.{ext}"

    # 返回上传路径
    return f"avatars/{instance.id}/{unique_filename}"


class UserManager(BaseUserManager):
    """
    自定义用户管理器
    """
    def create_user(self, email, username, password=None, **extra_fields):
        """
        创建普通用户
        """
        if not email:
            raise ValueError('必须提供邮箱地址')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        """
        创建超级用户
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # 确保超级用户是激活状态

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """
    用户模型
    """

    email = models.EmailField(_("邮箱"), unique=True)
    bio = models.TextField(_("个人简介"), max_length=500, blank=True)
    avatar = models.ImageField(_("头像"), upload_to=user_avatar_upload_path, blank=True)

    # 使用邮箱作为用户名
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    # 邮箱验证
    is_active = models.BooleanField(_("用户激活状态"), default=False)
    email_verification_token = models.CharField(
        _("邮箱验证token"),
        max_length=64,
        blank=True,
        help_text=_("用于邮箱验证的token"),
    )

    # 使用自定义用户管理器
    objects = UserManager()  # type: ignore

    class Meta:
        verbose_name = _("用户")
        verbose_name_plural = _("用户")

    def __str__(self):
        return self.email
