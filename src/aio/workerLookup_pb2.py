# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: workerLookup.proto
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
    'workerLookup.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x10workerLookup.proto\"\x1f\n\x03msg\x12\x0b\n\x03\x63md\x18\x01 \x01(\t\x12\x0b\n\x03num\x18\x02 \x01(\x05\"-\n\x08msgreply\x12\x10\n\x08response\x18\x01 \x01(\t\x12\x0f\n\x07outcome\x18\x02 \x01(\x08\x32\'\n\x07sendmsg\x12\x1c\n\x07sendmsg\x12\x04.msg\x1a\t.msgreply\"\x00\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'workerLookup_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MSG']._serialized_start=20
  _globals['_MSG']._serialized_end=51
  _globals['_MSGREPLY']._serialized_start=53
  _globals['_MSGREPLY']._serialized_end=98
  _globals['_SENDMSG']._serialized_start=100
  _globals['_SENDMSG']._serialized_end=139
# @@protoc_insertion_point(module_scope)
