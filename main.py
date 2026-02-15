#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.13,<3.14"
# dependencies = [
#     "browser_cookie3>=0.20.1",
#     "instaloader>=4.15",
#     "python-decouple>=3.8",
# ]
# [tool.uv]
# exclude-newer = "2026-02-14T00:00:00Z"
# ///

# pyright: reportMissingImports=false

"""
Usage:
    insta-dl init [browser]
    insta-dl [-o DIR] <url> [max-title-length] [key=value ...]

Commands:
    init [browser]:   Create a session from browser cookies (default: firefox)
                      Supported: arc, brave, chrome, chromium, edge, firefox,
                      librewolf, opera, opera_gx, safari, vivaldi

Args:
    url:              Instagram post or reel URL
    max-title-length: Max characters for the caption-based filename (default: 70)
    key=value:        Override Instaloader constructor defaults, e.g.:
                        save_metadata=true  download_comments=true
                        compress_json=false download_pictures=false

Options:
    -o DIR:           Output directory (default: cwd)
                      Also configurable via INSTA_DL_DIR env var or .env file.
                      Flag takes precedence over env var.
"""

import instaloader
import json
import re
import sys
from datetime import UTC, datetime, timezone
from decouple import config
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SUPPORTED_BROWSERS = [
    "arc", "brave", "chrome", "chromium", "edge", "firefox",
    "librewolf", "opera", "opera_gx", "safari", "vivaldi",
]


def init_session(browser: str = "firefox") -> None:
    """Create a session by importing cookies from a browser. Skips if valid session exists."""
    # Check for existing session
    L = instaloader.Instaloader()
    existing = load_session(L)
    if existing and L.test_login():
        print(f"Session already exists for {existing}.")
        return

    if browser not in SUPPORTED_BROWSERS:
        print(f"Unsupported browser: {browser}")
        print(f"Supported: {', '.join(SUPPORTED_BROWSERS)}")
        sys.exit(1)

    import browser_cookie3

    cookie_fn = getattr(browser_cookie3, browser, None)
    if not cookie_fn:
        print(f"browser_cookie3 does not support: {browser}")
        sys.exit(1)

    L = instaloader.Instaloader()
    cookies = cookie_fn(domain_name=".instagram.com")
    L.context._session.cookies.update(cookies)

    username = L.test_login()
    if not username:
        print(f"No active Instagram session found in {browser}.")
        print("Make sure you're logged into Instagram in that browser.")
        sys.exit(1)

    L.context.username = username
    L.save_session_to_file()
    print(f"Session saved for {username} (from {browser}).")


def load_session(loader: instaloader.Instaloader) -> str | None:
    """Load the first saved session found. Returns username or None."""
    session_dir = Path.home() / ".config" / "instaloader"
    if not session_dir.exists():
        return None
    for f in sorted(session_dir.iterdir()):
        if f.name.startswith("session-"):
            username = f.name.removeprefix("session-")
            loader.load_session_from_file(username)
            return username
    return None


def clean_url(url: str) -> str:
    """Strip query string and fragment tracking params from URL."""
    parsed = urlparse(url)
    return urlunparse(parsed._replace(query="", fragment=""))


def extract_shortcode(url: str) -> str:
    """Extract shortcode from /reel/XXX or /p/XXX URLs."""
    match = re.search(r"/(reel|p)/([^/?]+)", url)
    if not match:
        print(f"Error: could not extract shortcode from: {url}")
        sys.exit(1)
    return match.group(2)


def logged_shortcodes(profile_dir: Path) -> set[str]:
    """Return shortcodes already recorded in the profile's log."""
    log = profile_dir / "downloads.jsonl"
    if not log.exists():
        return set()
    codes = set()
    for line in log.read_text().splitlines():
        if line.strip():
            codes.add(json.loads(line)["shortcode"])
    return codes


def append_log(profile_dir: Path, post: instaloader.Post, url: str, title: str) -> None:
    """Append download entry to the profile's log file."""
    log = profile_dir / "downloads.jsonl"
    entry = {
        "shortcode": post.shortcode,
        "url": url,
        "title": title,
        "caption": post.caption,
        "profile": post.profile,
        "date_posted": post.date_utc.isoformat(),
        "typename": post.typename,
        "likes": post.likes,
        "video_view_count": post.video_view_count,
        "video_duration": post.video_duration,
        "downloaded_at": datetime.now(UTC).isoformat(),
    }
    with open(log, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def sanitize(name: str, max_len: int) -> str:
    """Truncate at word boundary and strip filesystem-unfriendly chars."""
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0]
    name = re.sub(r'[/:*?"<>|\\]', "_", name)
    return name.rstrip(". ")


def coerce(value: str) -> bool | int | float | str:
    """Coerce a string value to its appropriate Python type."""
    if value.lower() in ("true", "1", "yes"):
        return True
    if value.lower() in ("false", "0", "no"):
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def parse_args() -> tuple[str, int, Path, dict]:
    """Parse CLI args. Returns (url, max_len, output_dir, overrides)."""
    args = sys.argv[1:]
    output_dir = None
    max_len = 70

    # Pull out -o flag
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 >= len(args):
            print("Error: -o requires a directory argument")
            sys.exit(1)
        output_dir = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    # Separate key=value overrides from positional args
    positional = []
    overrides = {}
    for arg in args:
        if "=" in arg and not arg.startswith("http"):
            key, val = arg.split("=", 1)
            overrides[key] = coerce(val)
        else:
            positional.append(arg)

    match positional:
        case [url]:
            pass
        case [url, n]:
            max_len = int(n)
        case _:
            print(__doc__)
            sys.exit(1)

    # Priority: -o flag > INSTA_DL_DIR env/dotenv > cwd
    if output_dir:
        base = Path(output_dir)
    else:
        base = Path(config("INSTA_DL_DIR", default=""))
        if not base or str(base) == ".":
            base = Path.cwd()

    return url, max_len, base.expanduser().resolve(), overrides


def main():
    # Handle subcommands before arg parsing
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if sys.argv[1] == "init":
        browser = sys.argv[2] if len(sys.argv) > 2 else "firefox"
        init_session(browser)
        return

    raw_url, max_len, base, overrides = parse_args()
    url = clean_url(raw_url)
    shortcode = extract_shortcode(url)

    defaults = dict(
        dirname_pattern="{profile}",
        filename_pattern="{date_utc:%Y}/{shortcode}",
        download_video_thumbnails=False,
        save_metadata=False,
        post_metadata_txt_pattern="{caption}",
        sanitize_paths=True,
    )
    L = instaloader.Instaloader(**{**defaults, **overrides})

    username = load_session(L)
    if not username:
        print("No saved session found. Run:  insta-dl init [browser]")
        sys.exit(1)

    print(f"Fetching {shortcode} (session: {username})...")
    post = instaloader.Post.from_shortcode(L.context, shortcode)

    profile_dir = base / post.profile
    if shortcode in logged_shortcodes(profile_dir):
        print(f"Already downloaded: {shortcode}")
        return

    base.mkdir(parents=True, exist_ok=True)
    L.dirname_pattern = str(base / "{profile}")
    L.download_post(post, target=post.profile)

    # Rename files with truncated caption
    caption_first_line = (post.caption or "").split("\n")[0].strip()
    title = sanitize(caption_first_line, max_len)

    post_dir = profile_dir / str(post.date_utc.year)
    if not title:
        append_log(profile_dir, post, url, shortcode)
        print(f"Saved: {post_dir / shortcode}")
        return

    for f in sorted(post_dir.glob(f"{shortcode}*")):
        suffix = f.name.removeprefix(shortcode)  # e.g. "_1.jpg", ".mp4", ".txt"
        f.rename(f.parent / f"{title}{suffix}")

    append_log(profile_dir, post, url, title or shortcode)
    print(f"Saved: {post_dir / title}")


if __name__ == "__main__":
    main()
