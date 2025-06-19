from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_users_with_perms
from .models import Comment, CommentUserObjectPermission, CommentGroupObjectPermission
from utils.permission_manager import CommentPermissionManager


class CommentTypeFilter(admin.SimpleListFilter):
    """自定义过滤器：区分主评论和回复"""
    title = '评论类型'
    parameter_name = 'comment_type'

    def lookups(self, request, model_admin):
        return (
            ('main', '主评论'),
            ('reply', '回复'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'main':
            return queryset.filter(parent__isnull=True)
        if self.value() == 'reply':
            return queryset.filter(parent__isnull=False)
        return queryset


@admin.register(Comment)
class CommentAdmin(GuardedModelAdmin):
    """
    评论管理
    集成Guardian对象级权限控制
    """

    # 列表显示字段
    list_display = (
        'id',
        'get_content_preview',
        'get_author_link',
        'get_article_link',
        'get_parent_info',
        'created_at',
        'get_replies_count',
        'permission_info'
    )

    # 列表过滤器
    list_filter = (
        'created_at',
        'article__status',
        CommentTypeFilter,  # 区分主评论和回复
    )

    # 搜索字段
    search_fields = (
        'content',
        'user__username',
        'user__email',
        'article__title',
    )

    # 排序
    ordering = ('-created_at',)

    # 每页显示数量
    list_per_page = 20

    # 详情页字段分组
    fieldsets = (
        ('基本信息', {
            'fields': ('article', 'user', 'content')
        }),
        ('关联信息', {
            'fields': ('parent',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # 只读字段
    readonly_fields = ('created_at',)

    # 原始ID字段（用于大数据量时的性能优化）
    raw_id_fields = ('user', 'article', 'parent')

    # 日期层次结构
    date_hierarchy = 'created_at'

    # 自定义方法：内容预览
    def get_content_preview(self, obj):
        """显示评论内容预览"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    get_content_preview.short_description = '评论内容'
    get_content_preview.admin_order_field = 'content'

    # 自定义方法：作者链接
    def get_author_link(self, obj):
        """显示作者链接"""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    get_author_link.short_description = '作者'
    get_author_link.admin_order_field = 'user__username'

    # 自定义方法：文章链接
    def get_article_link(self, obj):
        """显示文章链接"""
        url = reverse('admin:articles_article_change', args=[obj.article.id])
        return format_html('<a href="{}">{}</a>', url, obj.article.title)
    get_article_link.short_description = '关联文章'
    get_article_link.admin_order_field = 'article__title'

    # 自定义方法：父评论信息
    def get_parent_info(self, obj):
        """显示父评论信息"""
        if obj.parent:
            url = reverse('admin:comments_comment_change', args=[obj.parent.id])
            return format_html(
                '<a href="{}">回复: {}</a>',
                url,
                obj.parent.user.username
            )
        return '主评论'
    get_parent_info.short_description = '评论类型'
    get_parent_info.admin_order_field = 'parent'

    # 自定义方法：回复数量
    def get_replies_count(self, obj):
        """显示回复数量"""
        count = obj.replies.count()
        if count > 0:
            return format_html('<span style="color: green;">{} 条回复</span>', count)
        return '无回复'
    get_replies_count.short_description = '回复数量'

    # Guardian相关配置
    obj_perms_manage_template = "admin/comments/comment/obj_perms_manage.html"

    # 批量操作
    actions = ['delete_selected_comments', 'mark_as_spam', 'assign_moderator_permissions']

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

    def delete_selected_comments(self, request, queryset):
        """批量删除评论"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'成功删除 {count} 条评论。')
    delete_selected_comments.short_description = '删除选中的评论'

    def mark_as_spam(self, request, queryset):
        """标记为垃圾评论（这里可以扩展为添加spam字段）"""
        # 这里暂时只是删除，实际项目中可以添加spam字段
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'成功标记并删除 {count} 条垃圾评论。')
    mark_as_spam.short_description = '标记为垃圾评论并删除'

    def assign_moderator_permissions(self, request, queryset):
        """
        为选中评论分配审核权限
        """
        count = 0
        for comment in queryset:
            # 为评论作者分配审核权限
            if CommentPermissionManager.assign_moderator_permissions(comment.user, comment):
                count += 1

        self.message_user(request, f"成功为 {count} 条评论分配审核权限")

    assign_moderator_permissions.short_description = "为选中评论分配审核权限"

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
        return CommentPermissionManager.can_edit_comment(request.user, obj)

    def has_delete_permission(self, request, obj=None):
        """
        检查删除权限
        """
        if obj is None:
            return super().has_delete_permission(request)

        # 超级用户有所有权限
        if request.user.is_superuser:
            return True

        # 评论作者可以删除自己的评论
        if obj.user == request.user:
            return True

        # 检查Guardian管理权限
        return request.user.has_perm('comments.manage_comment', obj)

    def save_model(self, request, obj, form, change):
        """
        保存模型时分配权限
        """
        is_new = not change
        super().save_model(request, obj, form, change)

        # 为新评论的作者分配权限
        if is_new:
            CommentPermissionManager.assign_author_permissions(obj.user, obj)


@admin.register(CommentUserObjectPermission)
class CommentUserObjectPermissionAdmin(admin.ModelAdmin):
    """
    评论用户权限管理界面
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


@admin.register(CommentGroupObjectPermission)
class CommentGroupObjectPermissionAdmin(admin.ModelAdmin):
    """
    评论组权限管理界面
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

    # 自定义查询集优化
    def get_queryset(self, request):
        """优化查询性能"""
        return super().get_queryset(request).select_related(
            'user', 'article', 'parent', 'parent__user'
        ).prefetch_related('replies')
