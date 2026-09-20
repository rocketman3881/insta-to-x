"""Fetch an Instagram post via Apify: caption, comments, and media (audio file or image bytes)."""
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

SHORTCODE_RE = re.compile(r"instagram\.com/(?:[\w.]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")
MAX_COMMENTS = 15
MAX_MEDIA_BYTES = 200 * 1024 * 1024
APIFY_RUN_URL = "https://api.apify.com/v2/acts/apify~instagram-scraper/run-sync-get-dataset-items"


@dataclass
class Post:
    url: str
    author: str
    caption: str
    comments: list[str] = field(default_factory=list)
    audio_path: Path | None = None  # set for videos (mp3)
    image_bytes: bytes | None = None  # set for images


def extract_url(text: str) -> str | None:
    m = SHORTCODE_RE.search(text)
    return f"https://www.instagram.com/p/{m.group(1)}/" if m else None


def _apify_post(url: str) -> dict:
    r = requests.post(
        APIFY_RUN_URL,
        params={"token": os.environ["APIFY_TOKEN"], "timeout": 120},
        json={"directUrls": [url], "resultsType": "posts", "resultsLimit": 1},
        timeout=150,
    )
    r.raise_for_status()
    items = r.json()
    if not items:
        raise ValueError("Apify returned nothing")
    item = items[0]
    if item.get("error"):
        raise ValueError(f"Instagram: {item.get('errorDescription') or item['error']}")
    return item


def _download(url: str, dest: Path, attempts: int = 3) -> None:
    for attempt in range(1, attempts + 1):
        try:
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                size = 0
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        size += len(chunk)
                        if size > MAX_MEDIA_BYTES:
                            raise ValueError("media too large")
                        f.write(chunk)
            return
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError):
            if attempt == attempts:
                raise
            time.sleep(2 * attempt)


def _has_audio(video: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, timeout=60,
    )
    return "audio" in out.stdout


def _extract_audio(video: Path) -> Path:
    audio = video.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", str(audio)],
        check=True, timeout=300,
    )
    return audio


def fetch(url: str) -> Post:
    item = _apify_post(url)
    # For carousels, use the first slide.
    media = (item.get("childPosts") or [item])[0]
    video_url, image_url = media.get("videoUrl"), media.get("displayUrl")
    if not (video_url or image_url):
        raise ValueError("post has no downloadable media")

    comments = [c["text"] for c in (item.get("latestComments") or [])[:MAX_COMMENTS] if c.get("text")]
    post = Post(url=url, author=item.get("ownerUsername", "unknown"), caption=item.get("caption") or "", comments=comments)

    tmp = Path(tempfile.mkdtemp(prefix="ig_"))
    if video_url:
        # Reels usually ship audio as a separate stream; older posts mux it into the video.
        src = tmp / "video.mp4"
        _download(media.get("audioUrl") or video_url, src)
        if _has_audio(src):
            post.audio_path = _extract_audio(src)
        src.unlink()
    # Silent videos fall through to the thumbnail so the model still sees something.
    if not post.audio_path:
        if image_url:
            image = tmp / "image.jpg"
            _download(image_url, image)
            post.image_bytes = image.read_bytes()
        shutil.rmtree(tmp, ignore_errors=True)
    return post
