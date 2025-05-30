from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    用户管理类
    """

    # list_display: 在Django管理后台的用户列表页面中显示的字段
    # 这里显示用户名、邮箱、是否为管理员、是否激活状态
    list_display = ("username", "email", "is_staff", "is_active")

    # search_fields: 在管理后台提供搜索功能的字段
    # 用户可以通过邮箱或用户名来搜索用户
    search_fields = ("email", "username")

    # ordering: 设置用户列表的默认排序方式
    # 这里按邮箱字母顺序排序
    ordering = ("email",)
