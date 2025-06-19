"""
权限管理工具类模块

提供权限分配、检查、撤销等常用功能的封装，简化Guardian权限管理操作
"""

from typing import List, Optional, Union
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import assign_perm, remove_perm, get_perms, get_users_with_perms, get_groups_with_perms
from guardian.models import UserObjectPermission, GroupObjectPermission
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class PermissionManager:
    """
    权限管理工具类
    
    提供统一的权限管理接口，封装Guardian的常用操作
    """
    
    @staticmethod
    def assign_user_permission(user: User, permission: str, obj: object) -> bool:
        """
        为用户分配对象权限
        
        Args:
            user: 用户对象
            permission: 权限名称（如 'edit_article'）
            obj: 目标对象
            
        Returns:
            bool: 是否分配成功
        """
        try:
            assign_perm(permission, user, obj)
            logger.info(f"为用户 {user.email} 分配权限 {permission} 到对象 {obj}")
            return True
        except Exception as e:
            logger.error(f"分配权限失败: {e}")
            return False
    
    @staticmethod
    def assign_group_permission(group: Group, permission: str, obj: object) -> bool:
        """
        为用户组分配对象权限
        
        Args:
            group: 用户组对象
            permission: 权限名称
            obj: 目标对象
            
        Returns:
            bool: 是否分配成功
        """
        try:
            assign_perm(permission, group, obj)
            logger.info(f"为用户组 {group.name} 分配权限 {permission} 到对象 {obj}")
            return True
        except Exception as e:
            logger.error(f"分配组权限失败: {e}")
            return False
    
    @staticmethod
    def remove_user_permission(user: User, permission: str, obj: object) -> bool:
        """
        撤销用户的对象权限
        
        Args:
            user: 用户对象
            permission: 权限名称
            obj: 目标对象
            
        Returns:
            bool: 是否撤销成功
        """
        try:
            remove_perm(permission, user, obj)
            logger.info(f"撤销用户 {user.email} 的权限 {permission} 从对象 {obj}")
            return True
        except Exception as e:
            logger.error(f"撤销权限失败: {e}")
            return False
    
    @staticmethod
    def remove_group_permission(group: Group, permission: str, obj: object) -> bool:
        """
        撤销用户组的对象权限
        
        Args:
            group: 用户组对象
            permission: 权限名称
            obj: 目标对象
            
        Returns:
            bool: 是否撤销成功
        """
        try:
            remove_perm(permission, group, obj)
            logger.info(f"撤销用户组 {group.name} 的权限 {permission} 从对象 {obj}")
            return True
        except Exception as e:
            logger.error(f"撤销组权限失败: {e}")
            return False
    
    @staticmethod
    def check_user_permission(user: User, permission: str, obj: object) -> bool:
        """
        检查用户是否有特定对象的权限
        
        Args:
            user: 用户对象
            permission: 权限名称
            obj: 目标对象
            
        Returns:
            bool: 是否有权限
        """
        if not user.is_authenticated:
            return False
        
        # 管理员有所有权限
        if hasattr(user, 'is_staff') and user.is_staff:
            return True
        
        # 检查Guardian对象权限
        return user.has_perm(permission, obj)
    
    @staticmethod
    def get_user_permissions(user: User, obj: object) -> List[str]:
        """
        获取用户对特定对象的所有权限
        
        Args:
            user: 用户对象
            obj: 目标对象
            
        Returns:
            List[str]: 权限列表
        """
        if not user.is_authenticated:
            return []
        
        return get_perms(user, obj)
    
    @staticmethod
    def get_users_with_permission(permission: str, obj: object) -> List[User]:
        """
        获取拥有特定对象权限的所有用户
        
        Args:
            permission: 权限名称
            obj: 目标对象
            
        Returns:
            List[User]: 用户列表
        """
        users_with_perms = get_users_with_perms(obj, only_with_perms_in=[permission])
        return list(users_with_perms)
    
    @staticmethod
    def get_groups_with_permission(permission: str, obj: object) -> List[Group]:
        """
        获取拥有特定对象权限的所有用户组
        
        Args:
            permission: 权限名称
            obj: 目标对象
            
        Returns:
            List[Group]: 用户组列表
        """
        groups_with_perms = get_groups_with_perms(obj, only_with_perms_in=[permission])
        return list(groups_with_perms)
    
    @staticmethod
    def bulk_assign_permissions(user: User, permissions: List[str], obj: object) -> bool:
        """
        批量为用户分配权限
        
        Args:
            user: 用户对象
            permissions: 权限名称列表
            obj: 目标对象
            
        Returns:
            bool: 是否全部分配成功
        """
        success_count = 0
        for permission in permissions:
            if PermissionManager.assign_user_permission(user, permission, obj):
                success_count += 1
        
        return success_count == len(permissions)
    
    @staticmethod
    def bulk_remove_permissions(user: User, permissions: List[str], obj: object) -> bool:
        """
        批量撤销用户权限
        
        Args:
            user: 用户对象
            permissions: 权限名称列表
            obj: 目标对象
            
        Returns:
            bool: 是否全部撤销成功
        """
        success_count = 0
        for permission in permissions:
            if PermissionManager.remove_user_permission(user, permission, obj):
                success_count += 1
        
        return success_count == len(permissions)
    
    @staticmethod
    def transfer_ownership(old_owner: User, new_owner: User, obj: object, permissions: Optional[List[str]] = None) -> bool:
        """
        转移对象所有权
        
        Args:
            old_owner: 原所有者
            new_owner: 新所有者
            obj: 目标对象
            permissions: 要转移的权限列表，如果为None则转移所有权限
            
        Returns:
            bool: 是否转移成功
        """
        try:
            if permissions is None:
                # 获取原所有者的所有权限
                permissions = PermissionManager.get_user_permissions(old_owner, obj)
            
            # 为新所有者分配权限
            success = PermissionManager.bulk_assign_permissions(new_owner, permissions, obj)
            
            if success:
                # 撤销原所有者的权限
                PermissionManager.bulk_remove_permissions(old_owner, permissions, obj)
                logger.info(f"成功转移对象 {obj} 的所有权从 {old_owner.email} 到 {new_owner.email}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"转移所有权失败: {e}")
            return False
    
    @staticmethod
    def cleanup_object_permissions(obj: object) -> bool:
        """
        清理对象的所有权限
        
        Args:
            obj: 目标对象
            
        Returns:
            bool: 是否清理成功
        """
        try:
            content_type = ContentType.objects.get_for_model(obj)
            
            # 删除用户对象权限
            UserObjectPermission.objects.filter(
                content_type=content_type,
                object_pk=obj.pk
            ).delete()
            
            # 删除组对象权限
            GroupObjectPermission.objects.filter(
                content_type=content_type,
                object_pk=obj.pk
            ).delete()
            
            logger.info(f"成功清理对象 {obj} 的所有权限")
            return True
        except Exception as e:
            logger.error(f"清理对象权限失败: {e}")
            return False


class ArticlePermissionManager:
    """
    文章权限管理器

    专门处理文章相关的权限操作
    """

    # 文章权限常量（Guardian权限格式：app_label.permission_codename）
    # 文章编辑权限：允许修改文章内容、标题等
    EDIT_PERMISSION = 'articles.edit_article'
    # 文章发布权限：允许将草稿文章发布为公开状态
    PUBLISH_PERMISSION = 'articles.publish_article'
    # 草稿查看权限：允许查看未发布的草稿文章
    VIEW_DRAFT_PERMISSION = 'articles.view_draft_article'
    # 文章管理权限：允许删除文章、转移所有权等管理操作
    MANAGE_PERMISSION = 'articles.manage_article'

    # 文章的所有权限列表：包含编辑、发布、查看草稿和管理权限
    ALL_PERMISSIONS = [
        EDIT_PERMISSION,
        PUBLISH_PERMISSION,
        VIEW_DRAFT_PERMISSION,
        MANAGE_PERMISSION
    ]

    @classmethod
    def assign_author_permissions(cls, user: User, article: object) -> bool:
        """
        为文章作者分配所有权限

        Args:
            user: 用户对象
            article: 文章对象

        Returns:
            bool: 是否分配成功
        """
        return PermissionManager.bulk_assign_permissions(user, cls.ALL_PERMISSIONS, article)

    @classmethod
    def assign_editor_permissions(cls, user: User, article: object) -> bool:
        """
        为编辑者分配编辑权限

        Args:
            user: 用户对象
            article: 文章对象

        Returns:
            bool: 是否分配成功
        """
        editor_permissions = [cls.EDIT_PERMISSION, cls.VIEW_DRAFT_PERMISSION]
        return PermissionManager.bulk_assign_permissions(user, editor_permissions, article)

    @classmethod
    def can_edit_article(cls, user: User, article: object) -> bool:
        """
        检查用户是否可以编辑文章
        """
        return PermissionManager.check_user_permission(user, cls.EDIT_PERMISSION, article)

    @classmethod
    def can_publish_article(cls, user: User, article: object) -> bool:
        """
        检查用户是否可以发布文章
        """
        return PermissionManager.check_user_permission(user, cls.PUBLISH_PERMISSION, article)


class CommentPermissionManager:
    """
    评论权限管理器

    专门处理评论相关的权限操作
    注意：评论不允许编辑，只能删除后重新创建
    """

    # 评论权限常量（移除编辑权限，Guardian权限格式：app_label.permission_codename）
    # 评论审核权限：允许审核评论状态（通过/拒绝）
    MODERATE_PERMISSION = 'comments.moderate_comment'
    # 评论回复权限：允许回复其他用户的评论
    REPLY_PERMISSION = 'comments.reply_comment'
    # 评论管理权限：允许删除评论等管理操作
    MANAGE_PERMISSION = 'comments.manage_comment'

    # 所有评论权限的集合
    ALL_PERMISSIONS = [
        MODERATE_PERMISSION,  # 审核权限
        REPLY_PERMISSION,     # 回复权限
        MANAGE_PERMISSION     # 管理权限
    ]

    @classmethod
    def assign_author_permissions(cls, user: User, comment: object) -> bool:
        """
        为评论作者分配权限（不包括编辑权限）

        Args:
            user: 用户对象
            comment: 评论对象

        Returns:
            bool: 是否分配成功
        """
        author_permissions = [cls.REPLY_PERMISSION, cls.MANAGE_PERMISSION]
        return PermissionManager.bulk_assign_permissions(user, author_permissions, comment)

    @classmethod
    def assign_moderator_permissions(cls, user: User, comment: object) -> bool:
        """
        为审核员分配权限

        Args:
            user: 用户对象
            comment: 评论对象

        Returns:
            bool: 是否分配成功
        """
        return PermissionManager.bulk_assign_permissions(user, cls.ALL_PERMISSIONS, comment)

    @classmethod
    def can_moderate_comment(cls, user: User, comment: object) -> bool:
        """
        检查用户是否可以审核评论
        """
        return PermissionManager.check_user_permission(user, cls.MODERATE_PERMISSION, comment)

    @classmethod
    def can_reply_comment(cls, user: User, comment: object) -> bool:
        """
        检查用户是否可以回复评论
        """
        return PermissionManager.check_user_permission(user, cls.REPLY_PERMISSION, comment)

    @classmethod
    def can_manage_comment(cls, user: User, comment: object) -> bool:
        """
        检查用户是否可以管理评论（删除等）
        """
        return PermissionManager.check_user_permission(user, cls.MANAGE_PERMISSION, comment)
