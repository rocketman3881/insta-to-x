#!/usr/bin/env bash
# Starts the bot and an ngrok tunnel, prints the webhook URL to paste into Twilio.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-5050}"
export PORT

# caffeinate keeps the Mac awake while the bot runs (closing the lid still sleeps it).
caffeinate -is uv run python app.py &
APP_PID=$!

ngrok http "$PORT" --log=stdout --log-format=logfmt > /tmp/ngrok.log &
NGROK_PID=$!
# pkill -P catches the python child under caffeinate so it can't outlive this script.
trap 'pkill -P $APP_PID; kill $APP_PID $NGROK_PID' EXIT

sleep 3
URL=$(curl -s localhost:4040/api/tunnels | python3 -c 'import sys,json;print(json.load(sys.stdin)["tunnels"][0]["public_url"])')
echo
echo "==> Paste this into Twilio sandbox 'When a message comes in':  ${URL}/whatsapp"
echo
wait
