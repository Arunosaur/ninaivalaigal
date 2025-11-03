from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar
from typing import Optional as _Optional
from typing import Union as _Union

from common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class GetUserAnalyticsRequest(_message.Message):
    __slots__ = ("user_id", "start_date", "end_date")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    start_date: str
    end_date: str
    def __init__(
        self, user_id: _Optional[str] = ..., start_date: _Optional[str] = ..., end_date: _Optional[str] = ...
    ) -> None: ...

class GetOrganizationAnalyticsRequest(_message.Message):
    __slots__ = ("organization_id", "start_date", "end_date")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    start_date: str
    end_date: str
    def __init__(
        self, organization_id: _Optional[str] = ..., start_date: _Optional[str] = ..., end_date: _Optional[str] = ...
    ) -> None: ...

class GetEngagementRequest(_message.Message):
    __slots__ = ("organization_id", "period")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    period: str
    def __init__(self, organization_id: _Optional[str] = ..., period: _Optional[str] = ...) -> None: ...

class GetCohortRequest(_message.Message):
    __slots__ = ("start_date", "end_date", "grouping")
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    GROUPING_FIELD_NUMBER: _ClassVar[int]
    start_date: str
    end_date: str
    grouping: str
    def __init__(
        self, start_date: _Optional[str] = ..., end_date: _Optional[str] = ..., grouping: _Optional[str] = ...
    ) -> None: ...

class UserAnalytics(_message.Message):
    __slots__ = ("user_id", "total_memories", "total_api_calls", "total_storage_bytes", "daily_metrics")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMORIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_API_CALLS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_STORAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    DAILY_METRICS_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    total_memories: int
    total_api_calls: int
    total_storage_bytes: int
    daily_metrics: _containers.RepeatedCompositeFieldContainer[DailyMetric]
    def __init__(
        self,
        user_id: _Optional[str] = ...,
        total_memories: _Optional[int] = ...,
        total_api_calls: _Optional[int] = ...,
        total_storage_bytes: _Optional[int] = ...,
        daily_metrics: _Optional[_Iterable[_Union[DailyMetric, _Mapping]]] = ...,
    ) -> None: ...

class OrganizationAnalytics(_message.Message):
    __slots__ = (
        "organization_id",
        "total_users",
        "active_users",
        "total_memories",
        "total_api_calls",
        "total_revenue",
        "team_metrics",
    )
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_USERS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_MEMORIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_API_CALLS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_REVENUE_FIELD_NUMBER: _ClassVar[int]
    TEAM_METRICS_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    total_users: int
    active_users: int
    total_memories: int
    total_api_calls: int
    total_revenue: float
    team_metrics: _containers.RepeatedCompositeFieldContainer[TeamMetric]
    def __init__(
        self,
        organization_id: _Optional[str] = ...,
        total_users: _Optional[int] = ...,
        active_users: _Optional[int] = ...,
        total_memories: _Optional[int] = ...,
        total_api_calls: _Optional[int] = ...,
        total_revenue: _Optional[float] = ...,
        team_metrics: _Optional[_Iterable[_Union[TeamMetric, _Mapping]]] = ...,
    ) -> None: ...

class EngagementMetrics(_message.Message):
    __slots__ = (
        "daily_active_users",
        "weekly_active_users",
        "monthly_active_users",
        "retention_rate",
        "churn_rate",
        "engagement_timeline",
    )
    DAILY_ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    WEEKLY_ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    MONTHLY_ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    RETENTION_RATE_FIELD_NUMBER: _ClassVar[int]
    CHURN_RATE_FIELD_NUMBER: _ClassVar[int]
    ENGAGEMENT_TIMELINE_FIELD_NUMBER: _ClassVar[int]
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    retention_rate: float
    churn_rate: float
    engagement_timeline: _containers.RepeatedCompositeFieldContainer[EngagementPoint]
    def __init__(
        self,
        daily_active_users: _Optional[int] = ...,
        weekly_active_users: _Optional[int] = ...,
        monthly_active_users: _Optional[int] = ...,
        retention_rate: _Optional[float] = ...,
        churn_rate: _Optional[float] = ...,
        engagement_timeline: _Optional[_Iterable[_Union[EngagementPoint, _Mapping]]] = ...,
    ) -> None: ...

class CohortAnalysis(_message.Message):
    __slots__ = ("cohorts", "grouping")
    COHORTS_FIELD_NUMBER: _ClassVar[int]
    GROUPING_FIELD_NUMBER: _ClassVar[int]
    cohorts: _containers.RepeatedCompositeFieldContainer[CohortGroup]
    grouping: str
    def __init__(
        self, cohorts: _Optional[_Iterable[_Union[CohortGroup, _Mapping]]] = ..., grouping: _Optional[str] = ...
    ) -> None: ...

class DailyMetric(_message.Message):
    __slots__ = ("date", "api_calls", "memories_created", "storage_used")
    DATE_FIELD_NUMBER: _ClassVar[int]
    API_CALLS_FIELD_NUMBER: _ClassVar[int]
    MEMORIES_CREATED_FIELD_NUMBER: _ClassVar[int]
    STORAGE_USED_FIELD_NUMBER: _ClassVar[int]
    date: str
    api_calls: int
    memories_created: int
    storage_used: int
    def __init__(
        self,
        date: _Optional[str] = ...,
        api_calls: _Optional[int] = ...,
        memories_created: _Optional[int] = ...,
        storage_used: _Optional[int] = ...,
    ) -> None: ...

class TeamMetric(_message.Message):
    __slots__ = ("team_id", "team_name", "members", "memories", "api_calls")
    TEAM_ID_FIELD_NUMBER: _ClassVar[int]
    TEAM_NAME_FIELD_NUMBER: _ClassVar[int]
    MEMBERS_FIELD_NUMBER: _ClassVar[int]
    MEMORIES_FIELD_NUMBER: _ClassVar[int]
    API_CALLS_FIELD_NUMBER: _ClassVar[int]
    team_id: str
    team_name: str
    members: int
    memories: int
    api_calls: int
    def __init__(
        self,
        team_id: _Optional[str] = ...,
        team_name: _Optional[str] = ...,
        members: _Optional[int] = ...,
        memories: _Optional[int] = ...,
        api_calls: _Optional[int] = ...,
    ) -> None: ...

class EngagementPoint(_message.Message):
    __slots__ = ("date", "active_users", "new_users", "churned_users")
    DATE_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_USERS_FIELD_NUMBER: _ClassVar[int]
    NEW_USERS_FIELD_NUMBER: _ClassVar[int]
    CHURNED_USERS_FIELD_NUMBER: _ClassVar[int]
    date: str
    active_users: int
    new_users: int
    churned_users: int
    def __init__(
        self,
        date: _Optional[str] = ...,
        active_users: _Optional[int] = ...,
        new_users: _Optional[int] = ...,
        churned_users: _Optional[int] = ...,
    ) -> None: ...

class CohortGroup(_message.Message):
    __slots__ = ("cohort_id", "start_date", "initial_users", "retention_rates", "lifetime_value")
    COHORT_ID_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    INITIAL_USERS_FIELD_NUMBER: _ClassVar[int]
    RETENTION_RATES_FIELD_NUMBER: _ClassVar[int]
    LIFETIME_VALUE_FIELD_NUMBER: _ClassVar[int]
    cohort_id: str
    start_date: str
    initial_users: int
    retention_rates: _containers.RepeatedScalarFieldContainer[float]
    lifetime_value: float
    def __init__(
        self,
        cohort_id: _Optional[str] = ...,
        start_date: _Optional[str] = ...,
        initial_users: _Optional[int] = ...,
        retention_rates: _Optional[_Iterable[float]] = ...,
        lifetime_value: _Optional[float] = ...,
    ) -> None: ...
