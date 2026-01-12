from __future__ import annotations

import os
import ctypes
import numpy
from pathlib import Path
from PIL import Image
from typing import Tuple, List
from warnings import deprecated

from py3dst.utils import maxIntBits

_path = os.path.dirname(os.path.realpath(__file__))

if os.name == "nt":
    libtex3dst = ctypes.WinDLL(os.path.join(_path, "libtex3dst.dll"))
elif os.name == "posix":
    import platform

    if platform.system() == "Linux":
        libtex3dst = ctypes.CDLL(os.path.join(_path, "libtex3dst.so"))
    else:
        raise ImportError("OS not supported by py3dst_exp")
else:
    raise ImportError("OS not supported by py3dst_exp")

print("[Warning] Experimental py3dst_exp module loaded, use with precaution")

class _Texture3dst_wrapper(ctypes.Structure):
    pass

class _size2(ctypes.Structure):
    _fields_ = [
        ("width", ctypes.c_uint32),
        ("height", ctypes.c_uint32)
    ]

class _HeaderTexture3dst(ctypes.Structure):
    _fields_ = [
        ("mode", ctypes.c_uint32),
        ("format", ctypes.c_uint32),
        ("full_size", _size2),
        ("size", _size2),
        ("mip_level", ctypes.c_uint32),
    ]

class PixelData(ctypes.Structure):
    _fields_ = [
        ("r", ctypes.c_uint8),
        ("g", ctypes.c_uint8),
        ("b", ctypes.c_uint8),
        ("a", ctypes.c_uint8),
        ("l", ctypes.c_uint8),
    ]

_tex3dstobjp = ctypes.POINTER(_Texture3dst_wrapper)

libtex3dst.Tex3DSTNewObject.argtypes = None
libtex3dst.Tex3DSTNewObject.restype = _tex3dstobjp

libtex3dst.Tex3DSTFree.argtypes = [_tex3dstobjp]
libtex3dst.Tex3DSTFree.restype = None

libtex3dst.Tex3DSTGetHeader.argtypes = [_tex3dstobjp, ctypes.POINTER(_HeaderTexture3dst)]
libtex3dst.Tex3DSTGetHeader.restype = None

libtex3dst.Tex3DSTOpen.argtypes = [_tex3dstobjp, ctypes.c_char_p]
libtex3dst.Tex3DSTOpen.restype = None

libtex3dst.Tex3DSTCreate.argtypes = [_tex3dstobjp, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
libtex3dst.Tex3DSTCreate.restype = None

libtex3dst.Tex3DSTFlipVertical.argtypes = [_tex3dstobjp]
libtex3dst.Tex3DSTFlipVertical.restype = None

libtex3dst.Tex3DSTSetPixel.argtypes = [_tex3dstobjp, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(PixelData)]
libtex3dst.Tex3DSTSetPixel.restype = None

libtex3dst.Tex3DSTGetPixel.argtypes = [_tex3dstobjp, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(PixelData)]
libtex3dst.Tex3DSTGetPixel.restype = None

libtex3dst.Tex3DSTCrop.argtypes = [_tex3dstobjp, _tex3dstobjp, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
libtex3dst.Tex3DSTCrop.restype = None

libtex3dst.Tex3DSTGetRaw.argtypes = [_tex3dstobjp]
libtex3dst.Tex3DSTGetRaw.restype = ctypes.POINTER(ctypes.c_uint8)

libtex3dst.Tex3DSTPaste.argtypes = [_tex3dstobjp, _tex3dstobjp, ctypes.c_uint32, ctypes.c_uint32]
libtex3dst.Tex3DSTPaste.restype = ctypes.c_bool

libtex3dst.Tex3DSTCompare.argtypes = [_tex3dstobjp, _tex3dstobjp, ctypes.c_bool]
libtex3dst.Tex3DSTCompare.restype = None

libtex3dst.Tex3DSTSave.argtypes = [_tex3dstobjp, ctypes.c_char_p]
libtex3dst.Tex3DSTSave.restype = None

class Texture3dst:
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
        format_info = {}
        format_info["name"] = self.FORMATS[format][0]
        format_info["supported"] = self.FORMATS[format][1]
        format_info["pixel_length"] = self.FORMATS[format][2]
        format_info["pixel_channels"] = self.FORMATS[format][3]
        return format_info
    
    def __init__(self):
        self.obj = libtex3dst.Tex3DSTNewObject()
        self.header = _HeaderTexture3dst()
        self.size = []

    def __del__(self):
        libtex3dst.Tex3DSTFree(self.obj)

    @staticmethod
    def open(path: str | Path) -> Texture3dst:
        nins = Texture3dst()
        libtex3dst.Tex3DSTOpen(nins.obj, str(path).encode())
        libtex3dst.Tex3DSTGetHeader(nins.obj, ctypes.byref(nins.header))
        nins.size = [nins.header.size.width, nins.header.size.height]
        return nins

    @staticmethod
    def new(width: int, height: int, mip_level: int = 1, format: str = "rgba8") -> Texture3dst:
        nins = Texture3dst()
        format = nins._matchFormat(format)
        if format is None:
            return ValueError("Invalid format")
        libtex3dst.Tex3DSTCreate(nins.obj, width, height, mip_level, format)
        libtex3dst.Tex3DSTGetHeader(nins.obj, ctypes.byref(nins.header))
        nins.size = [width, height]
        return nins

    def setPixel(self, x: int, y: int, pixel_data: Tuple[int] | List[int]) -> None:
        pixel_data_obj = PixelData()
        match self.header.format:
            case 0|2|4:
                pixel_data_obj.r = pixel_data[0]
                pixel_data_obj.g = pixel_data[1]
                pixel_data_obj.b = pixel_data[2]
                pixel_data_obj.a = pixel_data[3]
            case 1|3:
                pixel_data_obj.r = pixel_data[0]
                pixel_data_obj.g = pixel_data[1]
                pixel_data_obj.b = pixel_data[2]
            case 5|9:
                pixel_data_obj.l = pixel_data[0]
                pixel_data_obj.a = pixel_data[1]
            case _:
                raise ValueError("Invalid format")
        libtex3dst.Tex3DSTSetPixel(self.obj, x, y, ctypes.byref(pixel_data_obj))
    
    def getPixel(self, x: int, y: int) -> Tuple[int]:
        pixel_data_obj = PixelData()
        libtex3dst.Tex3DSTGetPixel(self.obj, x, y, ctypes.byref(pixel_data_obj))
        match self.header.format:
            case 0|2|4:
                pixel_data = (pixel_data_obj.r, pixel_data_obj.g, pixel_data_obj.b, pixel_data_obj.a)
            case 1|3:
                pixel_data = (pixel_data_obj.r, pixel_data_obj.g, pixel_data_obj.b)
            case 5|9:
                pixel_data = (pixel_data_obj.l, pixel_data_obj.a)
            case _:
                raise ValueError("Invalid format")
        return pixel_data
    
    def toImage(self) -> Image.Image:
        bufferptr = libtex3dst.Tex3DSTGetRaw(self.obj)
        w, h = self.header.full_size.width, self.header.full_size.height
        channels = self._getFormatInfo(self.header.format)["pixel_channels"]
        np_array = numpy.ctypeslib.as_array(bufferptr, shape=(h, w, channels))
        match self.header.format:
            case 0 | 2 | 4: # rgba8 | rgba5551 | rgba4
                pil_fmt = "RGBA"
            case 1 | 3: # rgb8 | rgb565
                pil_fmt = "RGB"
            case 5 | 9: # la8 | la4
                pil_fmt = "LA"
            case _:
                raise ValueError("Texture 'format' value invalid")
        return Image.fromarray(np_array.copy(), pil_fmt)
    
    def crop(self, x1: int, y1: int, x2: int, y2: int) -> Texture3dst:
        # Check values
        if x1 < 0 or x1 >= self.size[0]:
            raise ValueError("x1 coordinates out of range")
        if x2 < 0 or x2 > self.size[0]:
            raise ValueError("x2 coordinates out of range")
        if x2 <= x1:
            raise ValueError("x2 coordinates must be greater than x1")
        
        if y1 < 0 and y1 >= self.size[1]:
            raise ValueError("y1 coordinates out of range")
        if y2 < 0 and y2 > self.size[1]:
            raise ValueError("y2 coordinates out of range")
        if y2 <= y1:
            raise ValueError("y2 coordinates must be greater than y1")
        
        nins = Texture3dst()
        libtex3dst.Tex3DSTCrop(self.obj, nins.obj, x1, y1, x2, y2)
        libtex3dst.Tex3DSTGetHeader(nins.obj, ctypes.byref(nins.header))
        nins.size = [nins.header.size.width, nins.header.size.height]
        return nins
    
    def paste(self, tex2: Texture3dst, x: int, y: int):
        # Validate values
        if x < 0 or x >= self.size[0]:
            raise ValueError("x1 coordinates out of range")
        
        if y < 0 and y >= self.size[1]:
            raise ValueError("y1 coordinates out of range")
        
        if self.header.format != tex2.header.format:
            raise TypeError("Texture format must be the same as destination")

        img_width = tex2.size[0]
        img_height = tex2.size[1]
        if img_width + x > self.size[0] or img_height + y > self.size[1]:
            raise ValueError("Not enough space to paste image")
        
        if not libtex3dst.Tex3DSTPaste(self.obj, tex2.obj):
            raise Exception("Failed to paste the texture")
        
    def compare(self, tex2: Texture3dst, ignoreAlpha: bool = True) -> bool:        
        return libtex3dst.Tex3DSTCompare(self.obj, tex2.obj, ignoreAlpha)
    
    @deprecated("Use crop and then toImage")
    def cropToImage(self, x1: int, y1: int, x2: int, y2: int) -> Image.Image:
        nins = self.crop(x1, y1, x2, y2)
        return nins.toImage()
    
    def pasteImage(self, image: Image.Image, x: int, y: int) -> None:
        if image.size[0] <= 0 or image.size[1] <= 0:
            raise ValueError("Image size must be greater than 0")
        
        img_width = image.size[0]
        img_height = image.size[1]
        if img_width + x > self.size[0] or img_height + y > self.size[1]:
            raise ValueError("Not enough space to paste image")
        
        match self.header.format:
            case 0 | 2 | 4: # rgba8 | rgba5551 | rgba4
                new_image = image.convert("RGBA")
            case 1 | 3: # rgb8 | rgb565
                new_image = image.convert("RGB")
            case 5 | 9: # la8 | la4
                new_image = image.convert("LA")
            case _:
                raise ValueError("Texture 'format' value invalid")
        
        for i in range(new_image.size[1]):
            for j in range(new_image.size[0]):
                self.setPixel(x+j, y+i, new_image.getpixel((j, i)))
        return
    
    @staticmethod
    def fromImage(image: Image.Image, format: str = "rgba8"):
        self = Texture3dst()
        # Check format and support
        format_match = self._matchFormat(format.lower())
        if format_match != None:
            format_info = self._getFormatInfo(format_match)
            if not format_info["supported"]:
                raise TypeError(f"Texture format unsupported: {format}, '{format_info['name']}'")
        else:
            raise ValueError(f"Texture format invalid: {format}")
        
        img_w, img_h = image.size
        self.new(img_w, img_h, format=format)
        self.pasteImage(image, 0, 0)
        return self
    
    def export(self, path: str | Path, mipmapOpaque: bool = False) -> None:
        libtex3dst.Tex3DSTSave(self.obj, str(path).encode())

    @deprecated("Added for backwards compatibility")
    def _convertPixelDataToBytes(self, pixel_data: List[int] | Tuple[int]) -> bytes:
        # Validate values
        format = self.header.format
        if format < 0 or format >= len(self.FORMATS):
            raise ValueError(f"Unexpected 'format' value: {format}")
        
        format_info = self._getFormatInfo(format)
        if not format_info["supported"]:
            raise TypeError(f"'format' is unsupported: {format}, {format_info['name']}")
        
        if len(pixel_data) > format_info["pixel_channels"]:
            raise ValueError(f"Too many values ({len(pixel_data)}) in 'pixel_data' for format: {format}, {format_info['name']}")
        elif len(pixel_data) < format_info["pixel_channels"]:
            raise ValueError(f"Too few values ({len(pixel_data)}) in 'pixel_data' for format: {format}, {format_info['name']}")

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
        return combined.to_bytes(format_info["pixel_length"], "little", signed=False)

    @deprecated("Added for backwards compatibility")
    def _convertBytesToPixelData(self, pixel_bytes: bytes) -> Tuple[int]:
        # Validate values
        format = self.header.format
        if format < 0 or format >= len(self.FORMATS):
            raise ValueError(f"Unexpected 'format' value: {format}")
        
        format_info = self._getFormatInfo(format)
        if not format_info["supported"]:
            raise TypeError(f"'format' is unsupported: {format}, {format_info['name']}")
        
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