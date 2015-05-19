#!/usr/bin/env python
#encoding=utf-8

import struct


class BytesReader(object):

    BIG_ENDIAN = 0
    LITTLE_ENDIAN = 1

    def __init__(self, endian):
        self._endian = endian

    def setEndian(self, endian):
        self._endian = endian

    def read_uint8(self):
        return struct.unpack("B", self._fp.read(1))[0]

    def read_uint16(self):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<H", self._fp.read(2))[0]
        else:
            return struct.unpack(">H", self._fp.read(2))[0]

    def read_uint32(self):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<I", self._fp.read(4))[0]
        else:
            return struct.unpack(">I", self._fp.read(4))[0]

    def read_uint64(self):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<Q", self._fp.read(8))[0]
        else:
            return struct.unpack(">Q", self._fp.read(8))[0]

    def read_int8(self):
        return struct.unpack("b", self._fp.read(1))[0]

    def read_int16(self):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<h", self._fp.read(2))[0]
        else:
            return struct.unpack(">h", self._fp.read(2))[0]

    def read_int32(self):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<i", self._fp.read(4))[0]
        else:
            return struct.unpack(">i", self._fp.read(4))[0]

    def read_int64(self):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<q", self._fp.read(8))[0]
        else:
            return struct.unpack(">q", self._fp.read(8))[0]

    def seek(self, offset, from_what=0):
        self._fp.seek(offset, from_what)

    def read_bytes(self, nbytes):
        return self._fp.read(nbytes)

    def bytes2uint16(self, bytes):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<H", bytes)[0]
        else:
            return struct.unpack(">H", bytes)[0]

    def bytes2uint32(self, bytes):
        if self._endian == BytesReader.LITTLE_ENDIAN:
            return struct.unpack("<I", bytes)[0]
        else:
            return struct.unpack(">I", bytes)[0]
