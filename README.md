# SRT Hinglish Translator (VPS Edition)

Translates `.srt` subtitle files into Hinglish (Roman-script Hindi) using
`anythingtranslate.com`'s Hinglish translator, with **character-based
batching** to minimize requests and avoid rate limits.

Two ways to use it:
1. **CLI** (`translate_srt.py`) — direct terminal use
2. **API** (`main.py`) — FastAPI app with Swagger UI, so you can test by
   uploading a file in the browser, and your Telegram bot can also call
   this same API instead of duplicating translation logic.

## Setup on VPS

```bash
git clone https://github.com/<your-username>/hingsub.git
cd hingsub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Option 1: CLI usage

```bash
python3 translate_srt.py input.srt output.srt
python3 translate_srt.py input.srt output.srt --batch-chars 300 --delay 1
```

## Option 2: API usage (Swagger UI testing)

Start the server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open in your browser:

```
http://<your-vps-ip>:8000/docs
```

- Click on `POST /translate-upload`
- Click "Try it out"
- Upload your `.srt` file, optionally adjust `batch_chars` / `delay`
- Click "Execute" — the translated `.srt` file downloads directly from
  the Swagger UI

> **Note:** Make sure port 8000 is open on your VPS firewall
> (`ufw allow 8000` on Ubuntu, or your cloud provider's security group).
> For production use later, put this behind nginx + a real domain +
> HTTPS instead of exposing the raw port.

### Using the API from your Telegram bot

Instead of running the translation logic inside the bot itself, the bot
can just call this API:

```python
import requests

with open("input.srt", "rb") as f:
    resp = requests.post(
        "http://<your-vps-ip>:8000/translate-upload",
        files={"file": f},
        params={"batch_chars": 450, "delay": 0.5},
        timeout=600,
    )

with open("output.srt", "wb") as f:
    f.write(resp.content)
```

This keeps the bot code simple and lets you scale/update the translation
logic independently of the bot.

## Running the API in the background (so it survives closing SSH)

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

Or better, use `systemd` or `pm2`/`supervisor` for a proper production
setup later.

## What to watch for while testing

1. **Rate limits** — if you get `rate_limit_exceeded`, increase `delay`
   and/or lower `batch_chars`.
2. **Batch mismatches** — the translator might not return the same
   number of lines it received. The script auto-falls-back to per-line
   translation when that happens — check the response headers
   (`X-Batch-Fallback`, `X-Line-Fail`) or CLI report to see how often.
3. **Nonce expiry** — if every request fails with an auth-type error,
   `anythingtranslate.com` may have rotated their nonce; update the
   fallback value in `translator.py`'s `_get_nonce()`.

## Project structure

```
hingsub/
├── translator.py       # core translation logic (shared)
├── translate_srt.py     # CLI entry point
├── main.py               # FastAPI app (Swagger UI + bot-callable API)
├── requirements.txt
└── README.md
```
