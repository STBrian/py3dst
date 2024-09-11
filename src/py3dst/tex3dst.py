import math
import numpy
from PIL import Image
from pathlib import Path

from dataclasses import dataclass, field
from typing import BinaryIO, Tuple, List, Union

from .primitive_types import read_uint32, write_uint32
from .utils import isPowerOfTwo, getClosestPowerOfTwo, maxIntBits
from .error_classes import *

@dataclass
class _headerTexture3dst:
    mode: int = 0
    format: int = 0
    full_size: List[int] = field(default_factory=lambda: [0, 0]) # Texture real full size
    size: List[int] = field(default_factory=lambda: [0, 0]) # Texture size
    mip_level: int = 0

def _readTexture3dstHeader(fileBuffer: BinaryIO, headerDst: _headerTexture3dst):
    headerDst.mode = read_uint32(fileBuffer)
    headerDst.format = read_uint32(fileBuffer)
    headerDst.full_size[0] = read_uint32(fileBuffer) # real full width
    headerDst.full_size[1] = read_uint32(fileBuffer) # real full height
    headerDst.size[0] = read_uint32(fileBuffer) # width
    headerDst.size[1] = read_uint32(fileBuffer) # height
    headerDst.mip_level = read_uint32(fileBuffer)

def _isMipLevelValid(width, height, mip_level) -> bool:
    num1 = int(math.log2(width)) # Times that can be divided by 2
    num2 = int(math.log2(height))
    return mip_level <= num1 and mip_level <= num2

def _getTexturePosition(x: int, y: int, width: int) -> Tuple[int]:
        dst_pos = ((((y >> 3) * (width >> 3) + (x >> 3)) << 6) + ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3)))
        y2 = (dst_pos//width)
        x2 = dst_pos - (y2*width)
        return (x2, y2)

def _checkListType(obj: list | tuple, istype):
    for element in obj:
        if not isinstance(element, istype):
            return False
    return True

def _checkListRange(obj: list | tuple, min: int, max: int):
    for element in obj:
        if element < min or element > max:
            return False
    return True

def _createPixelDataStructure(width: int, height: int) -> List[List[int]]:
    list_structure = [[] for _ in range(height)]
    for element in list_structure:
        for _ in range(width):
            element.append(bytes([0]))
    return list_structure

def _matrixToLinear(obj: List[List[bytes]]) -> List[bytes]:
    linear = []
    for element in obj:
        for value in element:
            linear.append(value)
    return linear

def _joinBytesList(obj: List[bytes]) -> bytearray:
    array = bytearray()
    for value in obj:
        array.extend(value)
    return array

def _matrixToBytearray(obj: List[List[bytes]]):
    return _joinBytesList(_matrixToLinear(obj))

class Texture3dst:
    header: _headerTexture3dst
    size: List[int]
    textureData: List[List[bytes]]
    FORMATS = (("rgba8", True, 4, 4),
               ("rgb8", True, 3, 3),
               ("rgba5551", True, 2, 4),
               ("rgb565", True, 2, 3),
               ("rgba4", True, 2, 4),
               ("la8", True, 2, 2),
               ("hilo8", False, 2, 2),
               ("l8", False, 1, 1),
               ("a8", False, 1, 1),
               ("la4", True, 1, 2))

    def _matchFormat(self, format: str) -> int:
        for i, value in enumerate(self.FORMATS):
            if value[0] == format:
                return i
        return None
    
    def _getFormatInfo(self, format: int) -> dict:
        if not isinstance(format, int):
            raise TypeError(genericTypeErrorMessage("format", format, int))
        
        if format < 0 or format >= len(self.FORMATS):
            return None
        
        format_info = {}
        format_info["name"] = self.FORMATS[format][0]
        format_info["supported"] = self.FORMATS[format][1]
        format_info["pixel_lenght"] = self.FORMATS[format][2]
        format_info["pixel_channels"] = self.FORMATS[format][3]
        return format_info

    def _convertPixelDataToBytes(self, pixel_data: List[int] | Tuple[int]) -> bytes:
        if not isinstance(pixel_data, list) and not isinstance(pixel_data, tuple):
            raise TypeError(genericTypeErrorMessage("pixel_data", pixel_data, Union[list, tuple]))
        
        # Validate values
        format = self.header.format
        if format < 0 or format >= len(self.FORMATS):
            raise ValueError(f"Unexpected 'format' value: {format}")
        
        format_info = self._getFormatInfo(format)
        if not format_info["supported"]:
            raise Texture3dstUnsupported(f"'format' is unsupported: {format}, {format_info['name']}")
        
        if not _checkListType(pixel_data, int):
            raise TypeError("'pixel_data' must only contain int values")
        
        if len(pixel_data) > format_info["pixel_channels"]:
            raise ValueError(f"Too many values ({len(pixel_data)}) in 'pixel_data' for format: {format}, {format_info['name']}")
        elif len(pixel_data) < format_info["pixel_channels"]:
            raise ValueError(f"Too few values ({len(pixel_data)}) in 'pixel_data' for format: {format}, {format_info['name']}")
        
        if not _checkListRange(pixel_data, 0, 255):
            raise ValueError("'pixel_data' values must be between 0 to 255")

        match format:
            case 0: # rgba8
                r = pixel_data[0]
                g = pixel_data[1]
                b = pixel_data[2]
                a = pixel_data[3]
                combined = (r << 24) | (g << 16) | (b << 8) | a
            case 1: # rgb8
                r = pixel_data[0]
                g = pixel_data[1]
                b = pixel_data[2]
                combined = (r << 16) | (g << 8) | b
            case 2: # rgba5551
                r = int(pixel_data[0] / 0xFF * maxIntBits(5))
                g = int(pixel_data[1] / 0xFF * maxIntBits(5))
                b = int(pixel_data[2] / 0xFF * maxIntBits(5))
                a = 1 if pixel_data[3] > 127 else 0
                combined = (r << 11) | (g << 6) | (b << 1) | a
            case 3: # rgb565
                r = int(pixel_data[0] / 0xFF * maxIntBits(5))
                g = int(pixel_data[1] / 0xFF * maxIntBits(6))
                b = int(pixel_data[2] / 0xFF * maxIntBits(5))
                combined = (r << 11) | (g << 5) | b
            case 4: # rgba4
                r = int(pixel_data[0] / 0xFF * maxIntBits(4))
                g = int(pixel_data[1] / 0xFF * maxIntBits(4))
                b = int(pixel_data[2] / 0xFF * maxIntBits(4))
                a = int(pixel_data[3] / 0xFF * maxIntBits(4))
                combined = (r << 12) | (g << 8) | (b << 4) | a
            case 5: # la8
                l = pixel_data[0]
                a = pixel_data[1]
                combined = (l << 8) | a
            case 9: # la4
                l = int((pixel_data[0] / 0xFF) * maxIntBits(4))
                a = int((pixel_data[1] / 0xFF) * maxIntBits(4))
                combined = (l << 4) | a
            case _:
                raise ValueError("Texture 'format' value invalid")
        return combined.to_bytes(format_info["pixel_lenght"], "little", signed=False)

    def _convertBytesToPixelData(self, pixel_bytes: bytes) -> Tuple[int]:
        if not isinstance(pixel_bytes, bytes):
            raise TypeError(genericTypeErrorMessage("pixel_bytes", pixel_bytes, bytes))
        
        # Validate values
        format = self.header.format
        if format < 0 or format >= len(self.FORMATS):
            raise ValueError(f"Unexpected 'format' value: {format}")
        
        format_info = self._getFormatInfo(format)
        if not format_info["supported"]:
            raise Texture3dstUnsupported(f"'format' is unsupported: {format}, {format_info['name']}")
        
        pixel_value = int.from_bytes(pixel_bytes, "little", signed=False)

        match format:
            case 0: # rgba8
                r = (pixel_value >> 24) & 0xFF
                g = (pixel_value >> 16) & 0xFF
                b = (pixel_value >> 8) & 0xFF
                a = pixel_value & 0xFF
                combined = (r, g, b, a)
            case 1: # rgb8
                r = (pixel_value >> 16) & 0xFF
                g = (pixel_value >> 8) & 0xFF
                b = pixel_value & 0xFF
                combined = (r, g, b)
            case 2: # rgba5551
                r = int(((pixel_value >> 11) & 0b11111) / maxIntBits(5) * 0xFF)
                g = int(((pixel_value >> 6) & 0b11111) / maxIntBits(5) * 0xFF)
                b = int(((pixel_value >> 1) & 0b11111) / maxIntBits(5) * 0xFF)
                a = (pixel_value & 0b1) * 0xFF
                combined = (r, g, b, a)
            case 3: # rgb565
                r = int(((pixel_value >> 11) & 0b11111) / maxIntBits(5) * 0xFF)
                g = int(((pixel_value >> 5) & 0b111111) / maxIntBits(6) * 0xFF)
                b = int((pixel_value & 0b11111) / maxIntBits(5) * 0xFF)
                combined = (r, g, b)
            case 4: # rgba4
                r = int(((pixel_value >> 12) & 0xF) / 0xF * 0xFF)
                g = int(((pixel_value >> 8) & 0xF) / 0xF * 0xFF)
                b = int(((pixel_value >> 4) & 0xF) / 0xF * 0xFF)
                a = int((pixel_value & 0xF) / 0xF * 0xFF)
                combined = (r, g, b, a)
            case 5: # la8
                l = (pixel_value >> 8) & 0xFF
                a = pixel_value & 0xFF
                combined = (l, a)
            case 9: # la4
                l = int(((pixel_value >> 4) & 0xF) / 0xF * 0xFF)
                a = int((pixel_value & 0xF) / 0xF * 0xFF)
                combined = (l, a)
            case _:
                raise ValueError("Texture 'format' value invalid")
        return combined

    def open(self, path: str | Path):
        # Validate types
        if  not isinstance(path, str) and not isinstance(path, Path):
            raise TypeError(genericTypeErrorMessage("path", path, Union[str, Path]))
        
        # File from the texture will be loaded
        textureFileBuffer = open(path, "rb")
        
        # File signature
        if textureFileBuffer.read(4) != b'3DST':
            raise Texture3dstNoSignature()
        
        # Header of the file
        self.header = _headerTexture3dst()
        _readTexture3dstHeader(textureFileBuffer, self.header)
        
        # Only mode 3 is supported
        if self.header.mode != 3:
            raise Texture3dstUnsupported(f"Unsupported mode: {self.header.mode}")
        
        # Get format info and support
        format = self.header.format
        format_info = self._getFormatInfo(format)
        if format_info == None:
            raise Texture3dstUnsupported(f"Texture format unsupported: {format}")
        elif not format_info["supported"]:
            raise Texture3dstUnsupported(f"Texture format unsupported: {format}, '{format_info['name']}'")

        # Full dimensions must be a power of 2
        full_width = self.header.full_size[0]
        full_height = self.header.full_size[1]
        if not isPowerOfTwo(full_width):
            raise ValueError(f"Texture full width is not power of 2: {full_width}")
        if not isPowerOfTwo(full_height):
            raise ValueError(f"Texture full height is not power of 2: {full_height}")

        # Verify mip level
        mip_level = self.header.mip_level
        if mip_level <= 0:
            raise ValueError("Mip level must be greater than 0")
        if not _isMipLevelValid(full_width, full_height, mip_level):
            raise Texture3dstException("Mip level' value greater than supported")

        # Save size
        self.size = (int(self.header.size[0]), int(self.header.size[1]))

        unarranged_texture_data = _createPixelDataStructure(full_width, full_height)
        # Gets all pixel data from file
        for i in range(full_height):
            for j in range(full_width):
                pixel_read = textureFileBuffer.read(format_info["pixel_lenght"])
                unarranged_texture_data[i][j] = pixel_read

        textureFileBuffer.close()

        self.textureData = _createPixelDataStructure(full_width, full_height)
        # Arrange pixel data in place
        for i in range(full_height):
            for j in range(full_width):
                dst_pos = _getTexturePosition(j, i, full_width)
                self.textureData[i][j] = unarranged_texture_data[dst_pos[1]][dst_pos[0]]

        # All textures are upside down by default
        self.flipVertical()
        return self

    def new(self, width: int, height: int, mip_level: int = 1, format: str = "rgba8"):
        # Validate types
        if not isinstance(width, int):
            raise TypeError(genericTypeErrorMessage("width", width, int))
        if not isinstance(height, int):
            raise TypeError(genericTypeErrorMessage("height", height, int))
        if not isinstance(mip_level, int):
            raise TypeError(genericTypeErrorMessage("miplevel", mip_level, int))
        if not isinstance(format, str):
            raise TypeError(genericTypeErrorMessage("format", format, str))
        
        # Validate values
        if width <= 0:
            raise ValueError("'width' must be greater than 0")
        if height <= 0:
            raise ValueError("'height' must be greater than 0")
        
        # Calculate real full size
        full_width = getClosestPowerOfTwo(width)
        full_height = getClosestPowerOfTwo(height)

        # Verify mip level
        if mip_level <= 0:
            raise ValueError("'mip_level' must be greater than 0")
        if not _isMipLevelValid(full_width, full_height, mip_level):
            raise Texture3dstException("'mip_level' value greater than supported")
        
        # Verify format and support
        format_match = self._matchFormat(format.lower())
        if format_match != None:
            format_info = self._getFormatInfo(format_match)
            if not format_info["supported"]:
                raise Texture3dstUnsupported(f"Texture format unsupported: {format}, '{format_info['name']}'")
        else:
            raise ValueError(f"Texture format invalid: {format}")
        
        self.header = _headerTexture3dst()
        self.header.mode = 3
        self.header.format = format_match
        self.header.full_size[0] = full_width
        self.header.full_size[1] = full_height
        self.header.size[0] = width
        self.header.size[1] = height
        self.header.mip_level = mip_level

        self.size = (width, height)

        # Creates empty structure for pixel data
        self.textureData = _createPixelDataStructure(full_width, full_height)
        return self

    def setPixel(self, x: int, y: int, pixel_data: Tuple[int] | List[int]) -> None:
        if not isinstance(x, int):
            raise TypeError(genericTypeErrorMessage("x", x, int))
        if not isinstance(y, int):
            raise TypeError(genericTypeErrorMessage("y", y, int))
        if not isinstance(pixel_data, tuple) and not isinstance(pixel_data, list):
            raise TypeError(genericTypeErrorMessage("pixel_data", pixel_data, Union[list, tuple]))
        for num in pixel_data:
            if not isinstance(num, int):
                raise ValueError("'pixel_data' values must be only int types")
        
        # Validate values
        if x < 0 or x >= self.size[0]:
            raise ValueError("x coordinates out of range")
        if y < 0 or y >= self.size[1]:
            raise ValueError("y coordinates out of range")
        
        format = self.header.format
        format_info = self._getFormatInfo(format)
        if len(pixel_data) > format_info["pixel_channels"]:
            raise ValueError(f"Too many values ({len(pixel_data)}) in 'pixel_data' for format: {format}, {format_info['name']}")
        elif len(pixel_data) < format_info["pixel_channels"]:
            raise ValueError(f"Too few values ({len(pixel_data)}) in 'pixel_data' for format: {format}, {format_info['name']}")
        
        for num in pixel_data:
            if num < 0 or num > 255:
                raise ValueError("'pixel_data' values must be between 0 and 255")        
        
        self.textureData[y][x] = self._convertPixelDataToBytes(pixel_data)
        return

    def getPixel(self, x: int, y: int) -> Tuple[int]:
        if not isinstance(x, int):
            raise TypeError(genericTypeErrorMessage("x", x, int))
        if not isinstance(y, int):
            raise TypeError(genericTypeErrorMessage("y", y, int))

        # Validate values
        if x < 0 or x >= self.size[0]:
            raise ValueError("x coordinates out of range")
        if y < 0 or y >= self.size[1]:
            raise ValueError("y coordinates out of range")
        
        return self._convertBytesToPixelData(self.textureData[y][x])
    
    def copy(self, x1: int, y1: int, x2: int, y2: int) -> Image.Image:
        if not isinstance(x1, int):
            raise TypeError(genericTypeErrorMessage("x1", x1, int))
        if not isinstance(y1, int):
            raise TypeError(genericTypeErrorMessage("y1", y1, int))
        if not isinstance(x2, int):
            raise TypeError(genericTypeErrorMessage("x2", x2, int))
        if not isinstance(y2, int):
            raise TypeError(genericTypeErrorMessage("y2", y2, int))
        
        # Validate values
        if x1 < 0 or x1 >= self.size[0]:
            raise ValueError("x1 coordinates out of range")
        if x2 < 0 or x2 > self.size[0]:
            raise ValueError("x2 coordinates out of range")
        elif x2 <= x1:
            raise ValueError("x2 coordinates must be greater than x1")
        
        if y1 < 0 and y1 >= self.size[1]:
            raise ValueError("y1 coordinates out of range")
        if y2 < 0 and y2 > self.size[1]:
            raise ValueError("y2 coordinates out of range")
        elif y2 <= y1:
            raise ValueError("y2 coordinates must be greater than y1")
        
        copy_data = [[] for _ in  range(y2 - y1)]
        for i in range(y1, y2):
            for j in range(x1, x2):
                copy_data[i - y1].append(self.getPixel(j, i))
        data_buffer = numpy.asarray(copy_data, dtype=numpy.uint8)
        return Image.fromarray(data_buffer)

    def fromImage(self, image: Image.Image, format: str = "rgba8"):
        if not isinstance(image, Image.Image):
            raise TypeError(genericTypeErrorMessage("image", image, Image.Image))
        if not isinstance(format, str):
            raise TypeError(genericTypeErrorMessage("format", format, str))

        # Verify format and support
        format_match = self._matchFormat(format.lower())
        if format_match != None:
            format_info = self._getFormatInfo(format_match)
            if not format_info["supported"]:
                raise Texture3dstUnsupported(f"Texture format unsupported: {format}, '{format_info['name']}'")
        else:
            raise ValueError(f"Texture format invalid: {format}")
        
        img_w, img_h = image.size
        self.new(img_w, img_h, format=format)
        self.paste(image, 0, 0)
        return self

    def paste(self, image: Image.Image, x: int, y: int) -> None:
        if not isinstance(image, Image.Image):
            raise TypeError(genericTypeErrorMessage("image", image, Image.Image))
        if not isinstance(x, int):
            raise TypeError(genericTypeErrorMessage("x", x, int))
        if not isinstance(y, int):
            raise TypeError(genericTypeErrorMessage("y", y, int))
        
        img_width = image.size[0]
        img_height = image.size[1]
        if img_width > x + self.size[0] or img_height > y + self.size[1]:
            raise Texture3dstException("Not enough space to paste image")
        
        match self.header.format:
            case 0 | 2 | 4: # rgba8 | rgba5551 | rgba4
                new_image = image.convert("RGBA")
            case 1 | 3: # rgb8 | rgb565
                new_image = image.convert("RGB")
            case 5 | 9: # la8 | la4
                new_image = image.convert("LA")
            case _:
                raise ValueError("Texture 'format' value invalid")
        
        for i in range(y, img_height):
            for j in range(x, img_width):
                self.setPixel(j, i, new_image.getpixel((j, i)))
        return

    def flipVertical(self) -> None:
        self.textureData.reverse()
        return

    def flipHorizontal(self) -> None:
        for element in self.textureData:
            element.reverse()
        return

    def getData(self) -> List[List[Tuple[int]]]:
        copy_data = [[] for _ in  range(self.size[1])]
        for i in range(self.size[1]):
            for j in range(self.size[0]):
                copy_data[i].append(self.getPixel(j, i))
        return copy_data
    
    def _formatPixelData(self) -> bytearray:
        full_width = self.header.full_size[0]
        full_height = self.header.full_size[1]

        # Rearrange pixels and saves them in data
        rearranged_data = _createPixelDataStructure(full_width, full_height)
        i = 0
        while i < self.header.full_size[1]:
            for j in range(self.header.full_size[0]):
                dst_pos = _getTexturePosition(j, i, full_width)

                if dst_pos[1] >= full_height: # Prevents some miscalculations with the real dimensions
                    # Expands available slots
                    for k in range(full_height):
                        self.textureData.append([bytes([0]) for _ in range(full_width)])
                        rearranged_data.append([bytes([0]) for _ in range(full_width)])
                    self.header.full_size[1] *= 2
                    full_height = self.header.full_size[1]

                rearranged_data[dst_pos[1]][dst_pos[0]] = self.textureData[i][j]
            i += 1
        data = _matrixToBytearray(rearranged_data)

        # In case of mipmaps
        if self.header.mip_level > 1:
            self._processMipLevels(data)
        return data

    def _processMipLevels(self, data: bytearray) -> None:
        width = self.header.full_size[0]
        height = self.header.full_size[1]
        resized_width = width
        resized_height = height

        match self.header.format:
            case 0 | 2 | 4: # rgba8 | rgba5551 | rgba4
                image_tmp = Image.new("RGBA", (width, height))
            case 1 | 3: # rgb8 | rgb565
                image_tmp = Image.new("RGB", (width, height))
            case 5 | 9: # la8 | la4
                image_tmp = Image.new("LA", (width, height))
            case _:
                raise ValueError("Texture 'format' value invalid")
            
        # Copy pixel data to a new image
        image_tmp_data = image_tmp.load()
        for i in range(0, height):
            for j in range(0, width):
                pixel_data = self.getPixel(j, i)
                image_tmp_data[j, i] = pixel_data

        for i in range(self.header.mip_level - 1):
            # Resizes image at half
            resized_width = resized_width // 2
            resized_height = resized_height // 2
            image_tmp = image_tmp.resize((resized_width, resized_height), Image.Resampling.LANCZOS)
            
            # Rearrange pixels and appends them to output
            rearranged_data = _createPixelDataStructure(resized_width, resized_height)
            for j in range(resized_height):
                for k in range(resized_width):
                    dst_pos = _getTexturePosition(k, j, resized_width)
                    rearranged_data[dst_pos[1]][dst_pos[0]] = self._convertPixelDataToBytes(image_tmp.getpixel((k, j)))
            data.extend(_matrixToBytearray(rearranged_data))
        return

    def export(self, path: str | Path) -> None:
        if not isinstance(path, str) and not isinstance(path, Path):
            raise TypeError(genericTypeErrorMessage("path", path, Union[str, Path]))
        
        # Process pixel data
        self.flipVertical()
        data = self._formatPixelData()
        self.flipVertical()

        textureFileBuffer = open(path, "wb")

        # Create header
        ## File signature
        textureFileBuffer.write(b'3DST')
        ## Texture mode
        write_uint32(textureFileBuffer, self.header.mode)
        ## Texture format
        write_uint32(textureFileBuffer, self.header.format)

        ## Texture real full size
        write_uint32(textureFileBuffer, self.header.full_size[0])
        write_uint32(textureFileBuffer, self.header.full_size[1])

        ## Texture size
        write_uint32(textureFileBuffer, self.size[0])
        write_uint32(textureFileBuffer, self.size[1])

        ### Mip level
        write_uint32(textureFileBuffer, self.header.mip_level)

        ## Writes all pixel data
        textureFileBuffer.write(data)
        
        textureFileBuffer.close()
        return