import numpy
from PIL import Image
from pathlib import Path

from .primitive_types import read_bytes, read_uint32
from dataclasses import dataclass
from typing import BinaryIO, Tuple, List, Union
from numpy import uint32

from .utils import isPowerOfTwo, getClosestPowerOfTwo, maxIntBits
from .errors import *

def setPixelRGBAfromList(data: list, pos: tuple, pixel_data: tuple | list) -> list:
        if type(data) != list:
            raise TypeError("Data expected to be a list.")

        if type(pos) != tuple:
            raise TypeError("Position expected to be a tuple.")
        if len(pos) == 2:
            if not all(isinstance(num, int) for num in pos):
                raise TypeError("Coordinates must be integers.")
        else:
            raise ValueError("Position must have 2 values.")
        
        if type(pixel_data) == list:
            pixel_data = tuple(pixel_data)
        if type(pixel_data) != tuple:
            raise ValueError("Pixel_data expected to be a tuple or list.")
        for num in pixel_data:
            if isinstance(num, int):
                if num < 0 or num > 255:
                    raise Texture3dstException("Pixel_data values must be between 0 and 255.")
            else:
                raise Texture3dstException("Pixel_data must be only integers.")

        if len(pixel_data) != len(data[pos[1]][pos[0]]):
            raise ValueError("Pixel_data lenght does not match with original pixel")

        data[pos[1]][pos[0]] = list(pixel_data)
        return data

def getPixelDataFromList(data: list, pos: tuple) -> list:
        if type(data) != list:
            raise Texture3dstException("data expected to be a list.")
        
        if type(pos) != tuple:
            raise TypeError("Position expected to be a tuple.")
        if len(pos) == 2:
            if not all(isinstance(num, int) for num in pos):
                raise TypeError("Coordinates must be integers.")
        else:
            raise ValueError("Position must have 2 values.")
        return data[pos[1]][pos[0]]

def convertRGBA5551toRGBA8(data: list):
    tmpData = []
    for i in range(len(data)):
        tmpData.append([])
        for j in range(len(data[i])):
            tmpData[-1].append([])
            byte1 = data[i][j][0]
            byte2 = data[i][j][1]

            combined = (byte2 << 8) | byte1

            a = int((combined >> 0) & 0b1)
            b = int((combined >> 1) & 0b11111)
            g = int((combined >> 6) & 0b11111)
            r = int((combined >> 11) & 0b11111)

            a = a * 255
            b = int((b/maxIntBits(5))*255)
            g = int((g/maxIntBits(5))*255)
            r = int((r/maxIntBits(5))*255)

            tmpData[-1][-1].extend([a, b, g, r])
    return tmpData

def convertRGB565toRGB8(data: list):
    tmpData = []
    for i in range(len(data)):
        tmpData.append([])
        for j in range(len(data[i])):
            tmpData[-1].append([])
            byte1 = data[i][j][0]
            byte2 = data[i][j][1]

            combined = (byte2 << 8) | byte1

            b = int((combined >> 0) & 0b11111)
            g = int((combined >> 5) & 0b111111)
            r = int((combined >> 11) & 0b11111)

            b = int((b/maxIntBits(5))*255)
            g = int((g/maxIntBits(6))*255)
            r = int((r/maxIntBits(5))*255)

            tmpData[-1][-1].extend([b, g, r])
    return tmpData

def convertRGBA4toRGBA8(data: list):
    tmpData = []
    for i in range(len(data)):
        tmpData.append([])
        for j in range(len(data[i])):
            tmpData[-1].append([])
            byte1 = data[i][j][0]
            byte2 = data[i][j][1]

            combined = (byte2 << 8) | byte1

            a = int((combined >> 0) & 0b1111)
            b = int((combined >> 4) & 0b1111)
            g = int((combined >> 8) & 0b1111)
            r = int((combined >> 12) & 0b1111)

            a = int((a/maxIntBits(4))*255)
            b = int((b/maxIntBits(4))*255)
            g = int((g/maxIntBits(4))*255)
            r = int((r/maxIntBits(4))*255)

            tmpData[-1][-1].extend([a, b, g, r])
    return tmpData

def convertLA4toLA8(data: list):
    tmpData = []
    for i in range(len(data)):
        tmpData.append([])
        for j in range(len(data[i])):
            tmpData[-1].append([])
            byte1 = data[i][j][0]

            a = int((byte1 >> 0) & 0b1111)
            l = int((byte1 >> 4) & 0b1111)

            a = int((a/maxIntBits(4))*255)
            l = int((l/maxIntBits(4))*255)

            tmpData[-1][-1].extend([a, l])
    return tmpData

def convertFunction(data: list, width: int, height: int, conversiontype: int):
        if type(data) != list:
            raise Texture3dstException("Data expected to be a list.")
        if type(width) != int:
            raise Texture3dstException("Width expected to be an integer.")
        if type(height) != int:
            raise Texture3dstException("Height expected to be an integer.")
        if type(conversiontype) != int:
            raise Texture3dstException("Conversion type must be and integer.")
        if not (conversiontype >= 1 and conversiontype <= 2):
            raise Texture3dstException("Conversion type must be 1 or 2.")
        
        channels = len(data[0][0])

        convertedData = [[] for _ in range(height)]
        for i in range(height):
            for j in range(width):
                convertedData[i].append([0] * channels)

        # Bucle que itera siguiendo el patron de guardado visto en estas texturas
        for x in range(width):
            for y in range(height):
                dstPos = ((((y >> 3) * (width >> 3) + (x >> 3)) << 6) + ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3)))
                y2 = (dstPos//width)
                x2 = dstPos - (y2*width)
                if conversiontype == 1:
                    # For convert from linear raw pixel data to 3dst texture data
                    pixelData = getPixelDataFromList(data, (x, y))
                    setPixelRGBAfromList(convertedData, (x2, y2), pixelData[::-1])
                elif conversiontype == 2:
                    # This does the opposite
                    setPixelRGBAfromList(convertedData, (x, y), data[y2][x2][::-1])

        return convertedData

@dataclass
class __headerTexture3dst:
    mode: uint32 = None
    format: uint32 = None
    full_size: Tuple[uint32, uint32] = None # Texture real full size
    size: Tuple[uint32, uint32] = None # Texture size
    mip_level: uint32 = None

def __readTexture3dstHeader(fileBuffer: BinaryIO, headerDst: __headerTexture3dst):
    headerDst.mode = read_uint32(fileBuffer)
    headerDst.format = read_uint32(fileBuffer)
    headerDst.full_size[0] = read_uint32(fileBuffer) # real full width
    headerDst.full_size[1] = read_uint32(fileBuffer) # real full height
    headerDst.size[0] = read_uint32(fileBuffer) # width
    headerDst.size[1] = read_uint32(fileBuffer) # height
    headerDst.mip_level = read_uint32(fileBuffer)

def __getTexturePosition(x: int, y: int, width: int) -> Tuple[int, int]:
    dstPos = ((((y >> 3) * (width >> 3) + (x >> 3)) << 6) + ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) | ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3)))
    y2 = (dstPos//width)
    x2 = dstPos - (y2*width)
    return (x2, y2)

def __isMipLevelValid(width, height, mip_level) -> bool:
    return (width / (2 ** (mip_level - 1)) >= 8) and (height / (2 ** (mip_level - 1)) >= 8)

class Texture3dst:
    header: __headerTexture3dst
    size: Tuple[int, int]
    texture_data: List[List[int]]
    FORMATS = (("rgba8", True),
               ("rgb8", True),
               ("rgba5551", True),
               ("rgb565", True),
               ("rgba4", True),
               ("la8", True),
               ("hilo8", False),
               ("l8", False),
               ("a8", False),
               ("la4", True))

    def __matchFormat(self, format: str) -> int:
        for i, value in enumerate(self.FORMATS):
            if value[0] == format:
                return i
        return None
    
    def __getFormatInfo(self, format: int) -> dict:
        if not isinstance(format, int):
            raise TypeError(genericTypeErrorMessage("format", format, int))
        if format < 0 or format >= len(self.FORMATS):
            return None
        
        formatInfo = {}
        formatInfo["name"] = self.FORMATS[format][0]
        formatInfo["supported"] = self.FORMATS[format][1]
        match format:
            case 0: # rgba8
                formatInfo["pixel_lenght"] = 4
                formatInfo["pixel_channels"] = 4
            case 1: # rgb8
                formatInfo["pixel_lenght"] = 3
                formatInfo["pixel_channels"] = 3
            case 2: # rgba5551
                formatInfo["pixel_lenght"] = 2
                formatInfo["pixel_channels"] = 4
            case 3: # rgb565
                formatInfo["pixel_lenght"] = 2
                formatInfo["pixel_channels"] = 3
            case 4: # rgba4
                formatInfo["pixel_lenght"] = 2
                formatInfo["pixel_channels"] = 4
            case 5: # la8
                formatInfo["pixel_lenght"] = 2
                formatInfo["pixel_channels"] = 2
            case 9: # la4
                formatInfo["pixel_lenght"] = 1
                formatInfo["pixel_channels"] = 2

        return formatInfo

    def open(self, path: str | Path):
        # Validate types
        if isinstance(path, str):
            path = Path(path)
        if not isinstance(path, Path):
            raise TypeError(genericTypeErrorMessage("path", path, Union[str, Path]))
        
        # File from the texture will be loaded
        textureFileBuffer = open(path, "rb")
        
        # File signature
        if read_bytes(textureFileBuffer, 4) != b'3DST':
            raise Texture3dstException("Texture does not contain file signature")
        
        # Header of the file
        self.header = __headerTexture3dst()
        __readTexture3dstHeader(textureFileBuffer, self.header)
        
        # Only mode 3 is supported
        if self.header.mode != 3:
            raise Texture3dstUnsupported(f"Unsupported mode: {self.header.mode}")
        
        # Get format info and support
        format = self.header.format
        format_info = self.__getFormatInfo(format)
        if format_info == None:
            raise Texture3dstUnsupported(f"Texture format unsupported: {format}")
        elif not format_info["supported"]:
            raise Texture3dstUnsupported(f"Texture format unsupported: {format}, '{format_info["name"]}'")

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
        if not __isMipLevelValid(full_width, full_height, mip_level):
            raise Texture3dstException("Mip level' value greater than supported")

        # Save size
        self.size: Tuple[int, int] = (int(self.header.size[0]), int(self.header.size[1]))

        # Creates empty structure for pixel data
        self.texture_data = [[] for _ in range(self.size[1])]
        for element in self.texture_data:
            for _ in range(self.size[0]):
                element.append([0])
        
        # Storage pixel data in place
        for i in range(self.size[1]):
            for j in range(self.size[0]):
                pixel_read = list(read_bytes(textureFileBuffer, format_info["pixel_lenght"]))[::-1] # Pixel data is reversed
                dst_pos = __getTexturePosition(j, i, self.size[0])
                self.texture_data[dst_pos[1]][dst_pos[0]] = pixel_read

        textureFileBuffer.close()
        # All textures are upside down by default
        self.flipX()
        return self

    def new(self, width: int, height: int, mip_level: int = 1, format: str = "rgba8"):
        # Validate types
        if type(width) != int:
            raise TypeError(genericTypeErrorMessage("width", width, int))
        if type(height) != int:
            raise TypeError(genericTypeErrorMessage("height", height, int))
        if type(mip_level) != int:
            raise TypeError(genericTypeErrorMessage("miplevel", mip_level, int))
        
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
        if not __isMipLevelValid(full_width, full_height, mip_level):
            raise Texture3dstException("'mip_level' value greater than supported")
        
        # Verify format and support
        format_match = self.__matchFormat(format)
        if format_match:
            format_info = self.__getFormatInfo(format_match)
            if not format_info["supported"]:
                raise Texture3dstUnsupported(f"Texture format unsupported: {format}, '{format_info["name"]}'")
        else:
            raise ValueError(f"Texture format invalid: {format}")
        
        self.header = __headerTexture3dst()
        self.header.mode = 3
        self.header.format = format_match
        self.header.full_size[0] = full_width
        self.header.full_size[1] = full_height
        self.header.size[0] = width
        self.header.size[1] = height
        self.header.mip_level = mip_level

        self.size: Tuple[int, int] = (width, height)

        # Creates empty structure for pixel data
        self.texture_data = [[] for _ in range(self.size[1])]
        for element in self.texture_data:
            for _ in range(self.size[0]):
                element.append([0])
        return self

    def setPixelRGBA(self, x: int, y: int, pixel_data: tuple | list) -> None:
        if type(x) != int:
            raise ValueError(genericTypeErrorMessage("x", x, int))
        if type(y) != int:
            raise ValueError(genericTypeErrorMessage("y", y, int))
        if x < 0 or x >= self.size[0]:
            raise ValueError("x coordinates out of range")
        if y < 0 or y >= self.size[1]:
            raise ValueError("y coordinates out of range")
        
        if type(pixel_data) == list:
            pixel_data = tuple(pixel_data)
        if type(pixel_data) != tuple:
            raise Texture3dstException("pixel_data expected to be a tuple or list.")
        if len(pixel_data) != self.channels:
            raise Texture3dstException("pixel_data lenght does not match with texture channels")
        for num in pixel_data:
            if isinstance(num, int):
                if num < 0 or num > 255:
                    raise Texture3dstException("pixel_data values must be between 0 and 255.")
            else:
                raise Texture3dstException("pixel_data must be only integers.")
        self.data[y][x] = list(pixel_data)
        return

    def getPixelData(self, x: int, y: int) -> list:
        if type(x) != int:
            raise Texture3dstException("x coordinates expected to be an integer.")
        if type(y) != int:
            raise Texture3dstException("y coordinates expected to be an integer.")
        if x < 0 or x >= self.width:
            raise Texture3dstException("x coordinates out of range.")
        if y < 0 or y >= self.height:
            raise Texture3dstException("y coordinates out of range.")
        return self.data[y][x]
    
    def copy(self, x1: int, y1: int, x2: int, y2: int) -> Image.Image:
        if not (x1 >= 0 and x1 <= self.width):
            raise Texture3dstException("x1 coordinates out of range")
        if not (x2 >= 0 and x2 <= self.width and x2 >= x1):
            raise Texture3dstException("x2 coordinates out of range or invalid value")
        if not (y1 >= 0 and y1 <= self.height):
            raise Texture3dstException("y1 coordinates out of range")
        if not (y2 >= 0 and y2 <= self.height and y2 >= y1):
            raise Texture3dstException("y2 coordinates out of range or invalid value")
        copyData = [[] for _ in  range(y2 - y1)]
        for i in range(y1, y2):
            for j in range(x1, x2):
                copyData[i - y1].append(self.data[i][j])
        buffer = numpy.asarray(copyData, dtype=numpy.uint8)
        return Image.fromarray(buffer)

    def fromImage(self, image: Image.Image):
        img_w, img_h = image.size
        texture = self.new(img_w, img_h, 1)
        texture.paste(image, 0, 0)
        return self

    def paste(self, image: Image.Image, x: int, y: int) -> None:
        if self.format == "rgba8" or self.format == "rgba5551":
            tformat = "RGBA"
        elif self.format == "rgb8":
            tformat = "RGB"
        width = image.size[0]
        height = image.size[1]
        if width > self.width or height > self.height:
            raise Texture3dstException("Source image is bigger than destination texture")
        imageRgba = image.convert(tformat)
        imgData = imageRgba.load()
        for i in range(y, height):
            for j in range(x, width):
                self.setPixelRGBA(j, i, list(imgData[j, i])[::])
        return

    def flipX(self) -> None:
        self.data.reverse()
        return

    def flipY(self) -> None:
        for element in self.data:
            element.reverse()
        return

    def getData(self) -> list:
        return self.data

    def convertData(self) -> None:        
        print("[Warning] 'convertData' function is deprecated and its use is no longer necessary")
    
    def __formatPixelData(self) -> None:
        # Uso interno
        self.convertedData = convertFunction(self.data, self.texwidth, self.texheight, 1)

        if self.miplevel > 1:
            self.mipoutput = []
            width = self.texwidth
            height = self.texheight
            resizedwidth = self.texwidth
            resizedheight = self.texheight

            # Copia la información de data a una imagen temporal
            tmpImage = Image.new("RGBA", (width, height))
            tmpImagePixels = tmpImage.load()
            for y in range(0, height):
                for x in range(0, width):
                    pixelData = getPixelDataFromList(self.data, (x, y))
                    tmpImagePixels[x, y] = tuple(pixelData)

            self.mipoutput = [[] for _ in range(self.miplevel - 1)]
            for i in range(0, self.miplevel - 1):
                # Se reescala la imagen
                resizedwidth = resizedwidth // 2
                resizedheight = resizedheight // 2
                tmpImage = tmpImage.resize((resizedwidth, resizedheight), Image.Resampling.LANCZOS)

                # Se obtiene los datos de la imagen reescalada
                mipTmpData = [[] for _ in range(resizedheight)]
                for y in range(0, resizedheight):
                    for x in range(0, resizedwidth):
                        mipTmpData[y].append([])
                        pixelData = tmpImage.getpixel((x, y))
                        mipTmpData[y][x] = pixelData[:]

                # Se convierte los datos usando la funcion
                self.mipoutput[i] = convertFunction(mipTmpData, resizedwidth, resizedheight, 1)

                # Se reducen las dimensiones en caso de usarse de nuevo
                width = width // 2
                height = height // 2
            mipTmpData = []
        return

    def export(self, path: str | Path) -> None:
        if type(path) == str:
            path = Path(path)
        if not isinstance(path, Path):
            raise TypeError("Expected str or Path type for path.")
        
        self.flipX()
        self.__formatPixelData()
        self.flipX()

        # Se crea la cabecera
        ## Marca de formato
        output = bytearray(uint_to_bytes(bytes_to_uint(bytes.fromhex("33445354"), "little"), "little"))
        ## Modo de textura
        output.extend(uint_to_bytes(self.mode, "little"))
        ## No sé aún pero mientras tanto xd (posiblemente es el formato)
        output.extend(uint_to_bytes(self.formats.index(self.format), "little"))

        ## Se escriben las dimensiones de la textura
        output.extend(uint_to_bytes(self.texwidth, "little"))
        output.extend(uint_to_bytes(self.texheight, "little"))

        ## Se escriben las dimensiones de la textura original
        output.extend(uint_to_bytes(self.width, "little"))
        output.extend(uint_to_bytes(self.height, "little"))

        ### Mip level
        output.extend(uint_to_bytes(self.miplevel, "little"))

        ## Se copia la lista de convertedData a output - Nivel primario
        for y in self.convertedData:
            for pixel in y:
                for channel in pixel:
                    output.append(channel)
        
        ## Se copian los niveles de mipoutput (si hay) - Niveles de mip
        if self.miplevel > 1:
            for nivel in self.mipoutput:
                for y in nivel:
                    for pixel in y:
                        for channel in pixel:
                            output.append(channel)

        # Se escriben los bytes en un archivo
        with open(path, "wb") as f:
            f.write(output)

        self.convertedData = []
        self.mipoutput = []
        return
    