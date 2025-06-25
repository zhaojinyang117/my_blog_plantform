from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_users_with_perms
from .models import Article, ArticleUserObjectPermission, ArticleGroupObjectPermission
from utils.permission_manager import ArticlePermissionManager

User = get_user_model()

@admin.register(Article)
class ArticleAdmin(GuardedModelAdmin):
    """
    文章管理界面
    集成Guardian对象级权限控制
    """
    list_display = ("title", "author", "status", "created_at", "updated_at", "permission_info")
    list_filter = ("status", "created_at", "updated_at", "author")
    search_fields = ("title", "content", "author__username", "author__email")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    # Guardian相关配置
    obj_perms_manage_template = "admin/articles/article/obj_perms_manage.html"

    # 字段分组
    fieldsets = (
        ("基本信息", {
            "fields": ("title", "content", "author", "status")
        }),
        ("时间信息", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    readonly_fields = ("created_at", "updated_at")

    # 批量操作
    actions = ["make_published", "make_draft", "assign_editor_permissions"]

    def permission_info(self, obj):
        """
        显示权限信息
        """
        users_with_perms = get_users_with_perms(obj, attach_perms=True)
        if users_with_perms:
            info = []
            for user, perms in users_with_perms.items():
                perm_list = ", ".join(perms)
                info.append(f"{user.username}: {perm_list}")
            return format_html("<br>".join(info))
        return "无特殊权限"

    permission_info.short_description = "权限信息"

    def make_published(self, request, queryset):
        """
        批量发布文章
        """
        updated = queryset.update(status=Article.Status.PUBLISHED)
        self.message_user(request, f"成功发布 {updated} 篇文章")

    make_published.short_description = "发布选中的文章"

    def make_draft(self, request, queryset):
        """
        批量设为草稿
        """
        updated = queryset.update(status=Article.Status.DRAFT)
        self.message_user(request, f"成功将 {updated} 篇文章设为草稿")

    make_draft.short_description = "将选中的文章设为草稿"

    def assign_editor_permissions(self, request, queryset):
        """
        为选中文章分配编辑权限
        """
        # 这里可以实现批量权限分配逻辑
        count = 0
        for article in queryset:
            # 示例：为文章作者分配编辑权限
            if ArticlePermissionManager.assign_editor_permissions(article.author, article):
                count += 1

        self.message_user(request, f"成功为 {count} 篇文章分配编辑权限")

    assign_editor_permissions.short_description = "为选中文章分配编辑权限"

    def get_queryset(self, request):
        """
        根据用户权限过滤查询集
        """
        qs = super().get_queryset(request)

        # 超级用户可以看到所有文章
        if request.user.is_superuser:
            return qs

        # 管理员可以看到所有文章
        if request.user.is_staff:
            return qs

        # 普通用户只能看到自己的文章
        return qs.filter(author=request.user)

    def has_change_permission(self, request, obj=None):
        """
        检查修改权限
        """
        if obj is None:
            return super().has_change_permission(request)

        # 超级用户有所有权限
        if request.user.is_superuser:
            return True

        # 检查Guardian对象权限
        return ArticlePermissionManager.can_edit_article(request.user, obj)

    def has_delete_permission(self, request, obj=None):
        """
        检查删除权限
        """
        if obj is None:
            return super().has_delete_permission(request)

        # 超级用户有所有权限
        if request.user.is_superuser:
            return True

        # 文章作者可以删除自己的文章
        if obj.author == request.user:
            return True

        # 检查Guardian管理权限
        return request.user.has_perm('articles.manage_article', obj)

    def save_model(self, request, obj, form, change):
        """
        保存模型时分配权限
        """
        is_new = not change
        super().save_model(request, obj, form, change)

        # 为新文章的作者分配权限
        if is_new:
            ArticlePermissionManager.assign_author_permissions(obj.author, obj)


@admin.register(ArticleUserObjectPermission)
class ArticleUserObjectPermissionAdmin(admin.ModelAdmin):
    """
    文章用户权限管理界面
    """
    list_display = ("user", "permission", "content_object")
    list_filter = ("permission",)
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user", "content_object")

    def get_queryset(self, request):
        """
        优化查询性能
        """
        return super().get_queryset(request).select_related("user", "content_object", "permission")


@admin.register(ArticleGroupObjectPermission)
class ArticleGroupObjectPermissionAdmin(admin.ModelAdmin):
    """
    文章组权限管理界面
    """
    list_display = ("group", "permission", "content_object")
    list_filter = ("permission",)
    search_fields = ("group__name",)
    raw_id_fields = ("group", "content_object")

    def get_queryset(self, request):
        """
        优化查询性能
        """
        return super().get_queryset(request).select_related("group", "content_object", "permission")
