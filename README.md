# insta-to-x

Share an Instagram link to WhatsApp → it's rewritten as a long-form post and published to X automatically. You get the link back on WhatsApp.

Videos are transcribed; images are analysed; caption and top comments are used for context.

## Setup (once)

1. `cp .env.example .env` and fill in the keys (links inside the file).
2. `brew install ngrok` and `ngrok config add-authtoken <token>` (free account at ngrok.com).
3. Twilio WhatsApp sandbox: send the "join …" code it shows you from your phone.
4. Apify (fetches Instagram posts; free tier covers ~1,000 posts/month): apify.com → Settings → API tokens → `APIFY_TOKEN`.

## Run

```
./run.sh
```

Paste the printed URL into Twilio → Messaging → Try it out → Send a WhatsApp message → Sandbox settings → *When a message comes in*. Save.

## Use

- Send an Instagram post/reel link → posted to X in ~20–60s, link sent back.
- Delete on X if you don't like it.

## Notes

- Twilio sandbox needs re-joining every 72h. For permanent use, register a WhatsApp sender in Twilio (~$0.005/msg).
- Only messages from `ALLOWED_WHATSAPP_NUMBER` are accepted; Twilio signatures are verified.
- Cost: ~1–3¢ per post (transcription + drafting + X's $0.015/tweet).
