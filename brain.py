"""Turn an Instagram post into a tweet draft using OpenAI."""
import base64
import os

from openai import OpenAI

from instagram import Post

TRANSCRIBE_MODEL = os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
TEXT_MODEL = os.environ.get("OPENAI_TEXT_MODEL", "gpt-4.1-mini")

INSTRUCTIONS = """You write long-form posts for a real person's X Premium account (no character limit).
Stay close to the source: keep the transcript's structure, specific claims, numbers, examples and phrasing. Do not compress it into a summary or a hook.
The source was made by someone else. Never write as if the poster did or experienced what the source describes: no first-person claims of their experience, results, jobs, or products. Rewrite personal anecdotes in third person or as general advice ("one approach that worked for a recruiter was..."), or credit the original creator by name.
Never use em dashes or en dashes (— or –). Use commas, full stops, or colons instead.
Tidy it into clean readable text with short paragraphs and line breaks; cut filler words and the creator's own calls to action like "comment X" or "follow for more" (a sign-off is added separately, do not write one).
Aim for roughly the same length as the transcript (or the caption if there is no transcript).
No links, no hashtags, no emojis unless the source is playful. Sound like a person, not a brand. Never mention Instagram or that this came from a post.
Output only the post text."""

SIGN_OFF = os.environ.get("SIGN_OFF", "If this kind of thing interests you, follow for more.")

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def transcribe(post: Post) -> str:
    assert post.audio_path
    with open(post.audio_path, "rb") as f:
        return client().audio.transcriptions.create(model=TRANSCRIBE_MODEL, file=f).text


def draft_tweet(post: Post, transcript: str | None, feedback: str | None = None, previous: str | None = None) -> str:
    parts = [f"Author: @{post.author}", f"Caption: {post.caption or '(none)'}"]
    if transcript:
        parts.append(f"Video transcript: {transcript}")
    if post.comments:
        parts.append("Top comments:\n" + "\n".join(f"- {c}" for c in post.comments))
    if previous and feedback:
        parts.append(f"Previous draft: {previous}\nRevise it per this feedback: {feedback}")

    content: list[dict] = [{"type": "input_text", "text": "\n\n".join(parts)}]
    if post.image_bytes:
        b64 = base64.b64encode(post.image_bytes).decode()
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}", "detail": "low"})

    resp = client().responses.create(
        model=TEXT_MODEL,
        instructions=INSTRUCTIONS,
        input=[{"role": "user", "content": content}],
        max_output_tokens=2000,
    )
    body = resp.output_text.strip().strip('"').replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
    return f"{body}\n\n{SIGN_OFF}" if SIGN_OFF else body
