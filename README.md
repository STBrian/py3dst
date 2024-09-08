py3dst is a module that allows to read, edit and convert 3DST textures

## Installation

```bash
pip install py3dst
```

## Supported formats:
- RGBA8
- RGB8
- RGBA5551
- RGB565
- RGBA4
- LA8
- LA4

## How to use
### Open a texture
The open() function decodes and loads the texture at the provided path
```python
from py3dst import Texture3dst

texture = Texture3dst().open("path/to/file")
```

### Create a texture
The new() function allows to create a blank new texture
```python
from py3dst import Texture3dst

texture = Texture3dst().new(128, 128)
```
new() takes 2 arguments: width, height

Optionally you can specify the 'mip_level' and 'format'

### Export a texture
The export() function converts the data and writes the output data to the specified location
```python
texture.export("path/to/file")
```

### Convert to PIL Image
The copy() function will create an output of PIL Image type that you can then export to other image format
```python
image = texture.copy(0, 0, texture.size[0], texture.size[1])
```
copy() takes 4 arguments: x1, y1, x2, y2

Being the coordinates that indicate the area to copy

### Convert from PIL Image
The paste() function will take the PIL Image object and will paste all of its content into the texture if theres enough space in the destination texture. Example:
```python
from py3dst import Texture3dst
from PIL import Image

image = Image.open("path/to/image/")
texture = Texture3dst().new(image.size[0], image.size[1])
texture.paste(image, 0, 0)
```
paste() takes 3 arguments: image, x, y

x and y being the coordinates where the image will be pasted