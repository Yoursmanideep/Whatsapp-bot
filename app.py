from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = "mytoken123"  # you will use this later
WHATSAPP_TOKEN = os.getenv("WA_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")

# ===== VERIFY WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "error", 403

# ===== RECEIVE MESSAGE =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("DATA:", data)

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        user = msg["from"]
        text = msg["text"]["body"]

        print("User:", user)
        print("Message:", text)

        send_message(user, "got your message")

    except:
        pass

    return "ok", 200

# ===== SEND MESSAGE =====
def send_message(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    app.run(port=5000)
