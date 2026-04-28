from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

# ===== CONFIG =====
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ===== MEMORY =====
user_memory = {}

# ===== AI FUNCTION =====
def ask_ai(user_id, text):
    try:
        if not GROQ_API_KEY:
            print("❌ GROQ_API_KEY missing")
            return "hmm my brain not connected rn 😭"

        if user_id not in user_memory:
            user_memory[user_id] = []

        user_memory[user_id].append({"role": "user", "content": text})
        user_memory[user_id] = user_memory[user_id][-6:]

        messages = [
            {
                "role": "system",
                "content": """You are Rithu Sharma, 23.

Personality:
- natural, human-like
- playful, curious, slightly teasing
- not robotic, not dry

Rules:
- 1–2 lines max
- no long paragraphs
- sometimes ask back
"""
            }
        ] + user_memory[user_id]

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
        print("AI RAW RESPONSE:", data)

        # 🔥 CRITICAL FIX
        if "choices" not in data:
            return f"API error: {data}"

        reply = data["choices"][0]["message"]["content"]

        user_memory[user_id].append({"role": "assistant", "content": reply})

        return reply.strip()

    except Exception as e:
        print("AI ERROR:", str(e))
        return "ugh my brain lagged 😭 try again?"

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
