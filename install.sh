#!/bin/bash

# UltraDL Pro Installer

echo "🚀 Installing UltraDL Pro..."

# Prefer cross-platform Python CLI install when possible
if command -v pipx &> /dev/null; then
    echo "📦 Installing cross-platform CLI (ultradl-pro) via pipx..."
    pipx install . --force || {
        echo "⚠️ pipx install failed; continuing with legacy setup..."
    }
else
    echo "ℹ️ pipx not found. For cross-platform install, use: python -m pip install --user pipx && pipx install ."
fi

# Check for dependencies
for tool in gum aria2c yt-dlp ffmpeg node; do
    if ! command -v $tool &> /dev/null; then
        echo "⚠️ Warning: $tool is not installed. Please install it for full functionality."
    fi
done

# Make script executable
chmod +x ultradl

# Create symlink
sudo ln -sf "$(pwd)/ultradl" /usr/local/bin/ultradl

echo "✅ Installation complete! You can now run 'ultradl' from anywhere."
echo "✅ Cross-platform CLI (Python) is 'ultradl-pro' (if installed via pipx)."
