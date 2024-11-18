from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class msg(_message.Message):
    __slots__ = ("cmd", "num")
    CMD_FIELD_NUMBER: _ClassVar[int]
    NUM_FIELD_NUMBER: _ClassVar[int]
    cmd: str
    num: int
    def __init__(self, cmd: _Optional[str] = ..., num: _Optional[int] = ...) -> None: ...

class msgreply(_message.Message):
    __slots__ = ("response", "outcome")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    response: str
    outcome: bool
    def __init__(self, response: _Optional[str] = ..., outcome: bool = ...) -> None: ...
