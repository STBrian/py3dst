import argparse, sys, os
import tkinter
from PIL import Image, ImageTk, UnidentifiedImageError
from glob import iglob
from pathlib import Path
from .tex3dst import Texture3dst
from .error_classes import *

__version__ = "1.1.1"

def main():
    parser = argparse.ArgumentParser(prog="py3dst", description="Display or convert 3DST textures")
    parser.add_argument(
        "path", 
        nargs="?",
        help="path to file to open and show"
    )
    parser.add_argument(
        "-c", 
        "--convert", 
        action="store_true",
        help="indicates whether to convert the provided file"
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
        help="(optional) color format for the output ('rgba8', 'rgb8', 'rgba5551', 'rgb565', 'rgba4', 'la8', 'la4')"
    )
    parser.add_argument(
        "-o", 
        "--output", 
        metavar=("OUT"),
        action="store",
        help="destination file or directory if multiple output files"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    args = parser.parse_args()
    if not args.convert and not args.path:
        parser.error("path is required if not -c --convert flag used")
    if args.convert and not args.output:
        parser.error("-o --output is required if -c --convert flag used")

    path = Path(args.path)
    if args.convert:
        output_path = Path(args.output)
        if path.is_file():
            try:
                texture = Texture3dst().open(path)
                try:
                    image = texture.copy(0, 0, texture.size[0], texture.size[1])
                    image.save(output_path)
                    print("File saved at:", output_path.absolute())
                except Exception as e:
                    print("Error: Unable to convert file:", e)
                    sys.exit(7)
            except Texture3dstNoSignature:
                try:
                    image = Image.open(path)
                    try:
                        texture = Texture3dst().fromImage(image)
                        texture.export(output_path)
                    except Exception as e:
                        print("Error: Unable to convert file:", e)
                        sys.exit(8)
                except Exception as e:
                    print("Error: Unable to load file:", e)
                    sys.exit(6)
            except Exception as e:
                print("Error: Unable to load file:", e)
                sys.exit(5)
        elif path.is_dir():
            print("The path is a directory. Select an option:")
            print("1) Convert 3DST textures to PNG images")
            print("2) Convert PNG images to 3DST textures")
            print("3) Convert all supported image formats to 3DST textures")
            print("0) Exit")
            option = input("Enter an option: ")
            match option:
                case "1":
                    if args.recursive:
                        input_files = iglob(os.path.join(path.absolute(), "**/*.3dst"), recursive=True)
                    else:
                        input_files = iglob(os.path.join(path.absolute(), "*.3dst"))

                    for file in input_files:
                        file_path = Path(file)
                        try:
                            texture = Texture3dst().open(file)
                            image = texture.copy(0, 0, texture.size[0], texture.size[1])
                            output_file_path = Path(os.path.join(output_path.absolute(), f"{file_path.stem}.png"))
                            if not output_path.exists():
                                os.makedirs(output_path)
                            image.save(output_file_path)
                            print("File saved at:", output_file_path.absolute())
                        except:
                            print("Unable to convert:", file_path.absolute())
                case "2":
                    if args.recursive:
                        input_files = iglob(os.path.join(path, "**/*.png"), recursive=True)
                    else:
                        input_files = iglob(os.path.join(path, "*.png"))

                    for file in input_files:
                        file_path = Path(file)
                        try:
                            image = Image.open(file_path)
                            texture = Texture3dst().fromImage(image)
                            output_file_path = Path(os.path.join(output_path, f"{file_path.stem}.3dst"))
                            if not output_path.exists():
                                os.makedirs(output_path)
                            texture.export(output_file_path)
                            print("File saved at:", output_file_path.absolute())
                        except:
                            print("Unable to convert:", file_path.absolute())
                case "3":
                    input_files = iglob(os.path.join(path.absolute(), "**"), recursive=args.recursive)

                    for file in input_files:
                        file_path = Path(file)
                        try:
                            image = Image.open(file_path)
                            texture = Texture3dst().fromImage(image)
                            output_file_path = Path(os.path.join(output_path.absolute(), f"{file_path.stem}.3dst"))
                            if not output_path.exists():
                                os.makedirs(output_path)
                            texture.export(output_file_path)
                            print("File saved at:", output_file_path.absolute())
                        except UnidentifiedImageError:
                            pass
                        except:
                            print("Unable to convert:", file_path.absolute())
                case "0":
                    sys.exit(0)
                case _:
                    print("Error: Invalid option")
            pass
        else:
            print("Error: Unable to open path")
            sys.exit(4)
    else:
        if path.exists() and path.is_file():
            try:
                texture = Texture3dst().open(path)
            except Exception as e:
                print("Error: Unable to load 3dst texture:", e)
                sys.exit(3)

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
            sys.exit(2)
        else:
            print("Error: The file doesn't exists")
            sys.exit(1)

if __name__ == "__main__":
    main()