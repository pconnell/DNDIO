# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: dndio.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'dndio.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0b\x64ndio.proto\"W\n\x08\x64ndiomsg\x12\x0b\n\x03\x63md\x18\x01 \x01(\t\x12\x0e\n\x06subcmd\x18\x02 \x01(\t\x12\x0c\n\x04\x61rgs\x18\x03 \x01(\t\x12\x12\n\ndc_channel\x18\x04 \x01(\t\x12\x0c\n\x04user\x18\x05 \x01(\t\"S\n\ndndioreply\x12\x10\n\x08orig_cmd\x18\x01 \x01(\t\x12\x0e\n\x06status\x18\x02 \x01(\x08\x12\x12\n\ndc_channel\x18\x03 \x01(\t\x12\x0f\n\x07\x64\x63_user\x18\x04 \x01(\t\"X\n\tcharreply\x12\x1b\n\x06\x63ommon\x18\x01 \x01(\x0b\x32\x0b.dndioreply\x12\x0f\n\x07\x63olumns\x18\x05 \x03(\t\x12\r\n\x05\x64type\x18\x06 \x03(\t\x12\x0e\n\x06values\x18\x07 \x03(\t\"Z\n\x0blookupreply\x12\x1b\n\x06\x63ommon\x18\x01 \x01(\x0b\x32\x0b.dndioreply\x12\x0f\n\x07\x63olumns\x18\x05 \x03(\t\x12\r\n\x05\x64type\x18\x06 \x03(\t\x12\x0e\n\x06values\x18\x07 \x03(\t\"u\n\trollreply\x12\x1b\n\x06\x63ommon\x18\x01 \x01(\x0b\x32\x0b.dndioreply\x12\x12\n\nroll_unmod\x18\x05 \x03(\x05\x12\x11\n\tmodifiers\x18\x06 \x01(\t\x12\x10\n\x08roll_mod\x18\x07 \x03(\x05\x12\x12\n\nroll_total\x18\x08 \x01(\x05\"(\n\tinitreply\x12\x1b\n\x06\x63ommon\x18\x01 \x01(\x0b\x32\x0b.dndioreply2(\n\x07rollSvc\x12\x1d\n\x04roll\x12\t.dndiomsg\x1a\n.rollreply2(\n\x07\x63harSvc\x12\x1d\n\x04\x63har\x12\t.dndiomsg\x1a\n.charreply2.\n\tlookupSvc\x12!\n\x06lookup\x12\t.dndiomsg\x1a\x0c.lookupreply2(\n\x07initSvc\x12\x1d\n\x04init\x12\t.dndiomsg\x1a\n.initreplyb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'dndio_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_DNDIOMSG']._serialized_start=15
  _globals['_DNDIOMSG']._serialized_end=102
  _globals['_DNDIOREPLY']._serialized_start=104
  _globals['_DNDIOREPLY']._serialized_end=187
  _globals['_CHARREPLY']._serialized_start=189
  _globals['_CHARREPLY']._serialized_end=277
  _globals['_LOOKUPREPLY']._serialized_start=279
  _globals['_LOOKUPREPLY']._serialized_end=369
  _globals['_ROLLREPLY']._serialized_start=371
  _globals['_ROLLREPLY']._serialized_end=488
  _globals['_INITREPLY']._serialized_start=490
  _globals['_INITREPLY']._serialized_end=530
  _globals['_ROLLSVC']._serialized_start=532
  _globals['_ROLLSVC']._serialized_end=572
  _globals['_CHARSVC']._serialized_start=574
  _globals['_CHARSVC']._serialized_end=614
  _globals['_LOOKUPSVC']._serialized_start=616
  _globals['_LOOKUPSVC']._serialized_end=662
  _globals['_INITSVC']._serialized_start=664
  _globals['_INITSVC']._serialized_end=704
# @@protoc_insertion_point(module_scope)
