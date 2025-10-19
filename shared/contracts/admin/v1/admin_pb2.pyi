from common.v1 import errors_pb2 as _errors_pb2
from common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ListUsersRequest(_message.Message):
    __slots__ = ("page", "filter", "search")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    FILTER_FIELD_NUMBER: _ClassVar[int]
    SEARCH_FIELD_NUMBER: _ClassVar[int]
    page: _pagination_pb2.PageRequest
    filter: str
    search: str
    def __init__(self, page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ..., filter: _Optional[str] = ..., search: _Optional[str] = ...) -> None: ...

class GetUserRequest(_message.Message):
    __slots__ = ("user_id",)
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    def __init__(self, user_id: _Optional[str] = ...) -> None: ...

class UpdateUserRequest(_message.Message):
    __slots__ = ("user_id", "full_name", "roles", "is_active")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    FULL_NAME_FIELD_NUMBER: _ClassVar[int]
    ROLES_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    full_name: str
    roles: _containers.RepeatedScalarFieldContainer[str]
    is_active: bool
    def __init__(self, user_id: _Optional[str] = ..., full_name: _Optional[str] = ..., roles: _Optional[_Iterable[str]] = ..., is_active: bool = ...) -> None: ...

class SuspendUserRequest(_message.Message):
    __slots__ = ("user_id", "reason", "duration_days")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    DURATION_DAYS_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    reason: str
    duration_days: int
    def __init__(self, user_id: _Optional[str] = ..., reason: _Optional[str] = ..., duration_days: _Optional[int] = ...) -> None: ...

class SuspendUserResponse(_message.Message):
    __slots__ = ("success", "suspended_until")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    SUSPENDED_UNTIL_FIELD_NUMBER: _ClassVar[int]
    success: bool
    suspended_until: str
    def __init__(self, success: bool = ..., suspended_until: _Optional[str] = ...) -> None: ...

class ListOrganizationsRequest(_message.Message):
    __slots__ = ("page", "tier_filter")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    TIER_FILTER_FIELD_NUMBER: _ClassVar[int]
    page: _pagination_pb2.PageRequest
    tier_filter: str
    def __init__(self, page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ..., tier_filter: _Optional[str] = ...) -> None: ...

class GetSystemMetricsRequest(_message.Message):
    __slots__ = ("period",)
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    period: str
    def __init__(self, period: _Optional[str] = ...) -> None: ...

class GetAuditLogsRequest(_message.Message):
    __slots__ = ("user_id", "action_type", "start_date", "end_date", "page")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    action_type: str
    start_date: str
    end_date: str
    page: _pagination_pb2.PageRequest
    def __init__(self, user_id: _Optional[str] = ..., action_type: _Optional[str] = ..., start_date: _Optional[str] = ..., end_date: _Optional[str] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class UserList(_message.Message):
    __slots__ = ("users", "page_info")
    USERS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    users: _containers.RepeatedCompositeFieldContainer[UserSummary]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, users: _Optional[_Iterable[_Union[UserSummary, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class UserSummary(_message.Message):
    __slots__ = ("id", "email", "full_name", "is_active", "created_at", "last_login")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    FULL_NAME_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_LOGIN_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: str
    last_login: str
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., full_name: _Optional[str] = ..., is_active: bool = ..., created_at: _Optional[str] = ..., last_login: _Optional[str] = ...) -> None: ...

class UserDetails(_message.Message):
    __slots__ = ("id", "email", "full_name", "roles", "is_active", "created_at", "last_login", "total_memories", "total_api_calls", "organizations")
    ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    FULL_NAME_FIELD_NUMBER: _ClassVar[int]
    ROLES_FIELD_NUMBER: _ClassVar[int]
    IS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    LAST_LOGIN_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMORIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_API_CALLS_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATIONS_FIELD_NUMBER: _ClassVar[int]
    id: str
    email: str
    full_name: str
    roles: _containers.RepeatedScalarFieldContainer[str]
    is_active: bool
    created_at: str
    last_login: str
    total_memories: int
    total_api_calls: int
    organizations: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., email: _Optional[str] = ..., full_name: _Optional[str] = ..., roles: _Optional[_Iterable[str]] = ..., is_active: bool = ..., created_at: _Optional[str] = ..., last_login: _Optional[str] = ..., total_memories: _Optional[int] = ..., total_api_calls: _Optional[int] = ..., organizations: _Optional[_Iterable[str]] = ...) -> None: ...

class OrganizationList(_message.Message):
    __slots__ = ("organizations", "page_info")
    ORGANIZATIONS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    organizations: _containers.RepeatedCompositeFieldContainer[OrganizationSummary]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, organizations: _Optional[_Iterable[_Union[OrganizationSummary, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class OrganizationSummary(_message.Message):
    __slots__ = ("id", "name", "tier", "member_count", "monthly_revenue", "created_at")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    MEMBER_COUNT_FIELD_NUMBER: _ClassVar[int]
    MONTHLY_REVENUE_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    tier: str
    member_count: int
    monthly_revenue: float
    created_at: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., tier: _Optional[str] = ..., member_count: _Optional[int] = ..., monthly_revenue: _Optional[float] = ..., created_at: _Optional[str] = ...) -> None: ...

class SystemMetrics(_message.Message):
    __slots__ = ("total_users", "active_users", "total_organizations", "total_memories", "api_calls_per_second", "system_health_score", "services")
    TOTAL_USERS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_ORGANIZATIONS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMORIES_FIELD_NUMBER: _ClassVar[int]
    API_CALLS_PER_SECOND_FIELD_NUMBER: _ClassVar[int]
    SYSTEM_HEALTH_SCORE_FIELD_NUMBER: _ClassVar[int]
    SERVICES_FIELD_NUMBER: _ClassVar[int]
    total_users: int
    active_users: int
    total_organizations: int
    total_memories: int
    api_calls_per_second: int
    system_health_score: float
    services: _containers.RepeatedCompositeFieldContainer[ServiceStatus]
    def __init__(self, total_users: _Optional[int] = ..., active_users: _Optional[int] = ..., total_organizations: _Optional[int] = ..., total_memories: _Optional[int] = ..., api_calls_per_second: _Optional[int] = ..., system_health_score: _Optional[float] = ..., services: _Optional[_Iterable[_Union[ServiceStatus, _Mapping]]] = ...) -> None: ...

class ServiceStatus(_message.Message):
    __slots__ = ("name", "status", "response_time_ms", "error_rate")
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    ERROR_RATE_FIELD_NUMBER: _ClassVar[int]
    name: str
    status: str
    response_time_ms: float
    error_rate: float
    def __init__(self, name: _Optional[str] = ..., status: _Optional[str] = ..., response_time_ms: _Optional[float] = ..., error_rate: _Optional[float] = ...) -> None: ...

class AuditLogList(_message.Message):
    __slots__ = ("logs", "page_info")
    LOGS_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    logs: _containers.RepeatedCompositeFieldContainer[AuditLog]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, logs: _Optional[_Iterable[_Union[AuditLog, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class AuditLog(_message.Message):
    __slots__ = ("id", "user_id", "action", "resource_type", "resource_id", "timestamp", "ip_address", "metadata")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    timestamp: str
    ip_address: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ..., action: _Optional[str] = ..., resource_type: _Optional[str] = ..., resource_id: _Optional[str] = ..., timestamp: _Optional[str] = ..., ip_address: _Optional[str] = ..., metadata: _Optional[_Mapping[str, str]] = ...) -> None: ...
