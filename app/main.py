from flask import Flask, request
import requests
import os
import openai

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def tg_send(text):
    url = f"https://api.telegram.org/bot{8443438913}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.json
    if "message" in data:
        text = data["message"]["text"]
        reply = f"FX TrendMaster received: {text}"
        tg_send(reply)
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
