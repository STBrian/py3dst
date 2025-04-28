from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image
from typing import Tuple, List

if sys.version_info >= (3, 13) and sys.version_info < (3, 14):
    from .win.cp313.tex3dst import Texture3dst as CTexture3dst
    from .win.cp313.tex3dst import PixelData
elif sys.version_info >= (3, 12):
    from .win.cp312.tex3dst import Texture3dst as CTexture3dst
    from .win.cp312.tex3dst import PixelData
else:
    raise ImportError("Python 3.12 or 3.13 required for py3dst_exp.")

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
    
    def __init__(self):
        self.obj = CTexture3dst()

    def open(self, path: str | Path):
        path = str(path)
        self.obj.open(path)
        self.size = [self.obj.size.width, self.obj.size.height]
        self.header = self.obj.header
        return self

    def new(self, width: int, height: int, mip_level: int = 1, format: str = "rgba8"):
        format = self._matchFormat(format)
        if format is None:
            return ValueError("Invalid format")
        self.obj.create(width, height, mip_level, format)
        self.size = [width, height]
        self.header = self.obj.header
        return self

    def setPixel(self, x: int, y: int, pixel_data: Tuple[int] | List[int]) -> None:
        pixel_data_obj = PixelData()
        match self.obj.header.format:
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
        self.obj.setPixel(x, y, pixel_data_obj)
    
    def getPixel(self, x: int, y: int) -> Tuple[int]:
        pixel_data_obj = PixelData()
        self.obj.getPixel(x, y, pixel_data_obj)
        match self.obj.header.format:
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
        arr = self.obj.to_numpy()
        return Image.fromarray(arr)
    
    def cropToImage(self, x1: int, y1: int, x2: int, y2: int) -> Image.Image:
        arr = self.obj.crop_to_numpy(x1, y1, x2, y2)
        return Image.fromarray(arr)
    
    def export(self, path: str | Path, mipmapOpaque: bool = False) -> None:
        path = str(path)
        self.obj.save(path)