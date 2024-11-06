from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class lookupmsg(_message.Message):
    __slots__ = ("cmd", "value", "user", "channel")
    CMD_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    cmd: str
    value: str
    user: str
    channel: str
    def __init__(self, cmd: _Optional[str] = ..., value: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class lookupReply(_message.Message):
    __slots__ = ("response", "user", "channel")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    response: str
    user: str
    channel: str
    def __init__(self, response: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...
