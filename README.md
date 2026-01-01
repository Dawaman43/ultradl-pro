# UltraDL Pro 🚀

UltraDL Pro includes:

- **Linux TUI** (`ultradl`): the original Gum-based interactive UI
- **Cross-platform CLI** (`ultradl-pro`): works on Linux/macOS/Windows via Python

## Features

- 🎥 **Multi-Platform**: Support for YouTube, TikTok, Twitter, Twitch, and more.
- 🎵 **Spotify Support**: Download tracks, albums, and playlists directly.
- 🔍 **Built-in Search**: Search YouTube directly from your terminal.
- 📂 **Auto-Organizer**: Automatically sorts downloads into Video, Music, Images, etc.
- 🍪 **Cookie Integration**: Bypass bot detection by using your browser's cookies.
- ⚡ **Fast**: Uses `aria2c` for multi-threaded acceleration.
- 🎨 **Beautiful UI**: Interactive menus powered by `gum`.

## Installation

### Cross-platform (recommended)

Single-line install from PyPI:

```bash
python -m pip install -U ultradl-pro
```

Then run:

```bash
ultradl-pro
ultradl-pro "https://www.youtube.com/watch?v=D4A4APuwVgg&t=298s"
```

Notes:

- For best isolation (especially on Linux), prefer `pipx install ultradl-pro`.
- Some features (audio conversion) require `ffmpeg` installed on your system.

Install the Python CLI (`ultradl-pro`) using `pipx` (Linux/macOS/Windows):

```bash
python -m pip install --user -U pipx
python -m pipx ensurepath
pipx install .
```

Run:

```bash
ultradl-pro --help
ultradl-pro download "https://www.youtube.com/watch?v=..."
```

Windows PowerShell convenience installer:

```powershell
./install.ps1
```

### Linux TUI (legacy)

1. **Install Dependencies**:

   ```bash
   # Arch Linux
   sudo pacman -S gum aria2 yt-dlp ffmpeg nodejs
   pip install spotdl

   # Ubuntu/Debian
   sudo apt install gum aria2 yt-dlp ffmpeg nodejs
   pip install spotdl
   ```

2. **Setup**:
   ```bash
   chmod +x ultradl
   sudo ln -s $(pwd)/ultradl /usr/local/bin/ultradl
   ```

## Usage

Linux TUI:

- Run `ultradl` and follow the interactive prompts.

Cross-platform CLI:

- `ultradl-pro download <url>`
- `ultradl-pro config --download-dir <path>`
- `ultradl-pro config --cookies-browser firefox`
