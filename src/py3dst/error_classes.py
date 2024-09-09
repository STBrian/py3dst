from typing import Union, get_args

class Texture3dstException(Exception):
    def __init__(self, message):
        super().__init__(message)

class Texture3dstNoSignature(Texture3dstException):
    def __init__(self):
        super().__init__("Texture does not contain file signature")

class Texture3dstUnsupported(Texture3dstException):
    pass

def formatType(annotation) -> str:
    if hasattr(annotation, '__origin__') and annotation.__origin__ is Union:
        types = get_args(annotation)
        return " or ".join(t.__name__ for t in types)
    else:
        return annotation.__name__

def genericTypeErrorMessage(name: str, var, istype):
    return f"'{name}' expected to be {formatType(istype)}, not {type(var)}"