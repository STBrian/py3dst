import argparse
import sys
import os
import tkinter
import traceback
from PIL import Image, ImageTk, UnidentifiedImageError
from glob import iglob
from pathlib import Path
from .tex3dst import Texture3dst
from .error_classes import *

__version__ = "1.2.0"

def convertFile(input_path: Path, output_path: Path, show_unidentified_image: bool, show_tracebacks: bool):
    try:
        texture = Texture3dst().open(input_path)
        try:
            image = texture.copy(0, 0, texture.size[0], texture.size[1])
            if not output_path.exists():
                os.makedirs(output_path)
            image.save(f"{output_path}/{input_path.stem}.png")
            print("File saved at:", f"{output_path.absolute()}/{input_path.stem}.png")
        except Exception as e:
            print("Error: Unable to convert file:", e)
            print(input_path.absolute())
            if show_tracebacks:
                traceback.print_exc()
            return 6
    except Texture3dstNoSignature:
        try:
            image = Image.open(input_path)
            try:
                texture = Texture3dst().fromImage(image)
                if not output_path.exists():
                    os.makedirs(output_path)
                texture.export(f"{output_path}/{input_path.stem}.3dst")
                print("File saved at:", f"{output_path.absolute()}/{input_path.stem}.3dst")
            except Exception as e:
                print("Error: Unable to convert file:", e)
                print(input_path.absolute())
                if show_tracebacks:
                    traceback.print_exc()
                return 8
        except UnidentifiedImageError:
            if show_unidentified_image:
                print("Error: Unable to convert file")
                print(input_path.absolute())
            return 7
    except Exception as e:
        print("Error: Unable to convert file:", e)
        print(input_path.absolute())
        if show_tracebacks:
            traceback.print_exc()
        return 5
    return 0

def main():
    parser = argparse.ArgumentParser(prog="py3dst", description="Display or convert 3DST textures")
    parser.add_argument(
        "path", 
        nargs="?",
        help="path to file to open and show"
    )
    parser.add_argument(
        "-t", 
        "--touch", 
        action="store_true",
        help="textures provided will be rebuilded"
    )
    parser.add_argument(
        "--suppress-errors", 
        action="store_true",
        help="the program will continue even if it finds a non-critical error in a file"
    )
    parser.add_argument(
        "--show-tracebacks", 
        action="store_true",
        help="this will show tracebacks when a file is not converted fro unhandled reasons"
    )
    parser.add_argument(
        "-c", 
        "--convert", 
        action="store_true",
        help="indicates whether to convert the provided file"
    )
    parser.add_argument(
        "-i", 
        "--input", 
        metavar=("IN"),
        action="append",
        help="files to convert"
    )
    parser.add_argument(
        "-o", 
        "--output", 
        metavar=("OUT"),
        action="store",
        help="destination directory"
    )
    parser.add_argument(
        "-r", 
        "--recursive", 
        action="store_true", 
        help="convert files recursively in the directory"
    )
    parser.add_argument(
        "-f", 
        "--format", 
        action="store", 
        metavar=("FORMAT"),
        choices=["rgba8", "rgb8", "rgba5551", "rgb565", "rgba4", "la8", "la4"], 
        default="rgba8",
        help="color format for the output ('rgba8', 'rgb8', 'rgba5551', 'rgb565', 'rgba4', 'la8', 'la4')"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args()
    if args.touch and args.convert:
        parser.error("conflicting flags, select only one -t --touch or -c --convert")
    if args.touch and not args.path:
        parser.error("path is required with -t --touch flag")
    if not args.convert and not args.path:
        parser.error("path is required if not -c --convert flag used")
    if args.convert and not args.input:
        parser.error("-i --input is required if -c --convert flag used")
    if args.convert and not args.output:
        parser.error("-o --output is required if -c --convert flag used")

    if not args.convert and not args.touch:
        path = Path(args.path)
        if path.exists() and path.is_file():
            try:
                texture = Texture3dst().open(path)
            except Exception as e:
                print("Error: Unable to load 3dst texture:", e)
                return 3

            image = texture.copy(0, 0, texture.size[0], texture.size[1])
            
            root = tkinter.Tk()
            root.title(path.name)
            root.geometry(f"{texture.size[0]}x{texture.size[1]}")
            image_tk = ImageTk.PhotoImage(image)
            image_label = tkinter.Label(root, image=image_tk)
            image_label.pack(expand=True)

            root.mainloop()
        elif path.exists() and path.is_dir():
            print("Error: Path is a directory")
            return 2
        else:
            print("Error: Path doesn't exists")
            return 1
    elif args.touch:
        path = Path(args.path)
        if path.exists() and path.is_file():
            try:
                texture = Texture3dst().open(path)
            except Exception as e:
                print("Error: Unable to load 3dst texture:", e)
                return 3
            texture.export(path)
        elif path.exists() and path.is_dir():
            print("Error: Path is a directory")
            return 2
        else:
            print("Error: Path doesn't exists")
            return 1
    elif args.convert:
        output_path = Path(args.output)
        
        for path in args.input:
            input_path = Path(path)
            if input_path.exists() and input_path.is_file():
                input_path = Path(path)
                status_code = convertFile(input_path, output_path, show_unidentified_image=True, show_tracebacks=args.show_tracebacks)
                if not args.suppress_errors and status_code:
                    return status_code
            elif input_path.exists() and input_path.is_dir():
                if args.recursive:
                    input_files = iglob(os.path.join(input_path.absolute(), "**/**"), recursive=True)
                else:
                    input_files = iglob(os.path.join(input_path.absolute(), "**"))

                for file in input_files:
                    file_path = Path(file)
                    if file_path.is_file():
                        status_code = convertFile(file_path, output_path, show_unidentified_image=False, show_tracebacks=args.show_tracebacks)
                        if status_code and not args.suppress_errors and status_code != 7:
                            return status_code
            else:
                print("Error: Path doesn't exists")
                return 1
    else:
        print("Nothing has happened?")

    return 0
        

if __name__ == "__main__":
    status_code = main()
    sys.exit(status_code)