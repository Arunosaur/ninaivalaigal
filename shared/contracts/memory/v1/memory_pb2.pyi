import datetime
from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class RememberRequest(_message.Message):
    __slots__ = ("user_id", "content", "context", "metadata")

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    content: str
    context: str
    metadata: _containers.ScalarMap[str, str]
    def __init__(
        self,
        user_id: _Optional[str] = ...,
        content: _Optional[str] = ...,
        context: _Optional[str] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class RememberResponse(_message.Message):
    __slots__ = ("memory_id", "status", "created_at")
    MEMORY_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    memory_id: str
    status: str
    created_at: _timestamp_pb2.Timestamp
    def __init__(
        self,
        memory_id: _Optional[str] = ...,
        status: _Optional[str] = ...,
        created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...,
    ) -> None: ...

class RecallRequest(_message.Message):
    __slots__ = ("user_id", "query", "limit", "threshold")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    THRESHOLD_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    query: str
    limit: int
    threshold: float
    def __init__(
        self,
        user_id: _Optional[str] = ...,
        query: _Optional[str] = ...,
        limit: _Optional[int] = ...,
        threshold: _Optional[float] = ...,
    ) -> None: ...

class RecallResponse(_message.Message):
    __slots__ = ("memories", "total_count")
    MEMORIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    memories: _containers.RepeatedCompositeFieldContainer[Memory]
    total_count: int
    def __init__(
        self, memories: _Optional[_Iterable[_Union[Memory, _Mapping]]] = ..., total_count: _Optional[int] = ...
    ) -> None: ...

class ListMemoriesRequest(_message.Message):
    __slots__ = ("user_id", "page", "page_size")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    page: int
    page_size: int
    def __init__(
        self, user_id: _Optional[str] = ..., page: _Optional[int] = ..., page_size: _Optional[int] = ...
    ) -> None: ...

class ListMemoriesResponse(_message.Message):
    __slots__ = ("memories", "total_count", "page", "page_size")
    MEMORIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_COUNT_FIELD_NUMBER: _ClassVar[int]
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    memories: _containers.RepeatedCompositeFieldContainer[Memory]
    total_count: int
    page: int
    page_size: int
    def __init__(
        self,
        memories: _Optional[_Iterable[_Union[Memory, _Mapping]]] = ...,
        total_count: _Optional[int] = ...,
        page: _Optional[int] = ...,
        page_size: _Optional[int] = ...,
    ) -> None: ...

class Memory(_message.Message):
    __slots__ = ("id", "user_id", "content", "context", "metadata", "created_at", "updated_at", "relevance_score")

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    ID_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    RELEVANCE_SCORE_FIELD_NUMBER: _ClassVar[int]
    id: str
    user_id: str
    content: str
    context: str
    metadata: _containers.ScalarMap[str, str]
    created_at: _timestamp_pb2.Timestamp
    updated_at: _timestamp_pb2.Timestamp
    relevance_score: float
    def __init__(
        self,
        id: _Optional[str] = ...,
        user_id: _Optional[str] = ...,
        content: _Optional[str] = ...,
        context: _Optional[str] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
        created_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...,
        updated_at: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...,
        relevance_score: _Optional[float] = ...,
    ) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "version", "timestamp")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    status: str
    version: str
    timestamp: _timestamp_pb2.Timestamp
    def __init__(
        self,
        status: _Optional[str] = ...,
        version: _Optional[str] = ...,
        timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...,
    ) -> None: ...
