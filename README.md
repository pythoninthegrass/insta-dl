# insta-dl

Tiny, self-contained, mostly untested Instagram downloader made possible by [instaloader](https://instaloader.github.io/index.html) ❤️

* Works with reels (✅ tested), posts (✅ tested), and highlights (☢️ yolo)
* Uses browser authentication (Brave, Chrome, Chromium, Edge, Firefox, LibreWolf, Opera, Opera GX, Safari, Vivaldi)
* Strips tracking automatically ✂️
* Saves to working directory or custom directory via
  * Environment variables
  * `-o` output flag
* Saves post text metadata
* Keeps track of already downloaded files with a JSON log
* Accepts custom `instaloader` args to override defaults

## Minimum Requirements

* git
* [uv](https://docs.astral.sh/uv/getting-started/installation/)
* macOS, Linux, WSL

## Recommended Requirements

* [mise](https://mise.jdx.dev/getting-started.html)

## Install and setup

```bash
# download repo to working directory
git clone https://github.com/pythoninthegrass/insta-dl.git

# symlink to somewhere in your path
ln -s $(pwd)/main.py ~/.local/bin/insta-dl

# create a session (one-time) — replace "firefox" with your browser
insta-dl init firefox
```

## Quickstart

### Copy a shared link from Instagram

* Open a reel > Settings (...) > Copy link
* **IMPORTANT:** quote URLs that contain `&` (shared links from Instagram do) otherwise bash interprets `&` as "run in background"

### Download a video to a specific directory

```bash
λ insta-dl https://www.instagram.com/reel/DKcxwGzoAwA -o ~/Videos/instagram
Loaded session from ~/.config/instaloader/session-USERNAME.
Fetching DKcxwGzoAwA (session: USERNAME)...
Already downloaded: DKcxwGzoAwA

λ tree ~/Videos/instagram
~/Videos/instagram
└── maxinemeixnerx
    ├── 2025
    │   ├── Did you hear about this huge win for women__ 🫨🚀.mp4
    │   ├── Did you hear about this huge win for women__ 🫨🚀.txt
    │   ├── You deserve hope! 🫵 You deserve hope! 👈 Everybody deserves hope!.mp4
    │   └── You deserve hope! 🫵 You deserve hope! 👈 Everybody deserves hope!.txt
    └── downloads.jsonl

3 directories, 5 files
```

### Download an image post (supports sidecar/carousel posts)

```bash
λ insta-dl 'https://www.instagram.com/p/DPmJxJhjBVr/?utm_source=ig_web_copy_link&igsh=MzRlODBiNWFlZA==' \
    -o ~/Pictures/instagram

λ tree ~/Pictures/instagram/poorlydrawnlines/
~/Pictures/instagram/poorlydrawnlines/
├── 2025
│   ├── Own this comic as a limited edition hand-signed print! Link in bio_1.jpg
│   ├── Own this comic as a limited edition hand-signed print! Link in bio_2.jpg
│   └── Own this comic as a limited edition hand-signed print! Link in bio.txt
└── downloads.jsonl

2 directories, 4 files
```

### Override defaults with `key=value` args (passed to instaloader constructor)

```bash
λ insta-dl 'https://www.instagram.com/p/DUv5_hAEvoS/' \
    -o ~/Videos/instagram \
    save_metadata=true download_comments=true compress_json=false

λ tree olivertree/
olivertree/
├── 2026
│   ├── Send this to someone this reminds you of_comments.json
│   ├── Send this to someone this reminds you of.json
│   ├── Send this to someone this reminds you of.mp4
│   └── Send this to someone this reminds you of.txt
└── downloads.jsonl

2 directories, 5 files
```

## Further Reading

* [Command Line Options — Instaloader documentation](https://instaloader.github.io/cli-options.html)
* [Running scripts | uv](https://docs.astral.sh/uv/guides/scripts/)
