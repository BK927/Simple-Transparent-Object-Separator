# Simple Transparent Object Separator

A lightweight tool to automatically split transparent PNG images into separate object files.

## Features

- **Smart Cleanup**: Automatically detects and extracts separate objects from a transparent background.
- **Drag & Drop**: Simply drag PNG files onto the application window.
- **Noise Filtering**: Option to ignore small artifacts (default: <= 128px).
- **Uniform Output**: Option to resize all extracted images to match the smallest one.
- **Lightweight**: Built with Pillow and Tkinter for fast startup and minimal size.

## How to Use

1. Run `SimpleTransparentObjectSeparator.exe`.
2. (Optional) Set **Min Size** to filter out small pixel noise.
3. (Optional) Check **Unify to smallest size** if you want all output images to have the same dimensions.
4. Drag and drop one or multiple PNG files into the window.
5. The processed images will be saved in an `output` folder next to the executable.

## Development

### Requirements
- Python 3.x
- `uv` (for dependency management)

### Setup
```bash
uv sync
```

### Build Executable
To build a standalone `.exe`:
```bash
uv run pyinstaller --onefile --windowed --name "SimpleTransparentObjectSeparator" --clean --noconfirm app.py
```

## Tech Stack
- **GUI**: `tkinter`, `tkinterdnd2`
- **Processing**: `Pillow`, `scipy`
- **Build**: `PyInstaller`
