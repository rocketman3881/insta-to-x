# Launch Plan: Instagram reel → ready-to-post X draft, from the share sheet

Product: user taps Share on any Instagram reel/post → picks the shortcut → ~30 seconds later X opens with a finished long-form post ready to hit Post. No X login, no API keys, no chat bots.

---

## 1. User experience

1. Visit the website → enter email → pay ($9/mo, 3 free drafts first) → get an **Install shortcut** button.
2. Tap it once. The shortcut is now in Instagram's share sheet.
3. In Instagram: Share → **Draft for X**. Wait ~30s. X opens with the post pre-filled. Tap Post.
4. Optional in the dashboard: sign-off line, tone (default / punchy / neutral), copy-to-clipboard instead of opening X.

Works for LinkedIn/Threads too (user just pastes), but X is the headline.

---

## 2. Architecture

```
Instagram share sheet
   → iOS Shortcut / Android HTTP Shortcuts (holds the user's personal token)
   → POST https://api.yourapp.com/draft  {url, token}
   → Server: Apify fetch → OpenAI transcribe + write
   → JSON back {draft}
   → Shortcut opens X composer with text (or copies to clipboard)
```

Reuses `instagram.py` and `brain.py` unchanged. No Twilio, no X API, no tokens for other people's accounts.

---

## 3. What you need to set up (one-off, ~45 min)

| Service | Purpose | What to do |
|---|---|---|
| **Domain** | Shortcut URL + landing page | Namecheap/Cloudflare, ~$10/yr |
| **Hosting** | Always-on server | Railway or Fly.io, ~$5/mo + ~$5/mo Postgres |
| **Stripe** | Subscriptions | Create product "$9/month", get keys + webhook secret |
| **OpenAI, Apify** (have them) | Same pipeline | Raise monthly spend limits |
| **Resend** | Magic-link login emails | Free tier |

No X developer account needed for the product. Your personal bot stays as is.

---

## 4. What gets built (~1–2 days)

1. **Web app** (Flask): landing, email magic-link login, dashboard (install button, usage, settings, billing link), pricing, terms, privacy.
2. **Database** (Postgres): `users` (email, token, plan, drafts_used, period_end, sign_off, tone, open_x), `drafts` (user, ig_url, created).
3. **API**: `POST /draft` — validate token, check quota, run pipeline, return `{draft}` in one request (~30s). Rate-limited per user.
4. **Shortcut generator**: dashboard serves a personalised iOS `.shortcut` (token baked in) and an Android HTTP-Shortcuts import link.
5. **Stripe**: Checkout, webhook to activate/cancel, customer portal.
6. **Ops**: retries on network blips, logs, failure alert to you.

---

## 5. Costs & pricing

Per draft: OpenAI ~$0.005 + Apify ~$0.003 ≈ **$0.01**. 100 drafts/mo = $1/user.
Price **$9/mo, 100 drafts** → ~90% margin. Fixed ~$20/mo.
Free trial: 3 drafts, no card.

---

## 6. Legal / policy (before public launch)

- **Terms + Privacy** pages: you store email and generated drafts, nothing from X.
- Terms state the user is responsible for what they publish; default sign-off can credit the original creator.
- No Instagram branding in the name. Fetching goes via Apify.

---

## 7. Launch sequence

1. Build + deploy privately, test with 3–5 friends.
2. Stripe live, legal pages up.
3. Announce on X. Product Hunt optional.
4. Watch failed-draft rate and Apify health; keep a fallback fetcher wired.

---

# User Setup Guide (goes on the website)

## Turn any Instagram reel into an X post in one tap

**1. Sign up**
yourapp.com → enter your email → click the link we send. First 3 drafts are free.

**2. Install the shortcut**
On your phone, open the dashboard → **Install shortcut** → *Add Shortcut*.
Android: install the free "HTTP Shortcuts" app, then tap **Install**.

**3. Share a reel**
In Instagram, tap Share → **Draft for X**. About 30 seconds later X opens with your post written. Read it, tap Post.

**Settings**
- *Sign-off line*: added to the end of every draft.
- *Open X / copy to clipboard*: pick what happens when the draft is ready.
- *Tone*: default, punchy, or neutral.

**Good to know**
- Drafts stay close to what the creator said, rewritten in third person, no hashtags, no links, no dashes.
- Nothing is posted automatically. You always press Post.
- Usage resets monthly. Cancel any time from the dashboard.
