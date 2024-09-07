import struct

from numpy import uint32
from typing import BinaryIO

def read_bytes(fileBuffer: BinaryIO, n) -> bytes:
    bytesStringRead = b''
    for i in range(n):
        bytesStringRead += fileBuffer.read(1)
    return bytesStringRead

def read_string(fileBuffer: BinaryIO) -> bytes:
    stringRead = b''
    byteRead = fileBuffer.read(1)
    while byteRead and byteRead != b'\x00':
        stringRead += byteRead
        byteRead = fileBuffer.read(1)
    return stringRead

def read_uint32(fileBuffer: BinaryIO) -> uint32:
    return uint32(struct.unpack("<I", fileBuffer.read(4))[0])