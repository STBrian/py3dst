py3dst is a module that allows to read, edit and convert 3DST textures

# Installation

```bash
pip install py3dst
```

# Command-line interface
The module has a simple command-line interface to perform certain tasks such as displaying the provided file on screen or other conversion tasks between formats

```bash
python -m py3dst -h
```

The previous command shows this help message

```
usage: py3dst [-h] [-c] [-r] [-f FORMAT] [-o OUT] [-v] [path]

Display or convert 3DST textures

positional arguments:
  path                  path to file to open and show        

options:
  -h, --help            show this help message and exit
  -c, --convert         indicates whether to convert the provided file
  -r, --recursive       convert files recursively in the directory
  -f FORMAT, --format FORMAT
                        (optional) color format for the output ('rgba8', 'rgb8', 'rgba5551', 'rgb565', 'rgba4', 'la8', 'la4')        
  -o OUT, --output OUT  destination file or directory if multiple output files
  -v, --version         show program's version number and exit
```

# Supported formats:
- RGBA8
- RGB8
- RGBA5551
- RGB565
- RGBA4
- LA8
- LA4

# How to use
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
texture.export("path/to/out/file")
```

### Convert to PIL Image
The copy() function will create an output of PIL Image type that you can then export to other image format
```python
image = texture.copy(0, 0, texture.size[0], texture.size[1])
image.save("path/to/out/image/")
```
copy() takes 4 arguments: x1, y1, x2, y2

Being the coordinates that indicate the area to copy

### Convert from PIL Image
The fromImage() function will take the PIL Image object and create a new texture with it. Example:
```python
from py3dst import Texture3dst
from PIL import Image

image = Image.open("path/to/image/")
texture = Texture3dst().fromImage(image)
```
fromImage() takes 1 argument: image

image must be a PIL.Image object