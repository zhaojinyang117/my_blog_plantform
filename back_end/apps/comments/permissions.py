from rest_framework import permissions

class IsCommentUserOrReadOnly(permissions.BasePermission):
    """
    自定义权限，只允许评论的作者编辑或删除它。
    对于其他请求方法（如GET, HEAD, OPTIONS），总是允许。
    """
    # 读取权限对任何请求都是允许的，
    # 所以我们总是允许 GET, HEAD 或 OPTIONS 请求。
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # 只有发评论的那个人才有权修改或删除评论
        return obj.user == request.user