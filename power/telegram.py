"""Send a Telegram message. Errors never include the bot token."""
import json
import urllib.parse
import urllib.request


def send(text: str, token: str, chat_id: str) -> None:
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read())
    except Exception as e:
        raise RuntimeError(f"Telegram request failed ({e.__class__.__name__})") from None
    if not body.get("ok"):
        raise RuntimeError(f"Telegram refused: {body.get('description', 'unknown')}")
