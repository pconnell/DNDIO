from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class setcharmsg(_message.Message):
    __slots__ = ("main_cmd", "child_cmd", "value")
    MAIN_CMD_FIELD_NUMBER: _ClassVar[int]
    CHILD_CMD_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    main_cmd: str
    child_cmd: str
    value: str
    def __init__(self, main_cmd: _Optional[str] = ..., child_cmd: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class setcharreply(_message.Message):
    __slots__ = ("response",)
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: str
    def __init__(self, response: _Optional[str] = ...) -> None: ...

class getcharmsg(_message.Message):
    __slots__ = ("main_cmd", "value")
    MAIN_CMD_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    main_cmd: str
    value: str
    def __init__(self, main_cmd: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class getcharreply(_message.Message):
    __slots__ = ("response",)
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    response: str
    def __init__(self, response: _Optional[str] = ...) -> None: ...
