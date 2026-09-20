# Instagram → X Auto-Poster: Complete Setup Guide

Send an Instagram reel or post link to a WhatsApp number. Within about a minute it is transcribed (video) or analysed (image), rewritten as a long-form post in third person, and published to your X account. You get the X link back on WhatsApp.

Time to set up: about 45 minutes. Cost to run: roughly 2p per post. Skill needed: copy-paste and follow instructions. No coding.

---

## 1. How it works

```
WhatsApp (you)  →  Twilio  →  your Mac (bot)  →  Apify (fetches the Instagram post)
                                    ↓
                              OpenAI (transcribes audio, reads image, writes the post)
                                    ↓
                              X API (publishes)  →  WhatsApp gets the link back
```

- **Twilio** gives you a WhatsApp number that forwards messages to your computer.
- **ngrok** gives your computer a public web address so Twilio can reach it.
- **Apify** downloads the Instagram post (caption, comments, video/image). Instagram blocks direct scraping, so this paid-but-cheap service is required.
- **OpenAI** does the transcription and writing.
- **X API** posts the result. Pay-per-use, ~1.5p per post.

---

## 2. Before you start

You need:
- A Mac (Windows/Linux work too but the commands below are for Mac).
- An X account, ideally Premium (long posts need it).
- Your phone with WhatsApp.
- A debit card for small top-ups: ~$5 X credits, ~$5 OpenAI credits. Twilio, ngrok and Apify are free at this volume.

Install the tools (paste each into Terminal, press Enter):

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install uv ffmpeg ngrok
```

---

## 3. Get the code

Copy the `insta-to-x` folder from whoever gave you this guide. It contains:

| File | What it does |
|---|---|
| `app.py` | Receives WhatsApp messages, runs the pipeline, posts to X |
| `instagram.py` | Fetches the post via Apify, extracts audio |
| `brain.py` | OpenAI: transcription + writing the post (the style rules live here) |
| `run.sh` | Starts everything and prints the URL to paste into Twilio |
| `.env.example` | Template for your keys |

**Do not copy the `.env` file** from someone else. It contains their private keys.

Then in Terminal:

```
cd ~/insta-to-x
uv sync
cp .env.example .env
```

Open `.env` in TextEdit (or any editor). You'll fill it in as you go through section 4.

---

## 4. Get your keys

### 4a. OpenAI

1. Go to https://platform.openai.com/api-keys → **Create new secret key** → copy it.
2. Paste into `.env` as `OPENAI_API_KEY=sk-...`
3. Go to Billing → add **$5** credit. Keys don't work with a $0 balance.

### 4b. X (Twitter)

1. Go to https://developer.x.com → sign in with your X account → create a project and app (any names).
2. In the app: **Settings → User authentication settings → Set up**.
   - App permissions: **Read and write**
   - Type of app: **Web App**
   - Callback URL: `http://localhost`
   - Website URL: `https://x.com`
   - Save.
3. **Keys and tokens** tab:
   - Under *OAuth 1.0 Keys*: **Consumer Key** → Regenerate → copy both values into `.env` as `X_API_KEY` and `X_API_SECRET`.
   - **Access Token** → Regenerate → must say "Read and write" → copy both into `.env` as `X_ACCESS_TOKEN` and `X_ACCESS_TOKEN_SECRET`.
   - Ignore everything under *OAuth 2.0 Keys* and the Bearer Token.
4. **Important:** if you generated the access token *before* setting Read and write, regenerate it again. A read-only token gives "403 Forbidden" when posting.
5. Project page → **Manage** (next to "Pay Per Use") → buy **$5** of credits. Without this you get "402 credits depleted".

### 4c. Twilio (WhatsApp)

1. Go to https://twilio.com → sign up (free trial is fine). Skip or answer the onboarding survey with anything.
2. On the Console home page, find the **Account Info** box → copy **Account SID** and **Auth Token** (click the eye icon) into `.env` as `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN`.
3. Put your own phone number in `.env` as `ALLOWED_WHATSAPP_NUMBER=whatsapp:+44...` (full international format, no spaces). Only this number can use the bot.
4. Leave `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886` as is (that's Twilio's sandbox number).
5. Left sidebar → **Messaging → Try it out → Send a WhatsApp message**. It shows a code like `join something-word`. On your phone, send that exact message on WhatsApp to **+1 415 523 8886**. You'll get "You are all set!" back.

### 4d. Apify (Instagram fetching)

1. Go to https://apify.com → sign up (free).
2. **Settings → API & Integrations → Personal API tokens** → copy the token into `.env` as `APIFY_TOKEN=apify_api_...`
3. Free tier includes $5/month of usage, enough for ~1,000 posts.

### 4e. ngrok (public URL)

1. Go to https://ngrok.com → sign up (free).
2. Dashboard → **Your Authtoken** → copy it.
3. In Terminal: `ngrok config add-authtoken PASTE_TOKEN_HERE`

Your `.env` should now have every line filled in.

---

## 5. Run it

In Terminal:

```
cd ~/insta-to-x
./run.sh
```

After a few seconds it prints:

```
==> Paste this into Twilio sandbox 'When a message comes in':  https://something.ngrok-free.dev/whatsapp
```

Copy that URL. Then:

1. Twilio → **Messaging → Try it out → Send a WhatsApp message** → **Sandbox settings** tab (at the top of the page).
2. Paste the URL into **When a message comes in**. Method: **POST**. Click **Save**.

Leave the Terminal window open. The bot runs as long as it's open and your Mac is awake.

---

## 6. Use it

On WhatsApp, send any Instagram post or reel link to +1 415 523 8886.

- You get "On it, posting to X…" immediately.
- 20–60 seconds later: "Posted: https://x.com/..." plus the text.
- If something fails, it tells you why (private post, X rejected it, etc).

The post is published straight away with no approval step. If you don't like one, delete it on X.

---

## 7. Things that will trip you up

| Problem | Fix |
|---|---|
| Twilio replies "You said: ..." echoing your message | Webhook URL not saved in Sandbox settings, or bot not running |
| Nothing comes back at all | Mac asleep or lid closed, wifi dropped, or `./run.sh` was restarted (new URL, re-paste into Twilio) |
| "Couldn't process" on a post that usually works | Wifi blip mid-download. Just resend the link |
| "403 Forbidden ... oauth1 app permissions" | X access token is read-only. Set Read and write, then **regenerate** the access token |
| "402 credits depleted" | Buy X API credits (project → Manage) |
| "Couldn't process that post" | Post is private/deleted, or Apify credit ran out |
| Sandbox stopped working after 3 days | WhatsApp the `join ...` code to Twilio again (sandbox expires every 72h) |
| Port 5050 already in use | Another copy is running; close other Terminal windows |
| Mac has AirPlay Receiver on | Irrelevant now (bot uses port 5050, not 5000), just don't change the port to 5000 |

---

## 8. Costs

| Item | Cost |
|---|---|
| X post | $0.015 each (no links in post; links cost $0.20) |
| OpenAI transcription | ~$0.003 per minute of video |
| OpenAI writing | ~$0.001 per post |
| Apify fetch | ~$0.003 per post (free tier covers it) |
| Twilio sandbox | Free |
| ngrok | Free |

**~2p per post. 10 posts a day ≈ £5/month.**

---

## 9. Changing the writing style

Open `brain.py`. The block starting `INSTRUCTIONS = """` is the full brief the AI follows. Edit it in plain English (e.g. "use British spelling", "always end with a question"). Save, then stop (`Ctrl+C`) and re-run `./run.sh`. Re-paste the new URL into Twilio.

Every post ends with a fixed sign-off line. Change it in `.env` with `SIGN_OFF=...` (or leave empty to remove it).

Current rules: stay close to the transcript, similar length, third person (never claim the creator's experience as your own), no em dashes, no hashtags, no links, no emojis unless the source is playful.

---

## 10. Going permanent (optional, later)

Running on your Mac means it stops when the lid closes, the ngrok URL changes on restart, and the Twilio sandbox needs re-joining every 72h. To remove all three, host it on a small server (Railway, Fly.io, or a $5 VPS) and register a real WhatsApp sender in Twilio. Not needed to get started.

## 11. Security notes

- Never share your `.env` or paste keys into chats/screenshots. If you do, regenerate them.
- The bot only accepts messages from `ALLOWED_WHATSAPP_NUMBER` and verifies Twilio's signature, so nobody else can post to your X through it.
- Automated posting via the official API is allowed by X. Keep it to a handful of posts a day; never automate likes, follows or replies.
