import dndio_pb2

x = dndio_pb2.dndioreply(
    orig_cmd='/roll attack sword',
    status = True,
    dc_channel = 'DNDIO',
    dc_user = 'Chorky#8402'
)

#initiative rolled with advantage
roll1 = dndio_pb2.roll(
    roll_type = 'initiative',
    die_rolls = [14,6],
    modifiers = [3],
    modified_rolls = [17,9],
    total = 17
)

#attack roll with disadvantage
roll2 = dndio_pb2.roll(
    roll_type='attack',
    die_rolls=[20,5],
    modifiers = [3],
    modified_rolls = [23,8],
    total = 8
)

reply = dndio_pb2.rollreply(
    common = x,
    dierolls = [roll1,roll2]
)

print(reply)

#build a reply for a lookup message for weapons...
## all of this would be coded by the lookup worker before piping out a reply
c = ["Name","type","modifiers","damage"],
dtypes = [dndio_pb2.dtype.STR,dndio_pb2.dtype.STR,dndio_pb2.dtype.ARR,dndio_pb2.dtype.JSON]
values = [
    dndio_pb2.lookupvalues(values=["sword","greataxe"]),
    dndio_pb2.lookupvalues(values=['melee','melee']),
    dndio_pb2.lookupvalues(values=["['STR','DEX']","['STR']"]),
    dndio_pb2.lookupvalues(values=["{'1hnd':{'slashing':{'1':6}}}","{'1hnd':{'slashing':{'1':8}}}"])
]
print(type([i for i in c]))
lookup = dndio_pb2.lookupreply(
    common=x,
    columns=["Name","type","modifiers","damage"],
    dtypes=dtypes,
    values=values
)
print(lookup)

