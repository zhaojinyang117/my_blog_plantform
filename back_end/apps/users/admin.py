from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    自定义用户管理界面
    """

    # 列表页显示的字段
    list_display = (
        "email",
        "username",
        "is_active",
        "is_staff",
        "date_joined",
        "last_login",
    )

    # 列表页过滤器
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined", "last_login")

    # 搜索字段
    search_fields = ("email", "username")

    # 排序字段
    ordering = ("-date_joined",)

    # 批量操作
    actions = ["activate_users", "deactivate_users", "clear_verification_tokens"]

    # 详情页字段分组
    fieldsets = (
        (_("基本信息"), {"fields": ("username", "email", "password")}),
        (_("个人信息"), {"fields": ("bio", "avatar")}),
        (
            _("权限"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("重要日期"), {"fields": ("last_login", "date_joined")}),
        (
            _("邮箱验证"),
            {
                "fields": ("email_verification_token",),
                "classes": ("collapse",),  # 默认折叠
            },
        ),
    )

    # 添加用户页面字段
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "is_active"),
            },
        ),
    )

    def activate_users(self, request, queryset):
        """
        批量激活用户
        """
        updated = queryset.update(is_active=True)
        self.message_user(request, f"成功激活 {updated} 个用户账户。")

    activate_users.short_description = "激活选定用户"

    def deactivate_users(self, request, queryset):
        """
        批量禁用用户
        """
        updated = queryset.update(is_active=False)
        self.message_user(request, f"成功禁用 {updated} 个用户账户。")

    deactivate_users.short_description = "禁用选定用户"

    def clear_verification_tokens(self, request, queryset):
        """
        清空验证令牌
        """
        updated = queryset.update(email_verification_token="")
        self.message_user(request, f"成功清空 {updated} 个用户的验证令牌。")

    clear_verification_tokens.short_description = "清空验证令牌"

    # 只读字段
    readonly_fields = ("date_joined", "last_login")
