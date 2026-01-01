import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from platformdirs import user_config_dir
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn


console = Console()


@dataclass
class AppConfig:
    download_dir: Path
    cookies_browser: Optional[str]


def _legacy_config_path() -> Path:
    return Path.home() / ".ultradl_config"


def _config_path() -> Path:
    return Path(user_config_dir("ultradl-pro")) / "config.ini"


def _parse_simple_kv(path: Path) -> dict:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def load_config() -> AppConfig:
    # Prefer new config location, but also read legacy ~/.ultradl_config if present
    dl_default = Path.home() / "Downloads"
    cookies_default: Optional[str] = None

    new_kv = _parse_simple_kv(_config_path())
    legacy_kv = _parse_simple_kv(_legacy_config_path())

    download_dir = Path(new_kv.get("DOWNLOAD_DIR", legacy_kv.get("DOWNLOAD_DIR", str(dl_default)))).expanduser()
    cookies_browser = new_kv.get("COOKIES_BROWSER", legacy_kv.get("COOKIES_BROWSER", "")).strip() or None

    return AppConfig(download_dir=download_dir, cookies_browser=cookies_browser)


def save_config(cfg: AppConfig) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"DOWNLOAD_DIR={cfg.download_dir}\nCOOKIES_BROWSER={cfg.cookies_browser or ''}\n"
    path.write_text(content, encoding="utf-8")


def is_youtube(url: str) -> bool:
    return "youtube.com" in url or "youtu.be" in url


def _yt_dlp_available() -> bool:
    try:
        import yt_dlp  # noqa: F401

        return True
    except Exception:
        return False


def _run_spotdl(url: str, out_dir: Path) -> int:
    exe = "spotdl.exe" if os.name == "nt" else "spotdl"
    if not shutil_which(exe):
        console.print("[red]spotdl is not installed.[/red] Install with: `pipx inject ultradl-pro spotdl` or `pip install ultradl-pro[spotify]`.")
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)
    return subprocess.call([exe, url, "--output", str(out_dir)])


def shutil_which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def download_with_ytdlp(
    url: str,
    out_dir: Path,
    cookies_browser: Optional[str],
    audio_format: Optional[str],
) -> int:
    if not _yt_dlp_available():
        console.print("[red]Python dependency `yt-dlp` is not installed.[/red]")
        return 2

    import yt_dlp

    out_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts: dict = {
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        # YouTube JS challenges: use node runtime + fetch EJS scripts from GitHub
        "js_runtimes": ["node"],
        "remote_components": ["ejs:github"],
        "extractor_args": {"youtube": {"player_client": ["tv"], "player_skip": ["webpage", "configs"]}},
    }

    if cookies_browser:
        # yt-dlp expects e.g. "firefox" or "chrome" etc
        ydl_opts["cookiesfrombrowser"] = (cookies_browser,)

    if audio_format:
        ydl_opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": audio_format,
                        "preferredquality": "0" if audio_format == "mp3" else None,
                    }
                ],
            }
        )
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"

    total_holder = {"total": None}

    progress = Progress(
        TextColumn("[bold]Downloading[/bold]"),
        BarColumn(bar_width=None),
        TextColumn("{task.percentage:>3.0f}%"),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    )

    task_id = progress.add_task("download", total=100)

    def hook(d: dict) -> None:
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes")
            if total and downloaded is not None:
                total_holder["total"] = total
                pct = max(0.0, min(100.0, downloaded * 100.0 / total))
                progress.update(task_id, completed=pct)
        elif status == "finished":
            progress.update(task_id, completed=100)

    ydl_opts["progress_hooks"] = [hook]

    try:
        with progress:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        return 0
    except Exception as e:
        console.print(f"[red]Download failed:[/red] {e}")
        console.print("Tip: If you get bot-check errors, set cookies browser via `ultradl-pro config --cookies firefox`.")
        return 1


def cmd_config(args: argparse.Namespace) -> int:
    cfg = load_config()
    changed = False

    if args.download_dir:
        cfg.download_dir = Path(args.download_dir).expanduser()
        changed = True

    if args.cookies_browser is not None:
        cfg.cookies_browser = args.cookies_browser or None
        changed = True

    if changed:
        save_config(cfg)
        console.print("[green]Config updated[/green]")

    console.print(f"Download dir: {cfg.download_dir}")
    console.print(f"Cookies browser: {cfg.cookies_browser or 'none'}")
    console.print(f"Config file: {_config_path()}")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    cfg = load_config()

    url = args.url
    out_dir = Path(args.dir).expanduser() if args.dir else cfg.download_dir
    cookies_browser = args.cookies_browser or cfg.cookies_browser

    # Very simple routing
    if "spotify" in url:
        console.print("[yellow]Spotify URL detected.[/yellow]")
        return _run_spotdl(url, out_dir)

    audio_format = args.audio
    return download_with_ytdlp(url, out_dir, cookies_browser, audio_format)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ultradl-pro", description="UltraDL Pro (cross-platform CLI)")
    sub = p.add_subparsers(dest="cmd")

    p_dl = sub.add_parser("download", help="Download a URL")
    p_dl.add_argument("url")
    p_dl.add_argument("--dir", help="Output directory (defaults to config)")
    p_dl.add_argument("--cookies-browser", help="e.g. firefox, chrome, edge")
    p_dl.add_argument("--audio", choices=["mp3", "flac"], help="Audio-only download and convert")
    p_dl.set_defaults(func=cmd_download)

    p_cfg = sub.add_parser("config", help="View/update config")
    p_cfg.add_argument("--download-dir", help="Default download directory")
    p_cfg.add_argument("--cookies-browser", nargs="?", const="", help="Set browser for cookies (pass empty to clear)")
    p_cfg.set_defaults(func=cmd_config)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()

    if not argv:
        parser.print_help(sys.stdout)
        return 0

    # Convenience: `ultradl-pro <url>` behaves like `ultradl-pro download <url>`
    if argv and argv[0].startswith(("http://", "https://")):
        argv = ["download", *argv]

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help(sys.stdout)
        return 0

    return int(args.func(args))
