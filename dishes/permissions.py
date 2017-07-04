# -*- coding:utf8 -*-
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.IsAuthenticated):
    """
    自定义权限，只有创建者才能编辑
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the dishes.
        return obj.user_id == request.user.id


# class IsAdminOrOwner(permissions.IsAuthenticated):
#     """
#     自定义权限，只有管理员可以查看所有数据，用户只可以查看自己的数据
#     """
#     def has_permission(self, request, view):
#         if request.user.is_admin is True:
#             return True
#
#

