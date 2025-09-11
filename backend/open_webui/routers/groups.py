import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from open_webui.config import CACHE_DIR
from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.groups import (
    GroupForm,
    GroupResponse,
    Groups,
    GroupUpdateForm,
    JoinGroupForm,
    UserIdsForm,
)
from open_webui.models.users import Users
from open_webui.utils.auth import get_admin_user, get_verified_user

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()

############################
# GetGroups
############################


@router.get("/", response_model=list[GroupResponse])
async def get_groups(user=Depends(get_verified_user)):
    """
    Get groups based on user role:
    - Admins see all groups
    - Regular users see public groups they can discover and join
    """
    return Groups.get_groups_for_user(user.id, user.role)


############################
# GetPublicGroups
############################


@router.get("/public", response_model=list[GroupResponse])
async def get_public_groups(user=Depends(get_verified_user)):
    """
    Get all public groups that users can discover and join
    """
    return Groups.get_public_groups()


############################
# GetMyGroups
############################


@router.get("/my", response_model=list[GroupResponse])
async def get_my_groups(user=Depends(get_verified_user)):
    """
    Get groups where the current user is a member
    """
    return Groups.get_groups_by_member_id(user.id)


############################
# JoinGroup
############################


@router.post("/join", response_model=Optional[GroupResponse])
async def join_group(form_data: JoinGroupForm, user=Depends(get_verified_user)):
    """
    Allow a user to join a public group
    """
    try:
        # Check if group exists and is public
        group = Groups.get_group_by_id(form_data.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )

        # Check if user can join this group
        if not group.is_public and group.join_policy != "open":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ERROR_MESSAGES.DEFAULT("This group is not open for joining"),
            )

        # Check if user is already a member
        if Groups.is_user_member(form_data.group_id, user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("You are already a member of this group"),
            )

        # Join the group
        updated_group = Groups.join_group(form_data.group_id, user.id)
        if updated_group:
            return updated_group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error joining group"),
            )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error joining group {form_data.group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# LeaveGroup
############################


@router.post("/leave", response_model=Optional[GroupResponse])
async def leave_group(form_data: JoinGroupForm, user=Depends(get_verified_user)):
    """
    Allow a user to leave a group they are a member of
    """
    try:
        # Check if group exists
        group = Groups.get_group_by_id(form_data.group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )

        # Check if user is a member
        if not Groups.is_user_member(form_data.group_id, user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("You are not a member of this group"),
            )

        # Leave the group
        updated_group = Groups.leave_group(form_data.group_id, user.id)
        if updated_group:
            return updated_group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error leaving group"),
            )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error leaving group {form_data.group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# CreateNewGroup (Admin only)
############################


@router.post("/create", response_model=Optional[GroupResponse])
async def create_new_group(form_data: GroupForm, user=Depends(get_admin_user)):
    try:
        group = Groups.insert_new_group(user.id, form_data)
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error creating group"),
            )
    except Exception as e:
        log.exception(f"Error creating a new group: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# GetGroupById
############################


@router.get("/id/{id}", response_model=Optional[GroupResponse])
async def get_group_by_id(id: str, user=Depends(get_verified_user)):
    """
    Get group by ID. Regular users can only see public groups or groups they're members of
    """
    group = Groups.get_group_by_id(id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    # Check if user has permission to view this group
    if user.role != "admin":
        # Regular users can only see public groups or groups they're members of
        if not group.is_public and not Groups.is_user_member(id, user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ERROR_MESSAGES.DEFAULT("Access denied"),
            )

    return group


############################
# UpdateGroupById (Admin only)
############################


@router.post("/id/{id}/update", response_model=Optional[GroupResponse])
async def update_group_by_id(
    id: str, form_data: GroupUpdateForm, user=Depends(get_admin_user)
):
    try:
        if form_data.user_ids:
            form_data.user_ids = Users.get_valid_user_ids(form_data.user_ids)

        group = Groups.update_group_by_id(id, form_data)
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating group"),
            )
    except Exception as e:
        log.exception(f"Error updating group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# AddUserToGroupByUserIdAndGroupId (Admin only)
############################


@router.post("/id/{id}/users/add", response_model=Optional[GroupResponse])
async def add_user_to_group(
    id: str, form_data: UserIdsForm, user=Depends(get_admin_user)
):
    try:
        if form_data.user_ids:
            form_data.user_ids = Users.get_valid_user_ids(form_data.user_ids)

        group = Groups.add_users_to_group(id, form_data.user_ids)
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error adding users to group"),
            )
    except Exception as e:
        log.exception(f"Error adding users to group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# RemoveUsersFromGroup (Admin only)
############################


@router.post("/id/{id}/users/remove", response_model=Optional[GroupResponse])
async def remove_users_from_group(
    id: str, form_data: UserIdsForm, user=Depends(get_admin_user)
):
    try:
        group = Groups.remove_users_from_group(id, form_data.user_ids)
        if group:
            return group
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error removing users from group"),
            )
    except Exception as e:
        log.exception(f"Error removing users from group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# DeleteGroupById (Admin only)
############################


@router.delete("/id/{id}/delete", response_model=bool)
async def delete_group_by_id(id: str, user=Depends(get_admin_user)):
    try:
        result = Groups.delete_group_by_id(id)
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting group"),
            )
    except Exception as e:
        log.exception(f"Error deleting group {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )
