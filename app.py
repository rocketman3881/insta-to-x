"""WhatsApp (Twilio) -> Instagram post -> AI tweet draft -> approve -> post to X."""
import logging
import os
import shutil
import threading

import tweepy
from dotenv import load_dotenv
from flask import Flask, abort, request
from twilio.request_validator import RequestValidator
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

import brain  # noqa: E402  (needs env loaded)
import instagram  # noqa: E402

log = logging.getLogger("insta-to-x")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = Flask(__name__)
# ngrok terminates TLS; Twilio signs the public https URL, so trust forwarded scheme/host.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
TWILIO_FROM = os.environ["TWILIO_WHATSAPP_FROM"]  # e.g. whatsapp:+14155238886
ALLOWED = os.environ["ALLOWED_WHATSAPP_NUMBER"]  # e.g. whatsapp:+447700900000
twilio = TwilioClient(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
validator = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"])
x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
)


def send(body: str) -> None:
    twilio.messages.create(from_=TWILIO_FROM, to=ALLOWED, body=body[:1500])


def process_url(url: str) -> None:
    post = None
    try:
        post = instagram.fetch(url)
        transcript = brain.transcribe(post) if post.audio_path else None
        draft = brain.draft_tweet(post, transcript)
    except Exception:
        log.exception("processing failed for %s", url)
        send("Couldn't process that post. It may be private, deleted, or Instagram is blocking fetches right now.")
        return
    finally:
        if post and post.audio_path:
            shutil.rmtree(post.audio_path.parent, ignore_errors=True)
    try:
        tweet_id = x_client.create_tweet(text=draft).data["id"]
        send(f"Posted: https://x.com/i/status/{tweet_id}\n\n{draft}")
    except Exception as e:
        log.exception("X post failed")
        send(f"X rejected the post: {e}\n\nDraft was:\n\n{draft}")


@app.post("/whatsapp")
def whatsapp() -> str:
    sig = request.headers.get("X-Twilio-Signature", "")
    if not validator.validate(request.url, request.form, sig):
        abort(403)
    if request.form.get("From") != ALLOWED:
        abort(403)

    text = (request.form.get("Body") or "").strip()
    reply = MessagingResponse()

    url = instagram.extract_url(text)
    if url:
        threading.Thread(target=process_url, args=(url,), daemon=True).start()
        reply.message("On it, posting to X…")
    else:
        reply.message("Send me an Instagram post or reel link.")
    return str(reply)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5050")))
