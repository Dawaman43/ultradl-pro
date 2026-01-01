#!/bin/bash

# ==========================================
# ULTRADL PRO - The Ultimate Arch Downloader
# Powered by Gum, Aria2, yt-dlp, and SpotDL
# ==========================================

# --- Configuration ---
DOWNLOAD_DIR=$(grep "DOWNLOAD_DIR=" "$HOME/.ultradl_config" 2>/dev/null | cut -d'=' -f2)
DOWNLOAD_DIR="${DOWNLOAD_DIR:-$HOME/Downloads}"
COOKIES_BROWSER=$(grep "COOKIES_BROWSER=" "$HOME/.ultradl_config" 2>/dev/null | cut -d'=' -f2)
HISTORY_FILE="$HOME/.ultradl_history"
# Use /dev/shm for speed if available, else /tmp
if [ -d "/dev/shm" ]; then
    TEMP_DIR="/dev/shm/ultradl_buffer"
else
    TEMP_DIR="/tmp/ultradl_buffer"
fi

# --- Styling & UI Functions ---
logo() {
    clear
    FREE_SPACE=$(df -h "$DOWNLOAD_DIR" | awk 'NR==2 {print $4}')
    gum style \
        --border double \
        --margin "1 1" \
        --padding "1 2" \
        --border-foreground 212 \
        --foreground 212 \
        "🚀 ULTRA DL PRO | THE ULTIMATE DOWNLOADER" \
        "📂 Storage: $DOWNLOAD_DIR ($FREE_SPACE free)"
}

show_success() {
    gum style --foreground 82 "✅ $1"
}

show_error() {
    gum style --foreground 196 "❌ $1"
}

# --- Check Dependencies ---
check_deps() {
    local missing=()
    for tool in gum aria2c yt-dlp spotdl ffmpeg; do
        if ! command -v $tool &> /dev/null; then
            missing+=("$tool")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        logo
        show_error "Missing dependencies: ${missing[*]}"
        echo "Please install them using your package manager."
        echo "Example: sudo pacman -S gum aria2 yt-dlp ffmpeg && pip install spotdl"
        exit 1
    fi

    # Check for JS runtime (CRITICAL for YouTube n-parameter)
    if ! command -v node &> /dev/null && ! command -v quickjs &> /dev/null; then
        logo
        show_error "No JavaScript runtime found (node or quickjs)!"
        echo "YouTube has increased security. You MUST install Node.js or QuickJS"
        echo "to download videos, otherwise the 'n-challenge' will fail."
        echo ""
        echo "Fix: sudo pacman -S nodejs  OR  sudo apt install nodejs"
        echo ""
        gum confirm "Continue anyway? (Downloads will likely fail)" || exit 1
    fi
}

# --- TUI helpers for cleaner downloads ---
render_status_line() {
    local msg="$1"
    local cols
    cols=$(tput cols 2>/dev/null || echo 120)
    # Clear line + print truncated/padded message
    printf "\r\033[2K%.*s" "$cols" "$msg"
}

run_with_clean_progress() {
    # Runs a command, writes all output to a log, and only shows a single status line.
    # Usage: run_with_clean_progress <log_file> <cmd...>
    local log_file="$1"
    shift

    mkdir -p "$(dirname "$log_file")" 2>/dev/null || true
    : > "$log_file"

    set -o pipefail
    stdbuf -oL -eL "$@" 2>&1 | while IFS= read -r line; do
        echo "$line" >> "$log_file"

        # Prefer aria2c's progress line when present
        if [[ "$line" =~ ^\[# ]]; then
            render_status_line "$line"
        # Fall back to yt-dlp download status / sleep lines
        elif [[ "$line" =~ ^\[download\] ]]; then
            render_status_line "$line"
        # Surface errors/warnings as the status line without flooding
        elif [[ "$line" =~ ^(ERROR:|WARNING:) ]]; then
            render_status_line "$line"
        fi
    done

    local rc=${PIPESTATUS[0]}
    printf "\n"
    return $rc
}

# --- The Engine Room ---
download_video() {
    URL=$1
    logo
    echo "🔗 URL: $URL"

    # YouTube now requires EJS challenge solver scripts + a JS runtime.
    # Third-party yt-dlp packages (e.g. pacman) may not bundle these scripts.
    JS_RUNTIME_ARG=""
    if command -v node &> /dev/null; then
        JS_RUNTIME_ARG="--js-runtimes node"
    elif command -v quickjs &> /dev/null; then
        JS_RUNTIME_ARG="--js-runtimes quickjs"
    fi
    REMOTE_COMPONENTS_ARG="--remote-components ejs:github"
    YT_EXTRACTOR_ARG='--extractor-args youtube:player_client=tv;player_skip=webpage,configs'

    mkdir -p "$TEMP_DIR" 2>/dev/null || true

    # Add cookies if configured (must be defined before any yt-dlp calls)
    COOKIE_ARG=""
    if [ -n "$COOKIES_BROWSER" ]; then
        COOKIE_ARG="--cookies-from-browser $COOKIES_BROWSER"
    fi
    
    # Check if it's a playlist
    PLAYLIST_ARG="--no-playlist"
    if [[ "$URL" == *"list="* ]] || [[ "$URL" == *"/playlist"* ]]; then
        if gum confirm "This looks like a playlist. Download entire playlist?"; then
            PLAYLIST_ARG="--yes-playlist"
        fi
    fi

    MODE=$(gum choose "Quick Download (Best)" "Select Quality/Format" "Audio Only (MP3)" "Audio Only (FLAC)")
    
    case $MODE in
        "Quick Download (Best)")
            FORMAT="bestvideo+bestaudio/best"
            EXT_ARGS=""
            ;;
        "Select Quality/Format")
            gum spin --spinner dot --title "🔍 Fetching available formats..." -- \
                yt-dlp $COOKIE_ARG $JS_RUNTIME_ARG $REMOTE_COMPONENTS_ARG $YT_EXTRACTOR_ARG -F "$URL" > /tmp/ultradl_formats
            
            # Show formats and let user pick
            FORMAT_ID=$(grep -E '^[0-9]+' /tmp/ultradl_formats | gum filter --placeholder "Select Format ID (e.g. 137+140)..." | awk '{print $1}')
            if [ -z "$FORMAT_ID" ]; then return 1; fi
            FORMAT="$FORMAT_ID"
            EXT_ARGS=""
            ;;
        "Audio Only (MP3)")
            FORMAT="bestaudio/best"
            EXT_ARGS="-x --audio-format mp3 --audio-quality 0"
            ;;
        "Audio Only (FLAC)")
            FORMAT="bestaudio/best"
            EXT_ARGS="-x --audio-format flac"
            ;;
    esac

    echo "$(date '+%Y-%m-%d %H:%M:%S') | VIDEO | $URL" >> "$HISTORY_FILE"

    local log_file="$TEMP_DIR/ultradl_last_download.log"

    # Run yt-dlp with clean single-line progress; full logs are saved.
    run_with_clean_progress "$log_file" \
        yt-dlp "$URL" \
            $PLAYLIST_ARG \
            $COOKIE_ARG \
            $JS_RUNTIME_ARG \
            $REMOTE_COMPONENTS_ARG \
            $YT_EXTRACTOR_ARG \
            --output "$TEMP_DIR/%(title)s.%(ext)s" \
            --format "$FORMAT" \
            --embed-metadata \
            --embed-thumbnail \
            $EXT_ARGS \
            --external-downloader aria2c \
            --external-downloader-args "aria2c:-x 16 -s 16 -k 1M"
    
    return $?
}

search_youtube() {
    QUERY=$(gum input --placeholder "Search YouTube...")
    if [ -z "$QUERY" ]; then return; fi
    
    logo
    echo "🔍 Searching for: $QUERY"
    
    # Get top 10 results
    gum spin --spinner dot --title "Searching..." -- \
        yt-dlp "ytsearch10:$QUERY" --get-title --get-id --flat-playlist > /tmp/ultradl_search
    
    # Format results for gum choose
    # Each line in /tmp/ultradl_search is title then id on next line? No, yt-dlp output varies.
    # Let's use a better way to get title and id.
    yt-dlp "ytsearch10:$QUERY" --print "%(title)s [%(id)s]" --flat-playlist > /tmp/ultradl_search
    
    SELECTED=$(gum filter < /tmp/ultradl_search)
    if [ -z "$SELECTED" ]; then return; fi
    
    # Extract ID from [id]
    VIDEO_ID=$(echo "$SELECTED" | grep -o '\[.*\]$' | tr -d '[]')
    download_video "https://www.youtube.com/watch?v=$VIDEO_ID"
}

download_spotify() {
    URL=$1
    echo "$(date '+%Y-%m-%d %H:%M:%S') | SPOTIFY | $URL" >> "$HISTORY_FILE"
    cd "$TEMP_DIR" || return 1
    spotdl "$URL"
    return $?
}

download_direct() {
    URL=$1
    echo "$(date '+%Y-%m-%d %H:%M:%S') | DIRECT | $URL" >> "$HISTORY_FILE"
    
    FILENAME=$(basename "$URL" | cut -d'?' -f1)
    if [ -z "$FILENAME" ]; then FILENAME="download_$(date +%s)"; fi
    
    aria2c "$URL" \
        --dir="$TEMP_DIR" \
        --out="$FILENAME" \
        -x 16 -s 16 -k 1M \
        --file-allocation=none
    return $?
}

manage_settings() {
    logo
    ACTION=$(gum choose "Change Download Directory" "Set Browser for Cookies" "Update yt-dlp" "Back")
    
    case $ACTION in
        "Change Download Directory")
            NEW_DIR=$(gum input --placeholder "Enter absolute path (e.g. /home/user/Videos)..." --value "$DOWNLOAD_DIR")
            if [ -d "$NEW_DIR" ]; then
                sed -i '/DOWNLOAD_DIR=/d' "$HOME/.ultradl_config" 2>/dev/null
                echo "DOWNLOAD_DIR=$NEW_DIR" >> "$HOME/.ultradl_config"
                DOWNLOAD_DIR="$NEW_DIR"
                show_success "Directory updated to $NEW_DIR"
            else
                show_error "Invalid directory!"
            fi
            sleep 1
            ;;
        "Set Browser for Cookies")
            BROWSER=$(gum choose "none" "chrome" "firefox" "brave" "edge" "opera" "safari" "vivaldi" "chromium")
            sed -i '/COOKIES_BROWSER=/d' "$HOME/.ultradl_config" 2>/dev/null
            if [ "$BROWSER" != "none" ]; then
                echo "COOKIES_BROWSER=$BROWSER" >> "$HOME/.ultradl_config"
                COOKIES_BROWSER="$BROWSER"
                show_success "Cookies will be pulled from $BROWSER"
            else
                COOKIES_BROWSER=""
                show_success "Cookies disabled."
            fi
            sleep 1
            ;;
        "Update yt-dlp")
            gum spin --spinner dot --title "Updating yt-dlp..." -- yt-dlp -U
            show_success "Update check complete."
            sleep 1
            ;;
    esac
}

# --- The Sorter (Auto-Organizer) ---
sort_files() {
    gum style --foreground 99 "📂 Sorting & Categorizing..."
    
    mkdir -p "$DOWNLOAD_DIR"/{Video,Music,Archives,Images,Documents,Programs}

    # Move from RAM Buffer to Disk
    cd "$TEMP_DIR" || return

    # Videos
    find . -type f \( -iname "*.mp4" -o -iname "*.mkv" -o -iname "*.webm" \) -exec mv {} "$DOWNLOAD_DIR/Video/" \;
    # Audio
    find . -type f \( -iname "*.mp3" -o -iname "*.wav" -o -iname "*.flac" -o -iname "*.m4a" \) -exec mv {} "$DOWNLOAD_DIR/Music/" \;
    # Archives
    find . -type f \( -iname "*.zip" -o -iname "*.rar" -o -iname "*.7z" -o -iname "*.iso" \) -exec mv {} "$DOWNLOAD_DIR/Archives/" \;
    # Images
    find . -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.gif" \) -exec mv {} "$DOWNLOAD_DIR/Images/" \;
    # Docs
    find . -type f \( -iname "*.pdf" -o -iname "*.doc*" -o -iname "*.epub" \) -exec mv {} "$DOWNLOAD_DIR/Documents/" \;
    # Programs
    find . -type f \( -iname "*.exe" -o -iname "*.AppImage" -o -iname "*.sh" \) -exec mv {} "$DOWNLOAD_DIR/Programs/" \;
    
    # Catch-all
    find . -type f -exec mv {} "$DOWNLOAD_DIR/" \;
    
    # Cleanup
    rm -rf "$TEMP_DIR"/*
}

# --- Main Logic ---
main() {
    check_deps
    mkdir -p "$TEMP_DIR"

    while true; do
        logo
        CHOICE=$(gum choose \
            "🔗 Download URL" \
            "🔍 Search & Download" \
            "🎵 Spotify Downloader" \
            "📋 Batch Download" \
            "📜 View History" \
            "⚙️ Settings" \
            "🧹 Clear Buffer" \
            "🚪 Exit")

        case $CHOICE in
            "🔗 Download URL")
                URL=$(gum input --placeholder "Paste link here (YouTube, Twitter, TikTok, etc.)...")
                if [ -z "$URL" ]; then continue; fi

                if [[ "$URL" == *"spotify"* ]]; then
                    download_spotify "$URL"
                elif [[ "$URL" == *"youtube"* ]] || [[ "$URL" == *"youtu.be"* ]] || [[ "$URL" == *"twitch"* ]] || [[ "$URL" == *"twitter"* ]] || [[ "$URL" == *"tiktok"* ]]; then
                    download_video "$URL"
                else
                    # Try yt-dlp first as it supports almost everything
                    if yt-dlp --get-id "$URL" &>/dev/null; then
                        download_video "$URL"
                    else
                        download_direct "$URL"
                    fi
                fi
                
                if [ $? -eq 0 ]; then
                    sort_files
                    show_success "Task Completed!"
                else
                    show_error "Download failed or was cancelled."
                    echo "--------------------------------------------------"
                    echo "🛠️  TROUBLESHOOTING YOUTUBE ERRORS:"
                    echo "1. Install Node.js: 'sudo pacman -S nodejs' or 'sudo apt install nodejs'"
                    echo "2. Update yt-dlp: Go to Settings -> Update yt-dlp"
                    echo "3. Check Cookies: Ensure you are logged into YouTube in the browser you selected."
                    echo "4. Try 'Select Quality/Format' mode if 'Quick Download' fails."
                    echo "--------------------------------------------------"
                fi
                gum confirm "Back to menu?" || exit 0
                ;;

            "🔍 Search & Download")
                search_youtube
                if [ $? -eq 0 ]; then
                    sort_files
                    show_success "Task Completed!"
                else
                    show_error "Download failed or was cancelled."
                fi
                gum confirm "Back to menu?" || exit 0
                ;;

            "🎵 Spotify Downloader")
                URL=$(gum input --placeholder "Paste Spotify Track/Playlist/Album URL...")
                if [ -n "$URL" ]; then
                    download_spotify "$URL"
                    if [ $? -eq 0 ]; then
                        sort_files
                        show_success "Spotify Download Complete!"
                    else
                        show_error "Spotify download failed."
                    fi
                fi
                gum confirm "Back to menu?" || exit 0
                ;;

            "📋 Batch Download")
                FILE=$(gum file "$HOME")
                if [ -f "$FILE" ]; then
                    # Use yt-dlp for batch if possible
                    yt-dlp -a "$FILE" -o "$TEMP_DIR/%(title)s.%(ext)s" --external-downloader aria2c
                    sort_files
                    show_success "Batch Complete!"
                fi
                gum confirm "Back to menu?" || exit 0
                ;;

            "📜 View History")
                if [ -f "$HISTORY_FILE" ]; then
                    SELECTED_HIST=$(gum filter < "$HISTORY_FILE")
                    if [ -n "$SELECTED_HIST" ]; then
                        HIST_URL=$(echo "$SELECTED_HIST" | awk -F' | ' '{print $NF}')
                        if gum confirm "Re-download $HIST_URL?"; then
                            # Recursive call to main logic for this URL
                            # For simplicity, just trigger the smart detection
                            if [[ "$HIST_URL" == *"spotify"* ]]; then download_spotify "$HIST_URL"; else download_video "$HIST_URL"; fi
                            sort_files
                        fi
                    fi
                else
                    show_error "No history yet."
                    sleep 1
                fi
                ;;
                
            "⚙️ Settings")
                manage_settings
                ;;

            "🧹 Clear Buffer")
                rm -rf "$TEMP_DIR"/*
                show_success "RAM Buffer Cleared."
                sleep 1
                ;;

            "🚪 Exit")
                rm -rf "$TEMP_DIR"
                clear
                exit 0
                ;;
        esac
    done
}

main
