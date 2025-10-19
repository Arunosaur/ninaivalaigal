from common.v1 import errors_pb2 as _errors_pb2
from common.v1 import pagination_pb2 as _pagination_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SubscriptionTier(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUBSCRIPTION_TIER_UNSPECIFIED: _ClassVar[SubscriptionTier]
    SUBSCRIPTION_TIER_FREE: _ClassVar[SubscriptionTier]
    SUBSCRIPTION_TIER_STARTER: _ClassVar[SubscriptionTier]
    SUBSCRIPTION_TIER_PRO: _ClassVar[SubscriptionTier]
    SUBSCRIPTION_TIER_ENTERPRISE: _ClassVar[SubscriptionTier]

class SubscriptionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SUBSCRIPTION_STATUS_UNSPECIFIED: _ClassVar[SubscriptionStatus]
    SUBSCRIPTION_STATUS_ACTIVE: _ClassVar[SubscriptionStatus]
    SUBSCRIPTION_STATUS_CANCELLED: _ClassVar[SubscriptionStatus]
    SUBSCRIPTION_STATUS_EXPIRED: _ClassVar[SubscriptionStatus]
    SUBSCRIPTION_STATUS_TRIAL: _ClassVar[SubscriptionStatus]
SUBSCRIPTION_TIER_UNSPECIFIED: SubscriptionTier
SUBSCRIPTION_TIER_FREE: SubscriptionTier
SUBSCRIPTION_TIER_STARTER: SubscriptionTier
SUBSCRIPTION_TIER_PRO: SubscriptionTier
SUBSCRIPTION_TIER_ENTERPRISE: SubscriptionTier
SUBSCRIPTION_STATUS_UNSPECIFIED: SubscriptionStatus
SUBSCRIPTION_STATUS_ACTIVE: SubscriptionStatus
SUBSCRIPTION_STATUS_CANCELLED: SubscriptionStatus
SUBSCRIPTION_STATUS_EXPIRED: SubscriptionStatus
SUBSCRIPTION_STATUS_TRIAL: SubscriptionStatus

class CreateSubscriptionRequest(_message.Message):
    __slots__ = ("user_id", "organization_id", "tier", "payment_method_id")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    PAYMENT_METHOD_ID_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    organization_id: str
    tier: SubscriptionTier
    payment_method_id: str
    def __init__(self, user_id: _Optional[str] = ..., organization_id: _Optional[str] = ..., tier: _Optional[_Union[SubscriptionTier, str]] = ..., payment_method_id: _Optional[str] = ...) -> None: ...

class GetSubscriptionRequest(_message.Message):
    __slots__ = ("subscription_id",)
    SUBSCRIPTION_ID_FIELD_NUMBER: _ClassVar[int]
    subscription_id: str
    def __init__(self, subscription_id: _Optional[str] = ...) -> None: ...

class UpdateSubscriptionRequest(_message.Message):
    __slots__ = ("subscription_id", "new_tier")
    SUBSCRIPTION_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_TIER_FIELD_NUMBER: _ClassVar[int]
    subscription_id: str
    new_tier: SubscriptionTier
    def __init__(self, subscription_id: _Optional[str] = ..., new_tier: _Optional[_Union[SubscriptionTier, str]] = ...) -> None: ...

class CancelSubscriptionRequest(_message.Message):
    __slots__ = ("subscription_id", "immediate", "reason")
    SUBSCRIPTION_ID_FIELD_NUMBER: _ClassVar[int]
    IMMEDIATE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    subscription_id: str
    immediate: bool
    reason: str
    def __init__(self, subscription_id: _Optional[str] = ..., immediate: bool = ..., reason: _Optional[str] = ...) -> None: ...

class CancelSubscriptionResponse(_message.Message):
    __slots__ = ("success", "ends_at")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ENDS_AT_FIELD_NUMBER: _ClassVar[int]
    success: bool
    ends_at: str
    def __init__(self, success: bool = ..., ends_at: _Optional[str] = ...) -> None: ...

class GetUsageRequest(_message.Message):
    __slots__ = ("organization_id", "start_date", "end_date")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    start_date: str
    end_date: str
    def __init__(self, organization_id: _Optional[str] = ..., start_date: _Optional[str] = ..., end_date: _Optional[str] = ...) -> None: ...

class ListInvoicesRequest(_message.Message):
    __slots__ = ("organization_id", "page")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    page: _pagination_pb2.PageRequest
    def __init__(self, organization_id: _Optional[str] = ..., page: _Optional[_Union[_pagination_pb2.PageRequest, _Mapping]] = ...) -> None: ...

class Subscription(_message.Message):
    __slots__ = ("id", "user_id", "organization_id", "tier", "status", "started_at", "ends_at", "cancelled_at", "monthly_price", "currency")
    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    TIER_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STARTED_AT_FIELD_NUMBER: _ClassVar[int]
    ENDS_AT_FIELD_NUMBER: _ClassVar[int]
    CANCELLED_AT_FIELD_NUMBER: _ClassVar[int]
    MONTHLY_PRICE_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    organization_id: str
    tier: SubscriptionTier
    status: SubscriptionStatus
    started_at: str
    ends_at: str
    cancelled_at: str
    monthly_price: float
    currency: str
    def __init__(self, id: _Optional[str] = ..., user_id: _Optional[str] = ..., organization_id: _Optional[str] = ..., tier: _Optional[_Union[SubscriptionTier, str]] = ..., status: _Optional[_Union[SubscriptionStatus, str]] = ..., started_at: _Optional[str] = ..., ends_at: _Optional[str] = ..., cancelled_at: _Optional[str] = ..., monthly_price: _Optional[float] = ..., currency: _Optional[str] = ...) -> None: ...

class UsageReport(_message.Message):
    __slots__ = ("organization_id", "api_calls", "memory_count", "storage_bytes", "cost", "period_start", "period_end")
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    API_CALLS_FIELD_NUMBER: _ClassVar[int]
    MEMORY_COUNT_FIELD_NUMBER: _ClassVar[int]
    STORAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    COST_FIELD_NUMBER: _ClassVar[int]
    PERIOD_START_FIELD_NUMBER: _ClassVar[int]
    PERIOD_END_FIELD_NUMBER: _ClassVar[int]
    organization_id: str
    api_calls: int
    memory_count: int
    storage_bytes: int
    cost: float
    period_start: str
    period_end: str
    def __init__(self, organization_id: _Optional[str] = ..., api_calls: _Optional[int] = ..., memory_count: _Optional[int] = ..., storage_bytes: _Optional[int] = ..., cost: _Optional[float] = ..., period_start: _Optional[str] = ..., period_end: _Optional[str] = ...) -> None: ...

class InvoiceList(_message.Message):
    __slots__ = ("invoices", "page_info")
    INVOICES_FIELD_NUMBER: _ClassVar[int]
    PAGE_INFO_FIELD_NUMBER: _ClassVar[int]
    invoices: _containers.RepeatedCompositeFieldContainer[Invoice]
    page_info: _pagination_pb2.PageInfo
    def __init__(self, invoices: _Optional[_Iterable[_Union[Invoice, _Mapping]]] = ..., page_info: _Optional[_Union[_pagination_pb2.PageInfo, _Mapping]] = ...) -> None: ...

class Invoice(_message.Message):
    __slots__ = ("id", "organization_id", "amount", "currency", "status", "due_date", "paid_at", "pdf_url")
    ID_FIELD_NUMBER: _ClassVar[int]
    ORGANIZATION_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DUE_DATE_FIELD_NUMBER: _ClassVar[int]
    PAID_AT_FIELD_NUMBER: _ClassVar[int]
    PDF_URL_FIELD_NUMBER: _ClassVar[int]
    id: str
    organization_id: str
    amount: float
    currency: str
    status: str
    due_date: str
    paid_at: str
    pdf_url: str
    def __init__(self, id: _Optional[str] = ..., organization_id: _Optional[str] = ..., amount: _Optional[float] = ..., currency: _Optional[str] = ..., status: _Optional[str] = ..., due_date: _Optional[str] = ..., paid_at: _Optional[str] = ..., pdf_url: _Optional[str] = ...) -> None: ...
