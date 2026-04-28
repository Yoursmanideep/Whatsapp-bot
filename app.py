from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# ===== CONFIG =====
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ===== SIMPLE MEMORY (per user) =====
user_memory = {}

# ===== AI FUNCTION =====
def ask_ai(user_id, text):
    try:
        if user_id not in user_memory:
            user_memory[user_id] = []

        # add user message
        user_memory[user_id].append({"role": "user", "content": text})

        # keep last 6 messages (short memory)
        user_memory[user_id] = user_memory[user_id][-6:]

        system_prompt = {
            "role": "system",
            "content": """
You are Rithu Sharma, a 23-year-old girl.

Personality:
- funny, curious, slightly childish sometimes
- friendly and warm, not dry
- sometimes teasing or playful
- not overly flirty, not robotic
- speaks like a real human texter

Behavior:
- keep replies SHORT (1–2 lines max)
- sometimes ask questions back
- sometimes change topic naturally
- no long paragraphs
"""
        }

        messages = [system_prompt] + user_memory[user_id]

        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages
            },
            timeout=20
        )

        data = res.json()

        reply = data["choices"][0]["message"]["content"]

        # store reply
        user_memory[user_id].append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "ugh my brain lagged 😭 say that again?"

# ===== ROOT =====
@app.route("/")
def home():
    return "Rithu bot running 💬", 200

# ===== WHATSAPP HANDLER =====
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    incoming_msg = request.values.get("Body", "")
    sender = request.values.get("From")

    print("User:", sender)
    print("Message:", incoming_msg)

    reply = ask_ai(sender, incoming_msg)

    resp = MessagingResponse()
    resp.message(reply)

    return str(resp)

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
