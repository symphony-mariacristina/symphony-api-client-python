from unittest.mock import MagicMock, AsyncMock

import pytest
import base64

from symphony.bdk.core.auth.auth_session import AuthSession
from symphony.bdk.core.service.user.model.role_id import RoleId
from symphony.bdk.core.service.user.user_service import UserService
from symphony.bdk.gen.agent_api.audit_trail_api import AuditTrailApi
from symphony.bdk.gen.pod_api.system_api import SystemApi
from symphony.bdk.gen.pod_api.user_api import UserApi
from symphony.bdk.gen.pod_api.users_api import UsersApi
from symphony.bdk.gen.pod_model.avatar_update import AvatarUpdate
from symphony.bdk.gen.pod_model.followers_list import FollowersList
from symphony.bdk.gen.pod_model.string_id import StringId
from symphony.bdk.gen.pod_model.user_filter import UserFilter
from symphony.bdk.gen.pod_model.user_id_list import UserIdList
from symphony.bdk.gen.pod_model.user_search_filter import UserSearchFilter
from symphony.bdk.gen.pod_model.user_search_query import UserSearchQuery
from tests.utils.resource_utils import object_from_json_relative_path, object_from_json, get_resource_filepath
from symphony.bdk.gen.pod_model.delegate_action import DelegateAction
from symphony.bdk.core.service.user.model.delegate_action_enum import DelegateActionEnum
from symphony.bdk.gen.pod_model.feature_list import FeatureList
from symphony.bdk.gen.pod_model.feature import Feature
from symphony.bdk.gen.pod_model.user_status import UserStatus
from symphony.bdk.gen.pod_model.v2_user_create import V2UserCreate
from symphony.bdk.gen.pod_model.v2_user_attributes import V2UserAttributes
from symphony.bdk.gen.pod_model.user_suspension import UserSuspension


@pytest.fixture()
def auth_session():
    auth_session = AuthSession(None)
    auth_session.session_token = 'session_token'
    auth_session.key_manager_token = 'km_token'
    return auth_session


@pytest.fixture()
def user_api():
    return MagicMock(UserApi)


@pytest.fixture()
def users_api():
    return MagicMock(UsersApi)


@pytest.fixture()
def audit_trail_api():
    return MagicMock(AuditTrailApi)


@pytest.fixture()
def system_api():
    return MagicMock(SystemApi)


@pytest.fixture()
def user_service(user_api, users_api, audit_trail_api, system_api, auth_session):
    service = UserService(
        user_api,
        users_api,
        audit_trail_api,
        system_api,
        auth_session
    )
    return service


@pytest.mark.asyncio
async def test_list_users_by_ids(users_api, user_service):
    users_api.v3_users_get = AsyncMock()
    users_api.v3_users_get.return_value = object_from_json_relative_path("user/list_user.json")
    users_list = await user_service.list_users_by_ids([15942919536460, 15942919536461], active=True)

    users_api.v3_users_get.assert_called_with(
        uid='15942919536460,15942919536461',
        local=False,
        session_token="session_token",
        active=True
    )
    assert len(users_list.users) == 2
    assert len(users_list.errors) == 2
    assert users_list.users[0].username == 'tw'


@pytest.mark.asyncio
async def test_list_users_by_emails(users_api, user_service):
    users_api.v3_users_get = AsyncMock()
    users_api.v3_users_get.return_value = object_from_json_relative_path("user/list_user.json")
    users_list = await user_service.list_users_by_emails(
        ['technicalwriter@symphony.com', 'serviceaccount@symphony.com'],
        active=True
    )

    users_api.v3_users_get.assert_called_with(
        email='technicalwriter@symphony.com,serviceaccount@symphony.com',
        local=False,
        session_token="session_token",
        active=True
    )
    assert len(users_list.users) == 2
    assert len(users_list.errors) == 2
    assert users_list.users[0].username == 'tw'


@pytest.mark.asyncio
async def test_list_users_by_usernames(users_api, user_service):
    users_api.v3_users_get = AsyncMock()
    users_api.v3_users_get.return_value = object_from_json_relative_path("user/list_user.json")
    users_list = await user_service.list_users_by_usernames(
        ['tw', 'SA'],
        active=True
    )

    users_api.v3_users_get.assert_called_with(
        username='tw,SA',
        local=True,
        session_token="session_token",
        active=True
    )

    assert len(users_list.users) == 2
    assert len(users_list.errors) == 2
    assert users_list.users[0].emailAddress == 'technicalwriter@symphony.com'


@pytest.mark.asyncio
async def test_search_users(users_api, user_service):
    users_api.v1_user_search_post = AsyncMock()
    users_api.v1_user_search_post.return_value = object_from_json_relative_path("user/search_user.json")
    query = UserSearchQuery(query='jane', filters=UserSearchFilter(title='Sales Manager', company='Symphony'))
    result = await user_service.search_users(query)

    users_api.v1_user_search_post.assert_called_with(
        search_request=query,
        local=False,
        skip=0,
        limit=50,
        session_token='session_token'
    )
    assert result.count == 1
    assert len(result.users) == 1
    assert result.users[0].id == 13056700581099


@pytest.mark.asyncio
async def test_follow_user(user_api, user_service):
    user_api.v1_user_uid_follow_post = AsyncMock()
    user_api.v1_user_uid_follow_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "User(s) successfully added in the list of followers"'
        '}')

    await user_service.follow_user([1234, 2345], 12345)

    user_api.v1_user_uid_follow_post.assert_called_with(
        uid=12345,
        uid_list=FollowersList(followers=UserIdList(value=[1234, 2345])),
        session_token="session_token"
    )


@pytest.mark.asyncio
async def test_unfollow_user(user_api, user_service):
    user_api.v1_user_uid_unfollow_post = AsyncMock()
    user_api.v1_user_uid_unfollow_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "User(s) successfully removed from the list of followers"'
        '}'
    )

    await user_service.unfollow_user([1234, 2345], 12345)

    user_api.v1_user_uid_unfollow_post.assert_called_with(
        uid=12345,
        uid_list=FollowersList(followers=UserIdList(value=[1234, 2345])),
        session_token="session_token"
    )


@pytest.mark.asyncio
async def test_get_user_detail(user_api, user_service):
    user_api.v2_admin_user_uid_get = AsyncMock()
    user_api.v2_admin_user_uid_get.return_value = object_from_json_relative_path("user/user_detail.json")

    user_detail = await user_service.get_user_detail(7215545078461)

    user_api.v2_admin_user_uid_get.assert_called_with(
        uid=7215545078461,
        session_token="session_token"
    )

    assert user_detail.userAttributes.userName == 'johndoe'
    assert user_detail.userSystemInfo.status == 'ENABLED'
    assert len(user_detail.roles) == 6


@pytest.mark.asyncio
async def test_list_user_details(user_api, user_service):
    user_api.v2_admin_user_list_get = AsyncMock()
    user_api.v2_admin_user_list_get.return_value = \
        object_from_json_relative_path("user/list_user_detail.json")

    user_detail_list = await user_service.list_user_details()

    user_api.v2_admin_user_list_get.assert_called_with(
        skip=0,
        limit=50,
        session_token="session_token"
    )

    assert len(user_detail_list) == 5
    assert user_detail_list[0].userAttributes.userName == "agentservice"
    assert user_detail_list[1].userSystemInfo.id == 9826885173258


@pytest.mark.asyncio
async def test_list_user_details_by_filter(user_api, user_service):
    user_api.v1_admin_user_find_post = AsyncMock()
    user_api.v1_admin_user_find_post.return_value = \
        object_from_json_relative_path("user/list_user_detail.json")
    user_filter = UserFilter(status="ENABLED")

    user_detail_list = await user_service.list_user_details_by_filter(user_filter)

    user_api.v1_admin_user_find_post.assert_called_with(
        skip=0,
        limit=50,
        payload=user_filter,
        session_token="session_token"
    )

    assert len(user_detail_list) == 5
    assert user_detail_list[0].userAttributes.userName == "agentservice"
    assert user_detail_list[1].userSystemInfo.id == 9826885173258


@pytest.mark.asyncio
async def test_add_role(user_api, user_service):
    user_api.v1_admin_user_uid_roles_add_post = AsyncMock()
    user_api.v1_admin_user_uid_roles_add_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "Role added"'
        '}'
    )

    await user_service.add_role(1234, RoleId.INDIVIDUAL)

    user_api.v1_admin_user_uid_roles_add_post.assert_called_with(
        uid=1234,
        payload=StringId(id='INDIVIDUAL'),
        session_token="session_token"
    )


@pytest.mark.asyncio
async def test_list_roles(system_api, user_service):
    system_api.v1_admin_system_roles_list_get = AsyncMock()
    system_api.v1_admin_system_roles_list_get.return_value = \
        object_from_json_relative_path("user/list_roles.json")

    role_list = await user_service.list_roles()

    system_api.v1_admin_system_roles_list_get.assert_called_with(
        session_token="session_token"
    )

    assert len(role_list) == 12
    assert role_list[0].id == 'CONTENT_MANAGEMENT'
    assert role_list[1].id == 'COMPLIANCE_OFFICER'


@pytest.mark.asyncio
async def test_remove_role(user_api, user_service):
    user_api.v1_admin_user_uid_roles_remove_post = AsyncMock()
    user_api.v1_admin_user_uid_roles_remove_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "Role removed"'
        '}'
    )

    await user_service.remove_role(1234, RoleId.INDIVIDUAL)

    user_api.v1_admin_user_uid_roles_remove_post.assert_called_with(
        uid=1234,
        payload=StringId(id='INDIVIDUAL'),
        session_token="session_token"
    )


@pytest.mark.asyncio
async def test_get_avatar(user_api, user_service):
    user_api.v1_admin_user_uid_avatar_get = AsyncMock()
    user_api.v1_admin_user_uid_avatar_get.return_value = \
        object_from_json_relative_path("user/list_avatar.json")

    avatar_list = await user_service.get_avatar(1234)

    user_api.v1_admin_user_uid_avatar_get.assert_called_with(
        uid=1234,
        session_token="session_token"
    )

    assert len(avatar_list) == 5
    assert avatar_list[0].size == '600'
    assert avatar_list[1].url == '../avatars/acme/150/7215545057281/3gXMhglCCTwLPL9JAprnyHzYn5-PR49-wYDG814n1g8.png'


@pytest.mark.asyncio
async def test_update_avatar(user_api, user_service):
    user_api.v1_admin_user_uid_avatar_update_post = AsyncMock()
    user_api.v1_admin_user_uid_avatar_update_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "OK"'
        '}'
    )

    await user_service.update_avatar(1234, "image_string")
    user_api.v1_admin_user_uid_avatar_update_post.assert_called_with(
        uid=1234,
        payload=AvatarUpdate(image="image_string"),
        session_token="session_token"
    )

    with open(get_resource_filepath('user/FINOS_icon_rgb.png', as_text=True), 'rb') as f:
        avatar_bytes = f.read()
        await user_service.update_avatar(1234, avatar_bytes)

        user_api.v1_admin_user_uid_avatar_update_post.assert_called_with(
            uid=1234,
            payload=AvatarUpdate(image=str(base64.standard_b64encode(avatar_bytes))),
            session_token="session_token"
        )


@pytest.mark.asyncio
async def test_get_disclaimer(user_api, user_service):
    user_api.v1_admin_user_uid_disclaimer_get = AsyncMock()
    user_api.v1_admin_user_uid_disclaimer_get.return_value = object_from_json(
        '{'
        '   "id": "571d2052e4b042aaf06d2e7a",'
        '   "name": "Enterprise Disclaimer",'
        '   "content": "This is a disclaimer for the enterprise.",'
        '   "frequencyInHours": 24,'
        '   "isDefault": false,'
        '   "isActive": true,'
        '   "createdDate": 1461526610846,'
        '   "modifiedDate": 1461526610846'
        '}'
    )

    disclaimer = await user_service.get_disclaimer(1234)

    user_api.v1_admin_user_uid_disclaimer_get.assert_called_with(
        uid=1234,
        session_token="session_token"
    )

    assert disclaimer.id == '571d2052e4b042aaf06d2e7a'
    assert disclaimer.name == 'Enterprise Disclaimer'


@pytest.mark.asyncio
async def test_remove_disclaimer(user_api, user_service):
    user_api.v1_admin_user_uid_disclaimer_delete = AsyncMock()
    user_api.v1_admin_user_uid_disclaimer_delete.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "OK"'
        '}'
    )

    await user_service.remove_disclaimer(1234)

    user_api.v1_admin_user_uid_disclaimer_delete.assert_called_with(
        uid=1234,
        session_token="session_token"
    )


@pytest.mark.asyncio
async def test_add_disclaimer(user_api, user_service):
    user_api.v1_admin_user_uid_disclaimer_update_post = AsyncMock()
    user_api.v1_admin_user_uid_disclaimer_update_post.return_value = object_from_json(
        '{'
        '  "format": "TEXT",'
        '  "message": "OK"'
        '}'
    )

    await user_service.add_disclaimer(1234, 'disclaimer_id')

    user_api.v1_admin_user_uid_disclaimer_update_post.assert_called_with(
        uid=1234,
        payload=StringId(id='disclaimer_id'),
        session_token='session_token'
    )


@pytest.mark.asyncio
async def test_get_delegates(user_api, user_service):
    user_api.v1_admin_user_uid_delegates_get = AsyncMock()
    user_api.v1_admin_user_uid_delegates_get.return_value = object_from_json(
        '{'
        '   "value": [7215545078461]'
        '}'
    )

    delegate_list = await user_service.get_delegates(1234)

    user_api.v1_admin_user_uid_delegates_get.assert_called_with(
        uid=1234,
        session_token='session_token'
    )

    assert len(delegate_list) == 1
    assert delegate_list[0] == 7215545078461


@pytest.mark.asyncio
async def test_update_delegates(user_api, user_service):
    user_api.v1_admin_user_uid_delegates_update_post = AsyncMock()
    user_api.v1_admin_user_uid_delegates_update_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "Added delegate [7215545078461] for account [7215545078541]"'
        '}'
    )

    await user_service.update_delegates(7215545078541, 7215545078461, DelegateActionEnum.ADD)

    user_api.v1_admin_user_uid_delegates_update_post.assert_called_with(
        uid=7215545078541,
        payload=DelegateAction(user_id=7215545078461, action=DelegateActionEnum.ADD.value),
        session_token='session_token'
    )


@pytest.mark.asyncio
async def test_get_feature_entitlements(user_api, user_service):
    user_api.v1_admin_user_uid_features_get = AsyncMock()
    user_api.v1_admin_user_uid_features_get.return_value = object_from_json(
        '{'
        '   "value": ['
        '       {'
        '           "entitlment": "canCreatePublicRoom",'
        '           "enabled": true},'
        '       {   '
        '           "entitlment": "isExternalRoomEnabled",'
        '           "enabled": false'
        '       }'
        '   ]'
        '}'
    )

    feature_list = await user_service.get_feature_entitlements(1234)

    user_api.v1_admin_user_uid_features_get.assert_called_with(
        uid=1234,
        session_token='session_token'
    )

    assert len(feature_list) == 2
    assert feature_list[0].entitlment == 'canCreatePublicRoom'
    assert not feature_list[1].enabled


@pytest.mark.asyncio
async def test_update_feature_entitlements(user_api, user_service):
    user_api.v1_admin_user_uid_features_update_post = AsyncMock()
    user_api.v1_admin_user_uid_features_update_post.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "OK"'
        '}'
    )
    feature = Feature(entitlment='canCreatePublicRoom', enabled=True)
    await user_service.update_feature_entitlements(1234, [feature])

    user_api.v1_admin_user_uid_features_update_post.assert_called_with(
        uid=1234,
        payload=FeatureList(value=[feature]),
        session_token='session_token'
    )


@pytest.mark.asyncio
async def test_get_status(user_api, user_service):
    user_api.v1_admin_user_uid_status_get = AsyncMock()
    user_api.v1_admin_user_uid_status_get.return_value = object_from_json(
        '{'
        '   "status": "ENABLED"'
        '}'
    )

    status = await user_service.get_status(1234)

    user_api.v1_admin_user_uid_status_get.assert_called_with(
        uid=1234,
        session_token='session_token'
    )

    assert status.status == 'ENABLED'


@pytest.mark.asyncio
async def test_update_status(user_api, user_service):
    user_api.v1_admin_user_uid_status_update_post = AsyncMock()
    user_api.v1_admin_user_uid_status_update_post.return_value = object_from_json(
        '{'
        '   "message": "OK"'
        '}'
    )
    status = UserStatus(status="ENABLED")

    await user_service.update_status(1234, status)

    user_api.v1_admin_user_uid_status_update_post.assert_called_with(
        uid=1234,
        payload=status,
        session_token='session_token'
    )


@pytest.mark.asyncio
async def test_list_user_followers(user_api, user_service):
    user_api.v1_user_uid_followers_get = AsyncMock()
    user_api.v1_user_uid_followers_get.return_value = object_from_json(
        '{'
        '   "count": 5,'
        '   "followers": ['
        '       13056700579848,'
        '       13056700580889,'
        '       13056700580890'
        '   ],'
        '   "pagination": {'
        '       "cursors": {'
        '           "before": "1",'
        '           "after": "4"'
        '       }'
        '   }'
        '}'
    )

    follower_list = await user_service.list_user_followers(1234, before=4, after=1)

    user_api.v1_user_uid_followers_get.assert_called_with(
        uid=1234,
        limit=100,
        session_token='session_token',
        before=4,
        after=1
    )

    assert follower_list.count == 5
    assert follower_list.followers[0] == 13056700579848
    assert follower_list.followers[1] == 13056700580889


@pytest.mark.asyncio
async def test_list_users_following(user_api, user_service):
    user_api.v1_user_uid_following_get = AsyncMock()
    user_api.v1_user_uid_following_get.return_value = object_from_json(
        '{'
        '   "count": 3,'
        '   "following": ['
        '       13056700580888,'
        '       13056700580889'
        '   ],'
        '   "pagination": {'
        '       "cursors": {'
        '           "before": "1"'
        '       }'
        '   }'
        '}'
    )
    following_user_list = await user_service.list_users_following(1234, before=4, after=1)

    user_api.v1_user_uid_following_get.assert_called_with(
        uid=1234,
        limit=100,
        session_token='session_token',
        before=4,
        after=1
    )

    assert following_user_list.count == 3
    assert following_user_list.following[0] == 13056700580888
    assert following_user_list.following[1] == 13056700580889


@pytest.mark.asyncio
async def test_create(user_api, user_service):
    user_api.v2_admin_user_create_post = AsyncMock()
    user_api.v2_admin_user_create_post.return_value = object_from_json_relative_path("user/user_detail.json")

    user_create = V2UserCreate()
    user_detail = await user_service.create(user_create)

    user_api.v2_admin_user_create_post.assert_called_with(
        payload=user_create,
        session_token='session_token'
    )

    assert user_detail.userAttributes.userName == 'johndoe'
    assert user_detail.userSystemInfo.status == 'ENABLED'
    assert len(user_detail.roles) == 6


@pytest.mark.asyncio
async def test_update(user_api, user_service):
    user_api.v2_admin_user_uid_update_post = AsyncMock()
    user_api.v2_admin_user_uid_update_post.return_value = object_from_json_relative_path("user/user_detail.json")

    user_attribute = V2UserAttributes()

    user_detail = await user_service.update(1234, user_attribute)

    user_api.v2_admin_user_uid_update_post.assert_called_with(
        uid=1234,
        payload=user_attribute,
        session_token='session_token'
    )

    assert user_detail.userAttributes.userName == 'johndoe'
    assert user_detail.userSystemInfo.status == 'ENABLED'
    assert len(user_detail.roles) == 6


@pytest.mark.asyncio
async def test_list_audit_trail(audit_trail_api, user_service):
    audit_trail_api.v1_audittrail_privilegeduser_get = AsyncMock()
    audit_trail_api.v1_audittrail_privilegeduser_get.return_value = \
        object_from_json_relative_path("user/list_audit_trail.json")

    audit_trail_initiator_list = \
        await user_service.list_audit_trail(1234, 2345, 12345, RoleId.SUPER_ADMINISTRATOR, before=1, after=4)

    audit_trail_api.v1_audittrail_privilegeduser_get.assert_called_with(
        start_timestamp=1234,
        end_timestamp=2345,
        initiator_id=12345,
        role='SUPER_ADMINISTRATOR',
        before=1,
        after=4,
        limit=50,
        session_token='session_token',
        key_manager_token='km_token'
    )

    assert len(audit_trail_initiator_list.items) == 2
    assert audit_trail_initiator_list.items[0].initiatorId == 1353716993
    assert audit_trail_initiator_list.items[1].authorizationRoles[0] == 'SUPER_ADMINISTRATOR'


@pytest.mark.asyncio
async def test_suspend_user(user_api, user_service):
    user_api.v1_admin_user_user_id_suspension_update_put = AsyncMock()
    user_api.v1_admin_user_user_id_suspension_update_put.return_value = object_from_json(
        '{'
        '   "format": "TEXT",'
        '   "message": "User suspended with success"'
        '}'
    )

    user_suspension = UserSuspension(suspended=True, suspended_until=1601596799999, suspension_reason='testing')

    await user_service.suspend_user(1234, user_suspension)

    user_api.v1_admin_user_user_id_suspension_update_put.assert_called_with(
        user_id=1234,
        payload=user_suspension,
        session_token='session_token'
    )