from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ===== CONFIG =====
VERIFY_TOKEN = "mytoken123"
WHATSAPP_TOKEN = os.getenv("WA_TOKEN")
PHONE_ID = os.getenv("PHONE_ID")

# ===== ROOT (for Railway health check) =====
@app.route("/")
def home():
    return "Bot is running", 200

# ===== VERIFY WEBHOOK =====
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    return "error", 403

# ===== RECEIVE MESSAGE =====
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("FULL DATA:", data)

    try:
        if "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})

                    # ✅ HANDLE INCOMING MESSAGE
                    if "messages" in value:
                        msg = value["messages"][0]
                        user = msg.get("from")
                        text = msg.get("text", {}).get("body", "")

                        print("User:", user)
                        print("Message:", text)

                        if user:
                            send_message(user, "got your message")

                    # ✅ HANDLE STATUS UPDATES (IMPORTANT)
                    if "statuses" in value:
                        print("Status update:", value["statuses"])

    except Exception as e:
        print("ERROR:", e)

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

    response = requests.post(url, headers=headers, json=data)
    print("SEND RESPONSE:", response.text)

# ===== RUN SERVER =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
