from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    自定义权限，允许所有用户读取, 但只允许作者修改自己的文章
    """

    def has_object_permission(self, request, view, obj):
        # 读取权限允许所有用户
        if request.method in permissions.SAFE_METHODS:
            return True
        # 只有作者才有权修改
        # if request.method in ['PUT', 'DELETE'] and obj.author == request.user:
        #     return True
        # return False

        return obj.author == request.user
