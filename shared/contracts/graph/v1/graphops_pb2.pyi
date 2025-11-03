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

class ExecuteQueryRequest(_message.Message):
    __slots__ = ("query", "parameters", "user_id", "timeout_ms")

    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    QUERY_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    query: str
    parameters: _containers.ScalarMap[str, str]
    user_id: str
    timeout_ms: int
    def __init__(
        self,
        query: _Optional[str] = ...,
        parameters: _Optional[_Mapping[str, str]] = ...,
        user_id: _Optional[str] = ...,
        timeout_ms: _Optional[int] = ...,
    ) -> None: ...

class ExecuteQueryResponse(_message.Message):
    __slots__ = ("results", "metadata", "status")
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[QueryResult]
    metadata: QueryMetadata
    status: str
    def __init__(
        self,
        results: _Optional[_Iterable[_Union[QueryResult, _Mapping]]] = ...,
        metadata: _Optional[_Union[QueryMetadata, _Mapping]] = ...,
        status: _Optional[str] = ...,
    ) -> None: ...

class QueryResult(_message.Message):
    __slots__ = ("columns", "rows")
    COLUMNS_FIELD_NUMBER: _ClassVar[int]
    ROWS_FIELD_NUMBER: _ClassVar[int]
    columns: _containers.RepeatedCompositeFieldContainer[QueryColumn]
    rows: _containers.RepeatedCompositeFieldContainer[QueryRow]
    def __init__(
        self,
        columns: _Optional[_Iterable[_Union[QueryColumn, _Mapping]]] = ...,
        rows: _Optional[_Iterable[_Union[QueryRow, _Mapping]]] = ...,
    ) -> None: ...

class QueryColumn(_message.Message):
    __slots__ = ("name", "type")
    NAME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    name: str
    type: str
    def __init__(self, name: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class QueryRow(_message.Message):
    __slots__ = ("values",)
    VALUES_FIELD_NUMBER: _ClassVar[int]
    values: _containers.RepeatedCompositeFieldContainer[QueryValue]
    def __init__(self, values: _Optional[_Iterable[_Union[QueryValue, _Mapping]]] = ...) -> None: ...

class QueryValue(_message.Message):
    __slots__ = ("string_value", "int_value", "double_value", "bool_value", "json_value")
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    JSON_VALUE_FIELD_NUMBER: _ClassVar[int]
    string_value: str
    int_value: int
    double_value: float
    bool_value: bool
    json_value: bytes
    def __init__(
        self,
        string_value: _Optional[str] = ...,
        int_value: _Optional[int] = ...,
        double_value: _Optional[float] = ...,
        bool_value: bool = ...,
        json_value: _Optional[bytes] = ...,
    ) -> None: ...

class QueryMetadata(_message.Message):
    __slots__ = ("rows_affected", "execution_time_ms", "query_plan", "warnings")
    ROWS_AFFECTED_FIELD_NUMBER: _ClassVar[int]
    EXECUTION_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    QUERY_PLAN_FIELD_NUMBER: _ClassVar[int]
    WARNINGS_FIELD_NUMBER: _ClassVar[int]
    rows_affected: int
    execution_time_ms: int
    query_plan: str
    warnings: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        rows_affected: _Optional[int] = ...,
        execution_time_ms: _Optional[int] = ...,
        query_plan: _Optional[str] = ...,
        warnings: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ExecuteTransactionRequest(_message.Message):
    __slots__ = ("queries", "parameters", "user_id", "timeout_ms")

    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

    QUERIES_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_MS_FIELD_NUMBER: _ClassVar[int]
    queries: _containers.RepeatedScalarFieldContainer[str]
    parameters: _containers.ScalarMap[str, str]
    user_id: str
    timeout_ms: int
    def __init__(
        self,
        queries: _Optional[_Iterable[str]] = ...,
        parameters: _Optional[_Mapping[str, str]] = ...,
        user_id: _Optional[str] = ...,
        timeout_ms: _Optional[int] = ...,
    ) -> None: ...

class ExecuteTransactionResponse(_message.Message):
    __slots__ = ("results", "metadata", "status")
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[QueryResult]
    metadata: TransactionMetadata
    status: str
    def __init__(
        self,
        results: _Optional[_Iterable[_Union[QueryResult, _Mapping]]] = ...,
        metadata: _Optional[_Union[TransactionMetadata, _Mapping]] = ...,
        status: _Optional[str] = ...,
    ) -> None: ...

class TransactionMetadata(_message.Message):
    __slots__ = ("total_queries", "successful_queries", "total_execution_time_ms", "committed")
    TOTAL_QUERIES_FIELD_NUMBER: _ClassVar[int]
    SUCCESSFUL_QUERIES_FIELD_NUMBER: _ClassVar[int]
    TOTAL_EXECUTION_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    COMMITTED_FIELD_NUMBER: _ClassVar[int]
    total_queries: int
    successful_queries: int
    total_execution_time_ms: int
    committed: bool
    def __init__(
        self,
        total_queries: _Optional[int] = ...,
        successful_queries: _Optional[int] = ...,
        total_execution_time_ms: _Optional[int] = ...,
        committed: bool = ...,
    ) -> None: ...

class GetGraphStatsRequest(_message.Message):
    __slots__ = ("graph_name",)
    GRAPH_NAME_FIELD_NUMBER: _ClassVar[int]
    graph_name: str
    def __init__(self, graph_name: _Optional[str] = ...) -> None: ...

class GetGraphStatsResponse(_message.Message):
    __slots__ = ("stats",)
    STATS_FIELD_NUMBER: _ClassVar[int]
    stats: GraphStats
    def __init__(self, stats: _Optional[_Union[GraphStats, _Mapping]] = ...) -> None: ...

class GraphStats(_message.Message):
    __slots__ = ("node_count", "edge_count", "node_labels", "edge_labels", "last_updated")
    NODE_COUNT_FIELD_NUMBER: _ClassVar[int]
    EDGE_COUNT_FIELD_NUMBER: _ClassVar[int]
    NODE_LABELS_FIELD_NUMBER: _ClassVar[int]
    EDGE_LABELS_FIELD_NUMBER: _ClassVar[int]
    LAST_UPDATED_FIELD_NUMBER: _ClassVar[int]
    node_count: int
    edge_count: int
    node_labels: _containers.RepeatedCompositeFieldContainer[LabelStats]
    edge_labels: _containers.RepeatedCompositeFieldContainer[LabelStats]
    last_updated: _timestamp_pb2.Timestamp
    def __init__(
        self,
        node_count: _Optional[int] = ...,
        edge_count: _Optional[int] = ...,
        node_labels: _Optional[_Iterable[_Union[LabelStats, _Mapping]]] = ...,
        edge_labels: _Optional[_Iterable[_Union[LabelStats, _Mapping]]] = ...,
        last_updated: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...,
    ) -> None: ...

class LabelStats(_message.Message):
    __slots__ = ("label", "count")
    LABEL_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    label: str
    count: int
    def __init__(self, label: _Optional[str] = ..., count: _Optional[int] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "version", "timestamp", "database")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DATABASE_FIELD_NUMBER: _ClassVar[int]
    status: str
    version: str
    timestamp: _timestamp_pb2.Timestamp
    database: ConnectionStatus
    def __init__(
        self,
        status: _Optional[str] = ...,
        version: _Optional[str] = ...,
        timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ...,
        database: _Optional[_Union[ConnectionStatus, _Mapping]] = ...,
    ) -> None: ...

class ConnectionStatus(_message.Message):
    __slots__ = ("connected", "active_connections", "idle_connections", "max_connections")
    CONNECTED_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    IDLE_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    MAX_CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    connected: bool
    active_connections: int
    idle_connections: int
    max_connections: int
    def __init__(
        self,
        connected: bool = ...,
        active_connections: _Optional[int] = ...,
        idle_connections: _Optional[int] = ...,
        max_connections: _Optional[int] = ...,
    ) -> None: ...
