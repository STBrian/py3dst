# Copyright (C) 2025 STBrian
# This file is part of 'py3dst' and is licensed under the GPLv3.
# See <https://www.gnu.org/licenses/> for details.

import struct

from typing import BinaryIO

def read_uint32(fileBuffer: BinaryIO) -> int:
    return int(struct.unpack("<I", fileBuffer.read(4))[0])

def write_uint32(fileBuffer: BinaryIO, num: int) -> bool:
    bytes_write = fileBuffer.write(struct.pack("<I", num))
    if bytes_write == 4:
        return True
    else:
        return False