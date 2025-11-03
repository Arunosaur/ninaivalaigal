from typing import ClassVar as _ClassVar
from typing import Optional as _Optional

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

DESCRIPTOR: _descriptor.FileDescriptor

class PageRequest(_message.Message):
    __slots__ = ("page", "page_size", "sort_by", "sort_order")
    PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    SORT_BY_FIELD_NUMBER: _ClassVar[int]
    SORT_ORDER_FIELD_NUMBER: _ClassVar[int]
    page: int
    page_size: int
    sort_by: str
    sort_order: str
    def __init__(
        self,
        page: _Optional[int] = ...,
        page_size: _Optional[int] = ...,
        sort_by: _Optional[str] = ...,
        sort_order: _Optional[str] = ...,
    ) -> None: ...

class PageInfo(_message.Message):
    __slots__ = ("total", "pages", "current_page", "page_size", "has_next", "has_previous")
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    PAGES_FIELD_NUMBER: _ClassVar[int]
    CURRENT_PAGE_FIELD_NUMBER: _ClassVar[int]
    PAGE_SIZE_FIELD_NUMBER: _ClassVar[int]
    HAS_NEXT_FIELD_NUMBER: _ClassVar[int]
    HAS_PREVIOUS_FIELD_NUMBER: _ClassVar[int]
    total: int
    pages: int
    current_page: int
    page_size: int
    has_next: bool
    has_previous: bool
    def __init__(
        self,
        total: _Optional[int] = ...,
        pages: _Optional[int] = ...,
        current_page: _Optional[int] = ...,
        page_size: _Optional[int] = ...,
        has_next: bool = ...,
        has_previous: bool = ...,
    ) -> None: ...

class CursorRequest(_message.Message):
    __slots__ = ("cursor", "limit")
    CURSOR_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    cursor: str
    limit: int
    def __init__(self, cursor: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class CursorInfo(_message.Message):
    __slots__ = ("next_cursor", "previous_cursor", "has_more")
    NEXT_CURSOR_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_CURSOR_FIELD_NUMBER: _ClassVar[int]
    HAS_MORE_FIELD_NUMBER: _ClassVar[int]
    next_cursor: str
    previous_cursor: str
    has_more: bool
    def __init__(
        self, next_cursor: _Optional[str] = ..., previous_cursor: _Optional[str] = ..., has_more: bool = ...
    ) -> None: ...
