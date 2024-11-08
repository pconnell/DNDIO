from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class rollReply(_message.Message):
    __slots__ = ("roll_summary", "roll_total", "roll_total_modified", "user", "channel")
    ROLL_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    ROLL_TOTAL_FIELD_NUMBER: _ClassVar[int]
    ROLL_TOTAL_MODIFIED_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    roll_summary: str
    roll_total: int
    roll_total_modified: int
    user: str
    channel: str
    def __init__(self, roll_summary: _Optional[str] = ..., roll_total: _Optional[int] = ..., roll_total_modified: _Optional[int] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollAttackmsg(_message.Message):
    __slots__ = ("adv", "dadv", "weapon", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    WEAPON_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    weapon: str
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., weapon: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

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
    __slots__ = ("adv", "dadv", "spell", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    SPELL_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    spell: str
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., spell: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollAttackDamagemsg(_message.Message):
    __slots__ = ("adv", "dadv", "weapon", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    WEAPON_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    weapon: str
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., weapon: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollSpellDamagemsg(_message.Message):
    __slots__ = ("adv", "dadv", "spell", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    SPELL_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    spell: str
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., spell: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class rollSavemsg(_message.Message):
    __slots__ = ("adv", "dadv", "stat", "user", "channel")
    ADV_FIELD_NUMBER: _ClassVar[int]
    DADV_FIELD_NUMBER: _ClassVar[int]
    STAT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    adv: bool
    dadv: bool
    stat: str
    user: str
    channel: str
    def __init__(self, adv: bool = ..., dadv: bool = ..., stat: _Optional[str] = ..., user: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...
