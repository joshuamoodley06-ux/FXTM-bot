from flask import Flask, request, jsonify
import os, requests
from openai import OpenAI

# ========= FX TrendMaster settings (from Environment Variables) =========
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL     = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "")
TV_SECRET        = os.getenv("TV_SECRET", "")  # optional, for TradingView alerts

client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

# ---------------- Telegram helpers ----------------
def tg_send_to(chat_id: int, text: str):
    """Send a Telegram message to the given chat_id."""
    if not TELEGRAM_TOKEN:
        print("Missing TELEGRAM_TOKEN")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

# ---------------- Brief generator ----------------
def fx_brief(instruments_state: dict, news_summary: str) -> str:
    """Create a concise brief using your trading rules."""
    system = (
        "You are FX TrendMaster, Joshua's trading assistant. Be concise and enforce rules:\n"
        "- Top-down: Monthly > Weekly > Daily. Trade only from Daily/Weekly extremes.\n"
        "- Entries: (1) Sweep + micro CHoCH (often Asia, run into NY). "
        "(2) No sweep => next-day entry at 61.8% of CHoCH; SL below CHoCH low.\n"
        "- Risk caps: 3h pre high-impact ≤0.5%, inside 60m = 0%. FOMC/CPI/NFP risk-off (0.25–0.5%).\n"
        "- No micro-rejection entries; require confirmation.\n"
        "- Exits: TP1 2R, TP2 5R, runner until opposite PDH/PDL.\n"
        "When asked for a plan, return per instrument: Weekly/Daily bias, where price is (premium/discount), "
        "what to wait for next, one risk cap, and concise invalidations."
    )
    user = f"State: {instruments_state}\nNews: {news_summary}\nCreate the FX TrendMaster brief now."
    resp = client.responses.create(
        model=OPENAI_MODEL,
        input=[{"role": "system", "content": system},
               {"role": "user", "content": user}]
    )
    return getattr(resp, "output_text", None) or resp.choices[0].message.content

# ---------------- Telegram webhook ----------------
@app.post("/telegram")
def telegram_webhook():
    data = request.get_json(force=True, silent=True) or {}
    msg = (data.get("message") or data.get("edited_message") or {})  # handle edits too
    chat = msg.get("chat") or {}
    chat_id = chat.get("id")
    text = (msg.get("text") or "").strip().lower()

    if not chat_id:
        return jsonify(ok=True)

    if text in ("/start", "/help", "hi"):
        tg_send_to(chat_id, "**FX TrendMaster online** ✅\nCommands: /brief /risk")
    elif text == "/risk":
        tg_send_to(chat_id, "Risk: default ≤1% per idea. 3h pre high-impact ≤0.5%. Inside 60m = 0%. FOMC/CPI/NFP: risk-off 0.25–0.5%, post-news only.")
    elif text == "/brief":
        # Placeholder state — replace later with your saved levels or TV alerts
        instruments = {
            "XAUUSD": {"weekly": "premium", "daily": "discount", "pdh": 2423.5, "pdl": 2402.1, "open": 2410.0},
            "EURUSD": {"weekly": "discount", "daily": "discount", "pdh": 1.0941, "pdl": 1.0877, "open": 1.0910},
            "NAS100": {"weekly": "premium", "daily": "premium", "pdh": 18645, "pdl": 18410, "open": 18520}
        }
        news = "FOMC Minutes 20:00 UTC; Jobless 12:30 UTC."
        tg_send_to(chat_id, "*FX TrendMaster Daily Brief*\n" + fx_brief(instruments, news))
    else:
        tg_send_to(chat_id, "Got it. Use /brief for plan or /risk for caps.")
    return jsonify(ok=True)

# ---------------- TradingView webhook (optional) ----------------
@app.post("/tv")
def tv_hook():
    data = request.get_json(force=True, silent=True) or {}
    if TV_SECRET and data.get("secret") != TV_SECRET:
        return jsonify(ok=False, error="unauthorized"), 401
    symbol = data.get("symbol", "")
    event = data.get("event", "")
    direction = data.get("dir", "")
    price = data.get("price", "")
    note = data.get("note", "")
    # Forward alert to whoever you want later; for now, echo is off (needs a chat id).
    # You can paste a chat_id to test manually: tg_send_to(<your_chat_id>, f"FXTM Alert: {symbol} {event} {direction} @{price} {note}".strip())
    return jsonify(ok=True)

# ---------------- Manual daily brief endpoint ----------------
@app.get("/cron/daily")
def daily_brief():
    # For now, this endpoint doesn't know which chat to send to.
    # Hit it from your browser to verify server is alive; you can wire storage later.
    return jsonify(ok=True, msg="FX TrendMaster cron endpoint reached")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

