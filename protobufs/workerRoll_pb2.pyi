from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class rollReply(_message.Message):
    __slots__ = ("dice", "mod_dice", "roll_sum", "user", "channel")
    DICE_FIELD_NUMBER: _ClassVar[int]
    MOD_DICE_FIELD_NUMBER: _ClassVar[int]
    ROLL_SUM_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    dice: _containers.RepeatedScalarFieldContainer[int]
    mod_dice: _containers.RepeatedScalarFieldContainer[int]
    roll_sum: int
    user: str
    channel: str
    def __init__(self, dice: _Optional[_Iterable[int]] = ..., mod_dice: _Optional[_Iterable[int]] = ..., roll_sum: _Optional[int] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollAttackmsg(_message.Message):
    __slots__ = ("adv", "dadv", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollIniativemsg(_message.Message):
    __slots__ = ("adv", "dadv", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollSpellcastmsg(_message.Message):
    __slots__ = ("adv", "dadv", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollDamagemsg(_message.Message):
    __slots__ = ("adv", "dadv", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollSavemsg(_message.Message):
    __slots__ = ("adv", "dadv", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...
